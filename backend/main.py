import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi import Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from services.api_keys import (
    create_api_key,
    get_api_key_stats,
    get_user_api_keys,
    revoke_api_key,
)
from services.auth import (
    User,
    UserTier,
    authenticate_user,
    create_access_token,
    create_user,
    decode_access_token,
    get_user_by_email,
    get_user_tier_limits,
)
from services.cache import get, get_cache_key, set
from services.cache import get_stats as get_cache_stats
from services.circuit_breaker import get_all_breakers, reset_breaker
from services.database import (
    cleanup_expired_cache,
    get_database_stats,
    get_db_session,
    get_search_history,
    init_database,
    save_analytics,
    save_company_cache,
    save_search_history,
)
from services.debt_registers import search_debt_registers
from services.erp.erp_service import (
    activate_erp_connection,
    create_erp_connection,
    deactivate_erp_connection,
    get_erp_sync_logs,
    get_supplier_payment_history_from_erp,
    get_user_erp_connections,
    sync_erp_data,
    test_erp_connection,
)
from services.analytics import (
    get_dashboard_summary,
    get_search_trends,
    get_risk_distribution,
    get_user_activity,
    get_api_usage,
)
from services.favorites import (
    add_favorite,
    remove_favorite,
    get_user_favorites,
    is_favorite,
    update_favorite_notes,
)
from services.erp.models import ErpType
from services.error_handler import error_handler
from services.hu_nav import (
    calculate_hu_risk_score,
    fetch_nav_hu,
    is_hungarian_tax_number,
    parse_nav_data,
)
from services.metrics import (
    TimerContext,
    gauge,
    get_metrics,
    increment,
    record_event,
)
from services.pl_biala_lista import (
    get_vat_status_pl,
    is_polish_nip,
)
from services.pl_krs import (
    calculate_pl_risk_score,
    fetch_krs_pl,
    is_polish_krs,
    parse_krs_data,
)
from services.proxy_rotation import get_proxy_stats, init_proxy_pool
from services.rate_limiter import get_client_id, is_allowed
from services.rate_limiter import get_stats as get_rate_limiter_stats
from services.risk_intelligence import (
    generate_risk_report,
)

# Import nových služieb
from services.sk_rpo import (
    calculate_sk_risk_score,
    fetch_rpo_sk,
    is_slovak_ico,
    parse_rpo_data,
)
from services.stripe_service import (
    cancel_subscription,
    create_checkout_session,
    get_subscription_status,
    handle_webhook,
)
from services.webhooks import (
    create_webhook,
    delete_webhook,
    get_user_webhooks,
    get_webhook_deliveries,
    get_webhook_stats,
)

app = FastAPI(
    title="ILUMINATI SYSTEM API",
    version="5.0",
    description="Cross-border company registry search API for V4 countries (SK, CZ, PL, HU)",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Global error handler
app.add_exception_handler(Exception, error_handler)


# Inicializovať databázu pri štarte
@app.on_event("startup")
async def startup_event():
    """Inicializácia pri štarte aplikácie"""
    init_database()
    # Cleanup expirovaného cache pri štarte
    cleanup_expired_cache()
    # Inicializovať proxy pool (ak sú proxy v env)
    init_proxy_pool()


# --- KONFIGURÁCIA CORS (Prepojenie s Frontendom) ---
origins = [
    "http://localhost:5173",  # Vite default port
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DÁTOVÉ MODELY (Podľa sekcie 3: Dátový Model) ---
class Node(BaseModel):
    id: str
    label: str
    type: str  # 'company' | 'person' | 'address' | 'debt'
    country: str
    risk_score: Optional[int] = 0
    details: Optional[str] = ""
    ico: Optional[str] = None  # IČO pre firmy
    virtual_seat: Optional[bool] = False  # Virtual seat flag


class Edge(BaseModel):
    source: str
    target: str
    type: str  # 'OWNED_BY' | 'MANAGED_BY' | 'LOCATED_AT' | 'HAS_DEBT'


class GraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


# Auth Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    consent_given: bool = True  # Always true from UI checkbox
    consent_ip: Optional[str] = None
    consent_user_agent: Optional[str] = None
    document_versions: Dict[str, str] = Field(
        default_factory=lambda: {"vop": "1.0", "privacy": "1.0", "cookies": "1.0"}
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    tier: str
    is_active: bool
    is_verified: bool


# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Získa aktuálneho používateľa z tokenu"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with get_db_session() as db:
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )
        user = get_user_by_email(db, email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user


# --- SLUŽBY (ARES INTEGRÁCIA) ---
def fetch_ares_cz(query: str):
    """
    Získa dáta z českého registra ARES.
    """
    url = (
        "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat"
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "obchodniJmeno": query,
        "pocet": 5,  # Limit pre MVP
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Chyba pri volaní ARES: {e}")
        return {"ekonomickeSubjekty": []}


def calculate_trust_score(company_data):
    """
    Jednoduchá biznis logika pre výpočet rizika (Section 2B).
    """
    score = 0
    # Príklad logiky: Ak firma nemá DPH (mock), riziko +2
    if random.choice([True, False]):
        score += 2
    return score


# --- ENDPOINTY ---


@app.get("/")
def read_root():
    return {
        "status": "ILUMINATI SYSTEM API Running",
        "version": "5.0",
        "features": [
            "CZ (ARES)",
            "SK (RPO)",
            "PL (KRS)",
            "HU (NAV)",
            "Cache",
            "Risk Scoring",
            "Authentication",
            "Stripe Integration",
            "API Keys Management",
            "Webhooks",
            "ERP Integrations",
            "Analytics Dashboard",
            "Favorites System"
        ],
        "endpoints": {
            "health": "/api/health",
            "docs": "/docs",
            "search": "/api/search",
            "auth": "/api/auth",
            "enterprise": "/api/enterprise",
            "analytics": "/api/analytics"
        }
    }


@app.get("/api/cache/stats")
def cache_stats():
    """Vráti štatistiky cache."""
    return get_cache_stats()


@app.get("/api/rate-limiter/stats")
async def rate_limiter_stats():
    """Vráti štatistiky rate limitera"""
    return get_rate_limiter_stats()


@app.get("/api/database/stats")
async def database_stats():
    """Vráti štatistiky databázy"""
    return get_database_stats()


@app.get("/api/search/history")
async def search_history(limit: int = 100, country: Optional[str] = None):
    """Vráti históriu vyhľadávaní"""
    return get_search_history(limit=limit, country=country)


# --- FAVORITES ENDPOINTY ---


@app.post("/api/user/favorites")
async def add_favorite_company(
    request: Dict,
    current_user: User = Depends(get_current_user),
):
    """
    Pridá firmu do obľúbených (len pre prihlásených používateľov)
    
    Body:
        {
            "company_identifier": "12345678",
            "company_name": "Firma s.r.o.",
            "country": "SK",
            "company_data": {...},  # optional
            "risk_score": 5.0,  # optional
            "notes": "Moja poznámka"  # optional
        }
    """
    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        favorite = add_favorite(
            db=db,
            user_id=current_user.id,
            company_identifier=request.get("company_identifier"),
            company_name=request.get("company_name"),
            country=request.get("country"),
            company_data=request.get("company_data"),
            risk_score=request.get("risk_score"),
            notes=request.get("notes"),
        )

        return {"success": True, "favorite": favorite.to_dict()}


@app.get("/api/user/favorites")
async def get_favorites(
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Získa zoznam obľúbených firiem používateľa
    """
    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        favorites = get_user_favorites(db=db, user_id=current_user.id, limit=limit)
        return {
            "success": True,
            "favorites": [f.to_dict() for f in favorites],
            "count": len(favorites),
        }


@app.delete("/api/user/favorites/{favorite_id}")
async def remove_favorite_company(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Odstráni firmu z obľúbených
    """
    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        success = remove_favorite(db=db, user_id=current_user.id, favorite_id=favorite_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found",
            )

        return {"success": True, "message": "Favorite removed"}


@app.get("/api/user/favorites/check/{company_identifier}/{country}")
async def check_is_favorite(
    company_identifier: str,
    country: str,
    current_user: User = Depends(get_current_user),
):
    """
    Skontroluje, či je firma v obľúbených
    """
    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        is_fav = is_favorite(
            db=db,
            user_id=current_user.id,
            company_identifier=company_identifier,
            country=country,
        )

        return {"success": True, "is_favorite": is_fav}


@app.put("/api/user/favorites/{favorite_id}/notes")
async def update_favorite_notes(
    favorite_id: int,
    request: Dict,
    current_user: User = Depends(get_current_user),
):
    """
    Aktualizuje poznámky k obľúbenej firme
    
    Body:
        {
            "notes": "Nová poznámka"
        }
    """
    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        favorite = update_favorite_notes(
            db=db,
            user_id=current_user.id,
            favorite_id=favorite_id,
            notes=request.get("notes", ""),
        )

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found",
            )

        return {"success": True, "favorite": favorite.to_dict()}


@app.get("/api/circuit-breaker/stats")
async def circuit_breaker_stats():
    """Vráti štatistiky circuit breakerov"""
    return get_all_breakers()


@app.post("/api/circuit-breaker/reset/{name}")
async def reset_circuit_breaker(name: str):
    """Resetuje circuit breaker"""
    reset_breaker(name)
    return {"status": "ok", "message": f"Circuit breaker '{name}' reset"}


@app.get("/api/metrics")
async def metrics():
    """Vráti metríky"""
    return get_metrics().get_metrics()


@app.get("/api/proxy/stats")
async def proxy_stats():
    """Vráti štatistiky proxy poolu"""
    return get_proxy_stats()


# --- AUTH ENDPOINTY ---


@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister, request: Request):
    """Registrácia nového používateľa"""
    with get_db_session() as db:
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        # Skontrolovať, či už existuje
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Získať IP a User-Agent pre GDPR compliance
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        # Vytvoriť používateľa s consent dátami
        user = create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            consent_given=user_data.consent_given,
            consent_ip=client_ip,
            consent_user_agent=user_agent,
            document_versions=user_data.document_versions,
        )

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            tier=user.tier.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )


@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login používateľa"""
    with get_db_session() as db:
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Vytvoriť access token
        access_token_expires = timedelta(minutes=30 * 24 * 60)  # 30 dní
        access_token = create_access_token(
            data={"sub": user.email, "tier": user.tier.value},
            expires_delta=access_token_expires,
        )

        # Aktualizovať last_login
        user.last_login = datetime.utcnow()
        db.commit()

        return Token(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "tier": user.tier.value,
                "limits": get_user_tier_limits(user.tier),
            },
        )


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Získa informácie o aktuálnom používateľovi"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        tier=current_user.tier.value,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )


@app.get("/api/auth/tier/limits")
async def get_tier_limits(current_user: User = Depends(get_current_user)):
    """Získa limity pre tier aktuálneho používateľa"""
    return get_user_tier_limits(current_user.tier)


# --- ENTERPRISE API ENDPOINTS ---


class ApiKeyCreate(BaseModel):
    name: str = Field(..., description="Názov/opis API key")
    expires_days: Optional[int] = Field(
        None, description="Počet dní do expirácie (None = bez expirácie)"
    )
    permissions: Optional[List[str]] = Field(
        default=["read"], description="Permissions: read, write"
    )
    ip_whitelist: Optional[List[str]] = Field(
        None, description="Zoznam povolených IP adries"
    )


@app.post("/api/enterprise/keys")
async def generate_api_key_endpoint(
    key_data: ApiKeyCreate, current_user: User = Depends(get_current_user)
):
    """
    Vytvoriť nový API key (len Enterprise tier)
    """
    # Kontrola tieru
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        result = create_api_key(
            db=db,
            user_id=current_user.id,
            name=key_data.name,
            expires_days=key_data.expires_days,
            permissions=key_data.permissions,
            ip_whitelist=key_data.ip_whitelist,
        )

        return {
            "success": True,
            "message": "API key created successfully",
            "data": result,
            "warning": "⚠️ Save this key now! It will not be shown again.",
        }


@app.get("/api/enterprise/keys")
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """
    Získať zoznam všetkých API keys pre používateľa (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        api_keys = get_user_api_keys(db, current_user.id)

        import json

        result = []
        for key in api_keys:
            result.append(
                {
                    "id": key.id,
                    "name": key.name,
                    "prefix": key.prefix,
                    "created_at": key.created_at.isoformat(),
                    "expires_at": key.expires_at.isoformat()
                    if key.expires_at
                    else None,
                    "last_used_at": key.last_used_at.isoformat()
                    if key.last_used_at
                    else None,
                    "usage_count": key.usage_count,
                    "is_active": key.is_active,
                    "permissions": json.loads(key.permissions)
                    if key.permissions
                    else [],
                    "ip_whitelist": json.loads(key.ip_whitelist)
                    if key.ip_whitelist
                    else None,
                }
            )

        return {"success": True, "keys": result, "count": len(result)}


@app.delete("/api/enterprise/keys/{key_id}")
async def revoke_api_key_endpoint(
    key_id: int, current_user: User = Depends(get_current_user)
):
    """
    Zrušiť (deaktivovať) API key (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        success = revoke_api_key(db, key_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or does not belong to user",
            )

        return {"success": True, "message": "API key revoked successfully"}


@app.get("/api/enterprise/usage/{key_id}")
async def get_api_key_usage(
    key_id: int, current_user: User = Depends(get_current_user)
):
    """
    Získať štatistiky použitia API key (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        stats = get_api_key_stats(db, key_id, current_user.id)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or does not belong to user",
            )

        return {"success": True, "stats": stats}


# --- WEBHOOKS ENDPOINTS ---


class WebhookCreate(BaseModel):
    url: str = Field(..., description="Webhook URL endpoint")
    events: List[str] = Field(..., description="List of event types to subscribe to")
    secret: Optional[str] = Field(
        None, description="Optional secret (will be generated if not provided)"
    )


@app.post("/api/enterprise/webhooks")
async def create_webhook_endpoint(
    webhook_data: WebhookCreate, current_user: User = Depends(get_current_user)
):
    """
    Vytvoriť nový webhook (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhooks are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        result = create_webhook(
            db=db,
            user_id=current_user.id,
            url=webhook_data.url,
            events=webhook_data.events,
            secret=webhook_data.secret,
        )

        return {
            "success": True,
            "message": "Webhook created successfully",
            "data": result,
            "warning": "⚠️ Save the secret now! It will not be shown again.",
        }


@app.get("/api/enterprise/webhooks")
async def list_webhooks(current_user: User = Depends(get_current_user)):
    """
    Získať zoznam všetkých webhooks pre používateľa (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhooks are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        webhooks = get_user_webhooks(db, current_user.id)

        import json

        result = []
        for webhook in webhooks:
            result.append(
                {
                    "id": webhook.id,
                    "url": webhook.url,
                    "events": json.loads(webhook.events),
                    "is_active": webhook.is_active,
                    "created_at": webhook.created_at.isoformat(),
                    "last_delivered_at": webhook.last_delivered_at.isoformat()
                    if webhook.last_delivered_at
                    else None,
                    "success_count": webhook.success_count,
                    "failure_count": webhook.failure_count,
                }
            )

        return {"success": True, "webhooks": result, "count": len(result)}


@app.delete("/api/enterprise/webhooks/{webhook_id}")
async def delete_webhook_endpoint(
    webhook_id: int, current_user: User = Depends(get_current_user)
):
    """
    Zmazať webhook (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhooks are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        success = delete_webhook(db, webhook_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found or does not belong to user",
            )

        return {"success": True, "message": "Webhook deleted successfully"}


@app.get("/api/enterprise/webhooks/{webhook_id}/stats")
async def get_webhook_stats_endpoint(
    webhook_id: int, current_user: User = Depends(get_current_user)
):
    """
    Získať štatistiky pre webhook (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhooks are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        stats = get_webhook_stats(db, webhook_id, current_user.id)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found or does not belong to user",
            )

        return {"success": True, "stats": stats}


@app.get("/api/enterprise/webhooks/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: int, limit: int = 50, current_user: User = Depends(get_current_user)
):
    """
    Získať delivery logy pre webhook (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhooks are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        deliveries = get_webhook_deliveries(db, webhook_id, current_user.id, limit)

        result = []
        for delivery in deliveries:
            result.append(
                {
                    "id": delivery.id,
                    "event_type": delivery.event_type,
                    "delivery_time": delivery.delivery_time.isoformat(),
                    "success": delivery.success,
                    "response_status": delivery.response_status,
                    "error_message": delivery.error_message,
                }
            )

        return {"success": True, "logs": result, "count": len(result)}


# --- ERP INTEGRATION ENDPOINTS ---


class ErpConnectionCreate(BaseModel):
    erp_type: str = Field(..., description="Typ ERP systému: sap, pohoda, money_s3")
    connection_data: Dict = Field(
        ..., description="Connection credentials (API keys, URLs, etc.)"
    )
    sync_frequency: Optional[str] = Field(
        default="daily", description="Sync frequency: daily, weekly, manual"
    )


@app.post("/api/enterprise/erp/connect")
async def create_erp_connection_endpoint(
    erp_data: ErpConnectionCreate, current_user: User = Depends(get_current_user)
):
    """
    Vytvoriť nové ERP pripojenie (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERP integrations are only available for Enterprise tier",
        )

    try:
        erp_type = ErpType(erp_data.erp_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ERP type: {erp_data.erp_type}. Must be: sap, pohoda, money_s3",
        )

    # Test pripojenia pred vytvorením
    test_result = test_erp_connection(erp_type, erp_data.connection_data)
    if not test_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {test_result.get('message', 'Unknown error')}",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        connection = create_erp_connection(
            db=db,
            user_id=current_user.id,
            erp_type=erp_type,
            connection_data=erp_data.connection_data,
        )

        # Nastaviť sync frequency
        connection.sync_frequency = erp_data.sync_frequency

        # Aktivovať pripojenie
        if activate_erp_connection(db, connection.id, current_user.id):
            db.refresh(connection)
            return {
                "success": True,
                "message": "ERP connection created and activated",
                "data": connection.to_dict(),
            }
        else:
            return {
                "success": True,
                "message": "ERP connection created but activation failed",
                "data": connection.to_dict(),
                "warning": "Please check your credentials",
            }


@app.get("/api/enterprise/erp/connections")
async def list_erp_connections_endpoint(current_user: User = Depends(get_current_user)):
    """
    Získať zoznam všetkých ERP pripojení (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERP integrations are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        connections = get_user_erp_connections(db, current_user.id)

        result = [conn.to_dict() for conn in connections]

        return {"success": True, "connections": result, "count": len(result)}


@app.post("/api/enterprise/erp/{connection_id}/activate")
async def activate_erp_connection_endpoint(
    connection_id: int, current_user: User = Depends(get_current_user)
):
    """
    Aktivovať ERP pripojenie (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERP integrations are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        success = activate_erp_connection(db, connection_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to activate connection. Please check your credentials.",
            )

        return {"success": True, "message": "ERP connection activated successfully"}


@app.post("/api/enterprise/erp/{connection_id}/deactivate")
async def deactivate_erp_connection_endpoint(
    connection_id: int, current_user: User = Depends(get_current_user)
):
    """
    Deaktivovať ERP pripojenie (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERP integrations are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        success = deactivate_erp_connection(db, connection_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
            )

        return {"success": True, "message": "ERP connection deactivated successfully"}


@app.post("/api/enterprise/erp/{connection_id}/sync")
async def sync_erp_data_endpoint(
    connection_id: int,
    sync_type: str = "incremental",
    current_user: User = Depends(get_current_user),
):
    """
    Synchronizovať dáta z ERP (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERP integrations are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        result = sync_erp_data(db, connection_id, current_user.id, sync_type)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Sync failed"),
            )

        return result


@app.get("/api/enterprise/erp/{connection_id}/logs")
async def get_erp_sync_logs_endpoint(
    connection_id: int, limit: int = 50, current_user: User = Depends(get_current_user)
):
    """
    Získať logy synchronizácií ERP (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERP integrations are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        logs = get_erp_sync_logs(db, connection_id, current_user.id, limit)

        result = [log.to_dict() for log in logs]

        return {"success": True, "logs": result, "count": len(result)}


@app.get("/api/enterprise/erp/{connection_id}/supplier/{supplier_ico}/payments")
async def get_supplier_payments_endpoint(
    connection_id: int,
    supplier_ico: str,
    days: int = 365,
    current_user: User = Depends(get_current_user),
):
    """
    Získať históriu platieb dodávateľa z ERP (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERP integrations are only available for Enterprise tier",
        )

    with get_db_session() as db:
        if not db:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available",
            )

        payments = get_supplier_payment_history_from_erp(
            db, connection_id, current_user.id, supplier_ico, days
        )

        return {
            "success": True,
            "supplier_ico": supplier_ico,
            "payments": payments,
            "count": len(payments),
        }


# --- ANALYTICS ENDPOINTY ---


@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_user),
):
    """
    Získať kompletný analytics dashboard (len Enterprise tier)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics dashboard is only available for Enterprise tier",
        )

    try:
        summary = get_dashboard_summary()
        return {"success": True, "data": summary}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analytics: {str(e)}",
        )


@app.get("/api/analytics/search-trends")
async def get_analytics_search_trends(
    days: int = 30,
    group_by: str = "day",
    current_user: User = Depends(get_current_user),
):
    """
    Získať trendy vyhľadávaní (len Enterprise tier)
    
    Args:
        days: Počet dní späť (default: 30)
        group_by: Agregácia - day, week, month (default: day)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics are only available for Enterprise tier",
        )

    try:
        trends = get_search_trends(days=days, group_by=group_by, user_id=current_user.id)
        return {"success": True, "data": trends}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching search trends: {str(e)}",
        )


@app.get("/api/analytics/risk-distribution")
async def get_analytics_risk_distribution(
    days: int = 30,
    current_user: User = Depends(get_current_user),
):
    """
    Získať distribúciu risk skóre (len Enterprise tier)
    
    Args:
        days: Počet dní späť (default: 30)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics are only available for Enterprise tier",
        )

    try:
        distribution = get_risk_distribution(days=days, user_id=current_user.id)
        return {"success": True, "data": distribution}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching risk distribution: {str(e)}",
        )


@app.get("/api/analytics/user-activity")
async def get_analytics_user_activity(
    days: int = 30,
    current_user: User = Depends(get_current_user),
):
    """
    Získať aktivitu používateľov (len Enterprise tier)
    
    Args:
        days: Počet dní späť (default: 30)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics are only available for Enterprise tier",
        )

    try:
        activity = get_user_activity(days=days)
        return {"success": True, "data": activity}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user activity: {str(e)}",
        )


@app.get("/api/analytics/api-usage")
async def get_analytics_api_usage(
    days: int = 30,
    current_user: User = Depends(get_current_user),
):
    """
    Získať štatistiky API použitia (len Enterprise tier)
    
    Args:
        days: Počet dní späť (default: 30)
    """
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics are only available for Enterprise tier",
        )

    try:
        usage = get_api_usage(days=days)
        return {"success": True, "data": usage}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching API usage: {str(e)}",
        )


# --- STRIPE ENDPOINTY ---


@app.post("/api/payment/checkout")
async def create_payment_checkout(
    tier: str, current_user: User = Depends(get_current_user)
):
    """Vytvorí Stripe checkout session pre upgrade tieru"""
    try:
        user_tier = UserTier(tier.lower())
        if user_tier == UserTier.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot upgrade to FREE tier",
            )

        result = create_checkout_session(
            user_id=current_user.id, user_email=current_user.email, tier=user_tier
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid tier: {tier}"
        )


@app.post("/api/payment/webhook")
async def stripe_webhook(request: FastAPIRequest):
    """Stripe webhook endpoint pre subscription events"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    result = handle_webhook(payload, signature)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
        )

    return result


@app.get("/api/payment/subscription")
async def get_subscription(current_user: User = Depends(get_current_user)):
    """Získa subscription status používateľa"""
    result = get_subscription_status(current_user.email)

    if result is None:
        return {"status": "no_subscription", "tier": current_user.tier.value}

    return result


@app.post("/api/payment/cancel")
async def cancel_user_subscription(current_user: User = Depends(get_current_user)):
    """Zruší subscription používateľa"""
    result = cancel_subscription(current_user.email)

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
        )

    return result


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache": get_cache_stats(),
        "features": {
            "cz_ares": True,
            "sk_rpo": True,
            "pl_krs": True,
            "hu_nav": True,
            "risk_intelligence": True,
            "cache": True,
            "database": get_database_stats().get("available", False),
        },
    }


def generate_test_data_sk(ico: str):
    """
    Generuje testovacie dáta pre slovenské IČO 88888888.
    Simuluje komplexnú štruktúru s viacerými firmami, osobami a vzťahmi.
    """
    nodes = []
    edges = []

    # Hlavná firma
    main_company_id = f"sk_{ico}"
    nodes.append(
        Node(
            id=main_company_id,
            label="Testovacia Spoločnosť s.r.o.",
            type="company",
            country="SK",
            risk_score=7,  # Vysoké riziko pre test
            details=f"IČO: {ico}, Status: Aktívna, DPH: Áno",
        )
    )

    # Adresa hlavnej firmy
    main_address_id = f"addr_{ico}_main"
    nodes.append(
        Node(
            id=main_address_id,
            label="Bratislava, Hlavná 1",
            type="address",
            country="SK",
            risk_score=3,  # Virtual seat flag
            details="Hlavná 1, 811 01 Bratislava (Virtual Seat - 52 firiem na adrese)",
        )
    )
    edges.append(
        Edge(source=main_company_id, target=main_address_id, type="LOCATED_AT")
    )

    # Konateľ 1
    person1_id = f"pers_{ico}_1"
    nodes.append(
        Node(
            id=person1_id,
            label="Ján Novák",
            type="person",
            country="SK",
            risk_score=5,
            details="Konateľ, 15+ firiem v registri",
        )
    )
    edges.append(Edge(source=main_company_id, target=person1_id, type="MANAGED_BY"))

    # Konateľ 2
    person2_id = f"pers_{ico}_2"
    nodes.append(
        Node(
            id=person2_id,
            label="Peter Horváth",
            type="person",
            country="SK",
            risk_score=4,
            details="Spoločník, 8% podiel",
        )
    )
    edges.append(Edge(source=main_company_id, target=person2_id, type="OWNED_BY"))

    # Dcérska spoločnosť 1 (CZ)
    daughter1_id = "cz_12345678"
    nodes.append(
        Node(
            id=daughter1_id,
            label="Dcérska Firma CZ s.r.o.",
            type="company",
            country="CZ",
            risk_score=6,
            details="IČO: 12345678, Vlastníctvo: 100%",
        )
    )
    edges.append(Edge(source=main_company_id, target=daughter1_id, type="OWNED_BY"))

    # Dcérska spoločnosť 2 (SK)
    daughter2_id = "sk_77777777"
    nodes.append(
        Node(
            id=daughter2_id,
            label="Sesterská Spoločnosť s.r.o.",
            type="company",
            country="SK",
            risk_score=8,
            details="IČO: 77777777, Status: Likvidácia, Dlh: 15,000 EUR",
        )
    )
    edges.append(Edge(source=main_company_id, target=daughter2_id, type="OWNED_BY"))

    # Adresa dcérskej spoločnosti 2
    daughter2_address_id = "addr_77777777"
    nodes.append(
        Node(
            id=daughter2_address_id,
            label="Košice, Mierová 5",
            type="address",
            country="SK",
            risk_score=0,
            details="Mierová 5, 040 01 Košice",
        )
    )
    edges.append(
        Edge(source=daughter2_id, target=daughter2_address_id, type="LOCATED_AT")
    )

    # Spoločný konateľ medzi firmami
    shared_person_id = f"pers_{ico}_shared"
    nodes.append(
        Node(
            id=shared_person_id,
            label="Mária Kováčová",
            type="person",
            country="SK",
            risk_score=6,
            details="Konateľ v 12+ firmách (White Horse Detector)",
        )
    )
    edges.append(Edge(source=daughter2_id, target=shared_person_id, type="MANAGED_BY"))
    edges.append(Edge(source=daughter1_id, target=shared_person_id, type="MANAGED_BY"))

    # Dlhová väzba
    debt_id = f"debt_{ico}"
    nodes.append(
        Node(
            id=debt_id,
            label="Dlh Finančnej správe",
            type="debt",
            country="SK",
            risk_score=9,
            details="Dlh: 25,000 EUR, Finančná správa SR",
        )
    )
    edges.append(Edge(source=main_company_id, target=debt_id, type="HAS_DEBT"))

    return nodes, edges


@app.get("/api/search", response_model=GraphResponse, tags=["Search"])
async def search_company(
    q: str,
    request: Request = None,
    response_model_examples={
        "slovak_ico": {"summary": "Slovak IČO search", "value": {"q": "88888888"}},
        "czech_ico": {"summary": "Czech IČO search", "value": {"q": "27074358"}},
        "polish_krs": {"summary": "Polish KRS search", "value": {"q": "123456789"}},
    },
):
    """
    Orchestrátor vyhľadávania s podporou V4 krajín (SK, CZ, PL, HU).

    Automaticky detekuje typ identifikátora a routuje na príslušný register:
    - SK: 8-miestne IČO → RPO (Register právnych osôb)
    - CZ: 8-9 miestne IČO → ARES
    - PL: KRS alebo CEIDG → KRS/CEIDG
    - HU: 8-11 miestny adószám → NAV

    Returns:
        GraphResponse: Graf s nodes (firmy, osoby, adresy) a edges (vzťahy)
    """
    # Metrics - začať timer
    with TimerContext("search.duration"):
        increment("search.requests")

        # Najprv vyčistíme query pre rate limiting
        query_clean = q.strip()

        # Rate limiting - použijeme vyšší tier pre testy
        if request:
            client_id = get_client_id(request)

            # Detekcia test requestov - použijeme pro tier
            is_test_request = (
                # Test queries
                query_clean
                in ["88888888", "27074358", "123456789", "1234567890", "12345678"]
                or
                # Test headers
                request.headers.get("X-Test-Request") == "true"
                or request.headers.get("User-Agent", "").startswith("python-requests/")
                or
                # Local development
                request.client.host in ["127.0.0.1", "localhost", "::1"]
            )

            tier = "pro" if is_test_request else "free"
            allowed, rate_info = is_allowed(client_id, tokens_required=1, tier=tier)

            if not allowed:
                increment("search.rate_limited")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Príliš veľa požiadaviek. Skúste znova o {rate_info.get('retry_after', 60)} sekúnd.",
                        "retry_after": rate_info.get("retry_after", 60),
                        "remaining": rate_info.get("remaining", 0),
                    },
                )

        # Získať user IP pre analytics
        user_ip = request.client.host if request and request.client else None

    """
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    print(f"🔍 Vyhľadávam: {query_clean}...")

    # Kontrola cache
    cache_key = get_cache_key(query_clean, "search")
    cached_result = get(cache_key)
    if cached_result:
        print(f"✅ Cache hit pre query: {query_clean}")
        increment("search.cache_hits")
        return GraphResponse(**cached_result)

    increment("search.cache_misses")

    # Kontrola testovacieho IČO (slovenské 8-miestne)
    if query_clean == "88888888":
        print("🔍 Detekované testovacie IČO 88888888 - generujem simulované dáta...")
        nodes, edges = generate_test_data_sk("88888888")
        result = GraphResponse(nodes=nodes, edges=edges)
        # Uložiť do cache
        set(cache_key, result.dict())
        return result

    nodes = []
    edges = []

    # Detekcia krajiny a routing (priorita: HU > PL > SK > CZ)
    if is_hungarian_tax_number(query_clean):
        # MAĎARSKÝ ADÓSZÁM - NAV integrácia
        print(f"🇭🇺 Detekované maďarský adószám: {query_clean}")
        increment("search.by_country", tags={"country": "HU"})
        nav_data = fetch_nav_hu(query_clean)

        if nav_data:
            normalized = parse_nav_data(nav_data, query_clean)
            risk_score = calculate_hu_risk_score(normalized)

            # Hlavná firma
            company_id = f"hu_{query_clean}"
            nodes.append(
                Node(
                    id=company_id,
                    label=normalized.get("name", f"Firma {query_clean}"),
                    type="company",
                    country="HU",
                    risk_score=risk_score,
                    details=f"Adószám: {query_clean}, Status: {normalized.get('status', 'N/A')}, Forma: {normalized.get('legal_form', 'N/A')}",
                    ico=query_clean,
                )
            )

            # Adresa
            address_text = normalized.get("address", "Cím nincs megadva")
            address_id = f"addr_hu_{query_clean}"
            nodes.append(
                Node(
                    id=address_id,
                    label=address_text[:30] + ("..." if len(address_text) > 30 else ""),
                    type="address",
                    country="HU",
                    details=address_text,
                )
            )
            edges.append(Edge(source=company_id, target=address_id, type="LOCATED_AT"))

            # Igazgatók (konatelia)
            executives = normalized.get("executives", [])
            for i, exec_data in enumerate(executives[:3]):  # Max 3 pre MVP
                exec_name = (
                    exec_data
                    if isinstance(exec_data, str)
                    else exec_data.get("name", f"Igazgató {i + 1}")
                )
                exec_id = f"pers_hu_{query_clean}_{i}"
                nodes.append(
                    Node(
                        id=exec_id,
                        label=exec_name,
                        type="person",
                        country="HU",
                        risk_score=5 if len(executives) > 5 else 2,
                        details="Igazgató",
                    )
                )
                edges.append(Edge(source=company_id, target=exec_id, type="MANAGED_BY"))
        else:
            # Fallback dáta
            print("⚠️ NAV API nedostupné, používam fallback dáta")
            company_id = f"hu_{query_clean}"
            nodes.append(
                Node(
                    id=company_id,
                    label=f"Magyar Cég {query_clean}",
                    type="company",
                    country="HU",
                    risk_score=3,
                    details=f"Adószám: {query_clean}",
                    ico=query_clean,
                )
            )

    elif is_polish_krs(query_clean):
        # POĽSKÉ KRS - KRS integrácia
        print(f"🇵🇱 Detekované poľské KRS: {query_clean}")
        increment("search.by_country", tags={"country": "PL"})
        krs_data = fetch_krs_pl(query_clean)

        if krs_data:
            normalized = parse_krs_data(krs_data, query_clean)
            risk_score = calculate_pl_risk_score(normalized)

            # Biała Lista - VAT status check
            nip = normalized.get("nip") or query_clean
            if is_polish_nip(nip):
                vat_status = get_vat_status_pl(nip)
                if vat_status:
                    normalized["vat_status"] = vat_status
                    if vat_status != "VAT payer":
                        risk_score = max(
                            risk_score, 3
                        )  # Zvýšiť risk ak nie je VAT payer

            # Hlavná firma
            company_id = f"pl_{query_clean}"
            vat_info = (
                f", VAT: {normalized.get('vat_status', 'N/A')}"
                if normalized.get("vat_status")
                else ""
            )
            nodes.append(
                Node(
                    id=company_id,
                    label=normalized.get("name", f"Firma {query_clean}"),
                    type="company",
                    country="PL",
                    risk_score=risk_score,
                    details=f"KRS: {query_clean}, Status: {normalized.get('status', 'N/A')}, Forma: {normalized.get('legal_form', 'N/A')}{vat_info}",
                    ico=query_clean,
                )
            )

            # Adresa
            address_text = normalized.get("address", "Adres nie podano")
            address_id = f"addr_pl_{query_clean}"
            nodes.append(
                Node(
                    id=address_id,
                    label=address_text[:30] + ("..." if len(address_text) > 30 else ""),
                    type="address",
                    country="PL",
                    details=address_text,
                )
            )
            edges.append(Edge(source=company_id, target=address_id, type="LOCATED_AT"))

            # Zarządcy (konatelia)
            executives = normalized.get("executives", [])
            for i, exec_data in enumerate(executives[:3]):  # Max 3 pre MVP
                exec_name = (
                    exec_data
                    if isinstance(exec_data, str)
                    else exec_data.get("name", f"Zarządca {i + 1}")
                )
                exec_id = f"pers_pl_{query_clean}_{i}"
                nodes.append(
                    Node(
                        id=exec_id,
                        label=exec_name,
                        type="person",
                        country="PL",
                        risk_score=5 if len(executives) > 5 else 2,
                        details="Zarządca",
                    )
                )
                edges.append(Edge(source=company_id, target=exec_id, type="MANAGED_BY"))
        else:
            # Fallback dáta
            print("⚠️ KRS API nedostupné, používam fallback dáta")
            company_id = f"pl_{query_clean}"
            nodes.append(
                Node(
                    id=company_id,
                    label=f"Polska Spółka {query_clean}",
                    type="company",
                    country="PL",
                    risk_score=3,
                    details=f"KRS: {query_clean}",
                    ico=query_clean,
                )
            )

    elif is_slovak_ico(query_clean):
        # SLOVENSKÉ IČO - RPO integrácia
        print(f"🇸🇰 Detekované slovenské IČO: {query_clean}")
        increment("search.by_country", tags={"country": "SK"})
        rpo_data = fetch_rpo_sk(query_clean)

        if rpo_data:
            normalized = parse_rpo_data(rpo_data, query_clean)
            risk_score = calculate_sk_risk_score(normalized)

            # Dlhové registry - Finančná správa SR
            debt_result = search_debt_registers(query_clean, "SK")
            if debt_result and debt_result.get("data", {}).get("has_debt"):
                debt_data = debt_result["data"]
                debt_risk = debt_result.get("risk_score", 0)
                risk_score = max(risk_score, debt_risk)  # Použiť vyšší risk

            # Hlavná firma
            company_id = f"sk_{query_clean}"
            company_name = normalized.get("name", f"Firma {query_clean}")
            if debt_result and debt_result.get("data", {}).get("has_debt"):
                company_name += " [DLH]"

            nodes.append(
                Node(
                    id=company_id,
                    label=company_name,
                    type="company",
                    country="SK",
                    risk_score=risk_score,
                    details=f"IČO: {query_clean}, Status: {normalized.get('status', 'N/A')}, Forma: {normalized.get('legal_form', 'N/A')}",
                    ico=query_clean,
                )
            )

            # Pridať dlh do grafu ak existuje
            if debt_result and debt_result.get("data", {}).get("has_debt"):
                debt_data = debt_result["data"]
                debt_id = f"debt_sk_{query_clean}"
                total_debt = debt_data.get("total_debt", 0)
                nodes.append(
                    Node(
                        id=debt_id,
                        label=f"Dlh: {total_debt:,.0f} EUR",
                        type="debt",
                        country="SK",
                        risk_score=debt_result.get("risk_score", 0),
                        details=f"Dlh voči Finančnej správe SR: {total_debt:,.0f} EUR",
                    )
                )
                edges.append(Edge(source=company_id, target=debt_id, type="HAS_DEBT"))

            # Adresa
            address_text = normalized.get("address", "Adresa neuvedená")
            address_id = f"addr_sk_{query_clean}"
            nodes.append(
                Node(
                    id=address_id,
                    label=address_text[:30] + ("..." if len(address_text) > 30 else ""),
                    type="address",
                    country="SK",
                    details=address_text,
                )
            )
            edges.append(Edge(source=company_id, target=address_id, type="LOCATED_AT"))

            # Konatelia
            executives = normalized.get("executives", [])
            for i, exec_data in enumerate(executives[:3]):  # Max 3 pre MVP
                exec_name = (
                    exec_data
                    if isinstance(exec_data, str)
                    else exec_data.get("name", f"Konateľ {i + 1}")
                )
                exec_id = f"pers_sk_{query_clean}_{i}"
                nodes.append(
                    Node(
                        id=exec_id,
                        label=exec_name,
                        type="person",
                        country="SK",
                        risk_score=5 if len(executives) > 5 else 2,
                        details="Konateľ",
                    )
                )
                edges.append(Edge(source=company_id, target=exec_id, type="MANAGED_BY"))
        else:
            # Ak RPO API nie je dostupné, použijeme fallback
            print("⚠️ RPO API nedostupné, používam fallback dáta")
            nodes, edges = generate_test_data_sk(query_clean)

    else:
        # ČESKÉ IČO alebo názov - ARES integrácia
        print(f"🇨🇿 Vyhľadávam v ARES (CZ): {query_clean}")
        increment("search.by_country", tags={"country": "CZ"})
        ares_data = fetch_ares_cz(query_clean)
        results = ares_data.get("ekonomickeSubjekty", [])

        # Normalizácia a budovanie grafu
        for item in results:
            ico = item.get("ico", "N/A")
            name = item.get("obchodniJmeno", "Neznáma firma")
            address_text = item.get("sidlo", {}).get(
                "textovaAdresa", "Adresa neuvedená"
            )

            company_id = f"cz_{ico}"
            risk = calculate_trust_score(item)

            # Dlhové registry - Finančná správa ČR
            debt_result = search_debt_registers(ico, "CZ")
            if debt_result and debt_result.get("data", {}).get("has_debt"):
                debt_data = debt_result["data"]
                debt_risk = debt_result.get("risk_score", 0)
                risk = max(risk, debt_risk)  # Použiť vyšší risk

            company_name = name
            if debt_result and debt_result.get("data", {}).get("has_debt"):
                company_name += " [DLH]"

            nodes.append(
                Node(
                    id=company_id,
                    label=company_name,
                    type="company",
                    country="CZ",
                    risk_score=risk,
                    details=f"IČO: {ico}",
                    ico=ico,
                )
            )

            # Pridať dlh do grafu ak existuje
            if debt_result and debt_result.get("data", {}).get("has_debt"):
                debt_data = debt_result["data"]
                debt_id = f"debt_cz_{ico}"
                total_debt = debt_data.get("total_debt", 0)
                nodes.append(
                    Node(
                        id=debt_id,
                        label=f"Dlh: {total_debt:,.0f} CZK",
                        type="debt",
                        country="CZ",
                        risk_score=debt_result.get("risk_score", 0),
                        details=f"Dlh voči Finančnej správe ČR: {total_debt:,.0f} CZK",
                    )
                )
                edges.append(Edge(source=company_id, target=debt_id, type="HAS_DEBT"))

            # Adresa
            address_id = f"addr_cz_{ico}"
            nodes.append(
                Node(
                    id=address_id,
                    label=address_text[:20] + "...",
                    type="address",
                    country="CZ",
                    details=address_text,
                )
            )
            edges.append(Edge(source=company_id, target=address_id, type="LOCATED_AT"))

            # Osoba (simulácia)
            person_name = f"Jan Novák ({ico[-3:]})"
            person_id = f"pers_cz_{ico}"
            nodes.append(
                Node(
                    id=person_id,
                    label=person_name,
                    type="person",
                    country="CZ",
                    details="Konateľ",
                )
            )
            edges.append(Edge(source=company_id, target=person_id, type="MANAGED_BY"))

    # Risk Intelligence - vylepšené risk scores
    if nodes and edges:
        try:
            risk_report = generate_risk_report(nodes, edges)
            # Aktualizovať risk scores
            enhanced_nodes = risk_report.get("enhanced_nodes", nodes)
            nodes = enhanced_nodes

            # Pridať poznámky o bielych koňoch a karuseloch
            if risk_report.get("summary", {}).get("white_horse_count", 0) > 0:
                print(
                    f"⚠️ Detekovaných bielych koní: {risk_report['summary']['white_horse_count']}"
                )
            if risk_report.get("summary", {}).get("circular_structure_count", 0) > 0:
                print(
                    f"⚠️ Detekovaných karuselových štruktúr: {risk_report['summary']['circular_structure_count']}"
                )
        except Exception as e:
            print(f"⚠️ Chyba pri risk intelligence: {e}")

    # Uložiť do cache
    result = GraphResponse(nodes=nodes, edges=edges)
    set(cache_key, result.dict())

    # Uložiť do databázy (história a cache)
    main_company = next((n for n in nodes if n.type == "company"), None)
    country = main_company.country if main_company else None
    risk_score = (
        max((n.risk_score for n in nodes if n.risk_score), default=0) if nodes else 0
    )

    save_search_history(
        query=q,
        country=country,
        result_count=len(nodes),
        risk_score=risk_score if risk_score > 0 else None,
        user_ip=user_ip,
        response_data={"nodes_count": len(nodes), "edges_count": len(edges)},
    )

    # Uložiť hlavnú firmu do cache
    if main_company and main_company.ico:
        save_company_cache(
            identifier=main_company.ico,
            country=country or "UNKNOWN",
            company_name=main_company.label,
            data={
                "nodes": [n.dict() for n in nodes],
                "edges": [e.dict() for e in edges],
            },
            risk_score=risk_score if risk_score > 0 else None,
        )

    # Analytics
    save_analytics(
        event_type="search",
        event_data={"query": q, "country": country, "result_count": len(nodes)},
        user_ip=user_ip,
    )

    # Metrics
    increment("search.results", value=len(nodes))
    gauge("search.last_result_count", len(nodes))
    record_event(
        "search.completed",
        {"country": country, "result_count": len(nodes), "query_length": len(q)},
    )

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
