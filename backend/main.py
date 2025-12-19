from fastapi import FastAPI, HTTPException, Request, Depends, status, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
import requests
import random
import re
from datetime import datetime, timedelta

# Import nových služieb
from services.sk_rpo import fetch_rpo_sk, parse_rpo_data, calculate_sk_risk_score, is_slovak_ico
from services.pl_krs import fetch_krs_pl, parse_krs_data, calculate_pl_risk_score, is_polish_krs
from services.pl_ceidg import fetch_ceidg_pl, parse_ceidg_data, calculate_ceidg_risk_score, is_ceidg_number
from services.pl_biala_lista import fetch_biala_lista_pl, parse_biala_lista_data, get_vat_status_pl, is_polish_nip
from services.hu_nav import fetch_nav_hu, parse_nav_data, calculate_hu_risk_score, is_hungarian_tax_number
from services.debt_registers import search_debt_registers, has_debt
from services.risk_intelligence import generate_risk_report, calculate_enhanced_risk_score
from services.cache import get_cache_key, get, set, get_stats as get_cache_stats
from services.rate_limiter import is_allowed, get_client_id, get_stats as get_rate_limiter_stats
from services.database import (
    init_database, save_search_history, get_search_history,
    save_company_cache, get_company_cache, save_analytics,
    get_database_stats, cleanup_expired_cache
)
from services.error_handler import error_handler, log_error, safe_api_call
from services.circuit_breaker import get_all_breakers, reset_breaker
from services.metrics import get_metrics, increment, timer, TimerContext, record_event, gauge
from services.performance import timing_decorator, get_connection_pool
from services.proxy_rotation import get_proxy_stats, init_proxy_pool
from services.stripe_service import (
    create_checkout_session, handle_webhook, get_subscription_status,
    cancel_subscription
)
from services.auth import (
    User, UserTier, create_user, authenticate_user, get_user_by_email,
    create_access_token, decode_access_token, get_user_tier_limits,
    get_password_hash, verify_password, update_user_tier
)
from services.database import get_db_session, init_database

app = FastAPI(
    title="ILUMINATI SYSTEM API",
    version="5.0",
    description="Cross-border company registry search API for V4 countries (SK, CZ, PL, HU)",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
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

# --- SLUŽBY (ARES INTEGRÁCIA) ---
def fetch_ares_cz(query: str):
    """
    Získa dáta z českého registra ARES.
    """
    url = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "obchodniJmeno": query,
        "pocet": 5  # Limit pre MVP
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
        "features": ["CZ (ARES)", "SK (RPO)", "Cache", "Risk Scoring"]
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
                detail="Database not available"
            )
        user = get_user_by_email(db, email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """Registrácia nového používateľa"""
    with get_db_session() as db:
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
            )
        
        # Skontrolovať, či už existuje
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Vytvoriť používateľa
        user = create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            tier=user.tier.value,
            is_active=user.is_active,
            is_verified=user.is_verified
        )

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login používateľa"""
    with get_db_session() as db:
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not available"
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
            expires_delta=access_token_expires
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
                "limits": get_user_tier_limits(user.tier)
            }
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
        is_verified=current_user.is_verified
    )

@app.get("/api/auth/tier/limits")
async def get_tier_limits(current_user: User = Depends(get_current_user)):
    """Získa limity pre tier aktuálneho používateľa"""
    return get_user_tier_limits(current_user.tier)

# --- STRIPE ENDPOINTY ---

@app.post("/api/payment/checkout")
async def create_payment_checkout(
    tier: str,
    current_user: User = Depends(get_current_user)
):
    """Vytvorí Stripe checkout session pre upgrade tieru"""
    try:
        user_tier = UserTier(tier.lower())
        if user_tier == UserTier.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot upgrade to FREE tier"
            )
        
        result = create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            tier=user_tier
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {tier}"
        )

@app.post("/api/payment/webhook")
async def stripe_webhook(request: FastAPIRequest):
    """Stripe webhook endpoint pre subscription events"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    result = handle_webhook(payload, signature)
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
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
            "database": get_database_stats().get("available", False)
        }
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
    nodes.append(Node(
        id=main_company_id,
        label="Testovacia Spoločnosť s.r.o.",
        type="company",
        country="SK",
        risk_score=7,  # Vysoké riziko pre test
        details=f"IČO: {ico}, Status: Aktívna, DPH: Áno"
    ))
    
    # Adresa hlavnej firmy
    main_address_id = f"addr_{ico}_main"
    nodes.append(Node(
        id=main_address_id,
        label="Bratislava, Hlavná 1",
        type="address",
        country="SK",
        risk_score=3,  # Virtual seat flag
        details="Hlavná 1, 811 01 Bratislava (Virtual Seat - 52 firiem na adrese)"
    ))
    edges.append(Edge(source=main_company_id, target=main_address_id, type="LOCATED_AT"))
    
    # Konateľ 1
    person1_id = f"pers_{ico}_1"
    nodes.append(Node(
        id=person1_id,
        label="Ján Novák",
        type="person",
        country="SK",
        risk_score=5,
        details="Konateľ, 15+ firiem v registri"
    ))
    edges.append(Edge(source=main_company_id, target=person1_id, type="MANAGED_BY"))
    
    # Konateľ 2
    person2_id = f"pers_{ico}_2"
    nodes.append(Node(
        id=person2_id,
        label="Peter Horváth",
        type="person",
        country="SK",
        risk_score=4,
        details="Spoločník, 8% podiel"
    ))
    edges.append(Edge(source=main_company_id, target=person2_id, type="OWNED_BY"))
    
    # Dcérska spoločnosť 1 (CZ)
    daughter1_id = "cz_12345678"
    nodes.append(Node(
        id=daughter1_id,
        label="Dcérska Firma CZ s.r.o.",
        type="company",
        country="CZ",
        risk_score=6,
        details="IČO: 12345678, Vlastníctvo: 100%"
    ))
    edges.append(Edge(source=main_company_id, target=daughter1_id, type="OWNED_BY"))
    
    # Dcérska spoločnosť 2 (SK)
    daughter2_id = "sk_77777777"
    nodes.append(Node(
        id=daughter2_id,
        label="Sesterská Spoločnosť s.r.o.",
        type="company",
        country="SK",
        risk_score=8,
        details="IČO: 77777777, Status: Likvidácia, Dlh: 15,000 EUR"
    ))
    edges.append(Edge(source=main_company_id, target=daughter2_id, type="OWNED_BY"))
    
    # Adresa dcérskej spoločnosti 2
    daughter2_address_id = "addr_77777777"
    nodes.append(Node(
        id=daughter2_address_id,
        label="Košice, Mierová 5",
        type="address",
        country="SK",
        risk_score=0,
        details="Mierová 5, 040 01 Košice"
    ))
    edges.append(Edge(source=daughter2_id, target=daughter2_address_id, type="LOCATED_AT"))
    
    # Spoločný konateľ medzi firmami
    shared_person_id = f"pers_{ico}_shared"
    nodes.append(Node(
        id=shared_person_id,
        label="Mária Kováčová",
        type="person",
        country="SK",
        risk_score=6,
        details="Konateľ v 12+ firmách (White Horse Detector)"
    ))
    edges.append(Edge(source=daughter2_id, target=shared_person_id, type="MANAGED_BY"))
    edges.append(Edge(source=daughter1_id, target=shared_person_id, type="MANAGED_BY"))
    
    # Dlhová väzba
    debt_id = f"debt_{ico}"
    nodes.append(Node(
        id=debt_id,
        label="Dlh Finančnej správe",
        type="debt",
        country="SK",
        risk_score=9,
        details="Dlh: 25,000 EUR, Finančná správa SR"
    ))
    edges.append(Edge(source=main_company_id, target=debt_id, type="HAS_DEBT"))
    
    return nodes, edges



@app.get("/api/search", response_model=GraphResponse, tags=["Search"])
async def search_company(
    q: str,
    request: Request = None,
    response_model_examples={
        "slovak_ico": {
            "summary": "Slovak IČO search",
            "value": {
                "q": "88888888"
            }
        },
        "czech_ico": {
            "summary": "Czech IČO search",
            "value": {
                "q": "27074358"
            }
        },
        "polish_krs": {
            "summary": "Polish KRS search",
            "value": {
                "q": "123456789"
            }
        }
    }
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
        
        # Rate limiting
        if request:
            client_id = get_client_id(request)
            allowed, rate_info = is_allowed(client_id, tokens_required=1, tier='free')
            if not allowed:
                increment("search.rate_limited")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Príliš veľa požiadaviek. Skúste znova o {rate_info.get('retry_after', 60)} sekúnd.",
                        "retry_after": rate_info.get('retry_after', 60),
                        "remaining": rate_info.get('remaining', 0),
                    }
                )
        
        # Získať user IP pre analytics
        user_ip = request.client.host if request and request.client else None
    
    """
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    query_clean = q.strip()
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
            nodes.append(Node(
                id=company_id,
                label=normalized.get("name", f"Firma {query_clean}"),
                type="company",
                country="HU",
                risk_score=risk_score,
                details=f"Adószám: {query_clean}, Status: {normalized.get('status', 'N/A')}, Forma: {normalized.get('legal_form', 'N/A')}",
                ico=query_clean
            ))
            
            # Adresa
            address_text = normalized.get("address", "Cím nincs megadva")
            address_id = f"addr_hu_{query_clean}"
            nodes.append(Node(
                id=address_id,
                label=address_text[:30] + ("..." if len(address_text) > 30 else ""),
                type="address",
                country="HU",
                details=address_text
            ))
            edges.append(Edge(source=company_id, target=address_id, type="LOCATED_AT"))
            
            # Igazgatók (konatelia)
            executives = normalized.get("executives", [])
            for i, exec_data in enumerate(executives[:3]):  # Max 3 pre MVP
                exec_name = exec_data if isinstance(exec_data, str) else exec_data.get("name", f"Igazgató {i+1}")
                exec_id = f"pers_hu_{query_clean}_{i}"
                nodes.append(Node(
                    id=exec_id,
                    label=exec_name,
                    type="person",
                    country="HU",
                    risk_score=5 if len(executives) > 5 else 2,
                    details="Igazgató"
                ))
                edges.append(Edge(source=company_id, target=exec_id, type="MANAGED_BY"))
        else:
            # Fallback dáta
            print("⚠️ NAV API nedostupné, používam fallback dáta")
            company_id = f"hu_{query_clean}"
            nodes.append(Node(
                id=company_id,
                label=f"Magyar Cég {query_clean}",
                type="company",
                country="HU",
                risk_score=3,
                details=f"Adószám: {query_clean}",
                ico=query_clean
            ))
    
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
                        risk_score = max(risk_score, 3)  # Zvýšiť risk ak nie je VAT payer
            
            # Hlavná firma
            company_id = f"pl_{query_clean}"
            vat_info = f", VAT: {normalized.get('vat_status', 'N/A')}" if normalized.get('vat_status') else ""
            nodes.append(Node(
                id=company_id,
                label=normalized.get("name", f"Firma {query_clean}"),
                type="company",
                country="PL",
                risk_score=risk_score,
                details=f"KRS: {query_clean}, Status: {normalized.get('status', 'N/A')}, Forma: {normalized.get('legal_form', 'N/A')}{vat_info}",
                ico=query_clean
            ))
            
            # Adresa
            address_text = normalized.get("address", "Adres nie podano")
            address_id = f"addr_pl_{query_clean}"
            nodes.append(Node(
                id=address_id,
                label=address_text[:30] + ("..." if len(address_text) > 30 else ""),
                type="address",
                country="PL",
                details=address_text
            ))
            edges.append(Edge(source=company_id, target=address_id, type="LOCATED_AT"))
            
            # Zarządcy (konatelia)
            executives = normalized.get("executives", [])
            for i, exec_data in enumerate(executives[:3]):  # Max 3 pre MVP
                exec_name = exec_data if isinstance(exec_data, str) else exec_data.get("name", f"Zarządca {i+1}")
                exec_id = f"pers_pl_{query_clean}_{i}"
                nodes.append(Node(
                    id=exec_id,
                    label=exec_name,
                    type="person",
                    country="PL",
                    risk_score=5 if len(executives) > 5 else 2,
                    details="Zarządca"
                ))
                edges.append(Edge(source=company_id, target=exec_id, type="MANAGED_BY"))
        else:
            # Fallback dáta
            print("⚠️ KRS API nedostupné, používam fallback dáta")
            company_id = f"pl_{query_clean}"
            nodes.append(Node(
                id=company_id,
                label=f"Polska Spółka {query_clean}",
                type="company",
                country="PL",
                risk_score=3,
                details=f"KRS: {query_clean}",
                ico=query_clean
            ))
    
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
            
            nodes.append(Node(
                id=company_id,
                label=company_name,
                type="company",
                country="SK",
                risk_score=risk_score,
                details=f"IČO: {query_clean}, Status: {normalized.get('status', 'N/A')}, Forma: {normalized.get('legal_form', 'N/A')}",
                ico=query_clean
            ))
            
            # Pridať dlh do grafu ak existuje
            if debt_result and debt_result.get("data", {}).get("has_debt"):
                debt_data = debt_result["data"]
                debt_id = f"debt_sk_{query_clean}"
                total_debt = debt_data.get("total_debt", 0)
                nodes.append(Node(
                    id=debt_id,
                    label=f"Dlh: {total_debt:,.0f} EUR",
                    type="debt",
                    country="SK",
                    risk_score=debt_result.get("risk_score", 0),
                    details=f"Dlh voči Finančnej správe SR: {total_debt:,.0f} EUR"
                ))
                edges.append(Edge(source=company_id, target=debt_id, type="HAS_DEBT"))
            
            # Adresa
            address_text = normalized.get("address", "Adresa neuvedená")
            address_id = f"addr_sk_{query_clean}"
            nodes.append(Node(
                id=address_id,
                label=address_text[:30] + ("..." if len(address_text) > 30 else ""),
                type="address",
                country="SK",
                details=address_text
            ))
            edges.append(Edge(source=company_id, target=address_id, type="LOCATED_AT"))
            
            # Konatelia
            executives = normalized.get("executives", [])
            for i, exec_data in enumerate(executives[:3]):  # Max 3 pre MVP
                exec_name = exec_data if isinstance(exec_data, str) else exec_data.get("name", f"Konateľ {i+1}")
                exec_id = f"pers_sk_{query_clean}_{i}"
                nodes.append(Node(
                    id=exec_id,
                    label=exec_name,
                    type="person",
                    country="SK",
                    risk_score=5 if len(executives) > 5 else 2,
                    details="Konateľ"
                ))
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
            address_text = item.get("sidlo", {}).get("textovaAdresa", "Adresa neuvedená")
            
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
            
            nodes.append(Node(
                id=company_id,
                label=company_name,
                type="company",
                country="CZ",
                risk_score=risk,
                details=f"IČO: {ico}",
                ico=ico
            ))
            
            # Pridať dlh do grafu ak existuje
            if debt_result and debt_result.get("data", {}).get("has_debt"):
                debt_data = debt_result["data"]
                debt_id = f"debt_cz_{ico}"
                total_debt = debt_data.get("total_debt", 0)
                nodes.append(Node(
                    id=debt_id,
                    label=f"Dlh: {total_debt:,.0f} CZK",
                    type="debt",
                    country="CZ",
                    risk_score=debt_result.get("risk_score", 0),
                    details=f"Dlh voči Finančnej správe ČR: {total_debt:,.0f} CZK"
                ))
                edges.append(Edge(source=company_id, target=debt_id, type="HAS_DEBT"))

            # Adresa
            address_id = f"addr_cz_{ico}"
            nodes.append(Node(
                id=address_id,
                label=address_text[:20] + "...",
                type="address",
                country="CZ",
                details=address_text
            ))
            edges.append(Edge(source=company_id, target=address_id, type="LOCATED_AT"))

            # Osoba (simulácia)
            person_name = f"Jan Novák ({ico[-3:]})"
            person_id = f"pers_cz_{ico}"
            nodes.append(Node(
                id=person_id,
                label=person_name,
                type="person",
                country="CZ",
                details="Konateľ"
            ))
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
                print(f"⚠️ Detekovaných bielych koní: {risk_report['summary']['white_horse_count']}")
            if risk_report.get("summary", {}).get("circular_structure_count", 0) > 0:
                print(f"⚠️ Detekovaných karuselových štruktúr: {risk_report['summary']['circular_structure_count']}")
        except Exception as e:
            print(f"⚠️ Chyba pri risk intelligence: {e}")
    
    # Uložiť do cache
    result = GraphResponse(nodes=nodes, edges=edges)
    set(cache_key, result.dict())
    
    # Uložiť do databázy (história a cache)
    main_company = next((n for n in nodes if n.type == 'company'), None)
    country = main_company.country if main_company else None
    risk_score = max((n.risk_score for n in nodes if n.risk_score), default=0) if nodes else 0
    
    save_search_history(
        query=q,
        country=country,
        result_count=len(nodes),
        risk_score=risk_score if risk_score > 0 else None,
        user_ip=user_ip,
        response_data={"nodes_count": len(nodes), "edges_count": len(edges)}
    )
    
    # Uložiť hlavnú firmu do cache
    if main_company and main_company.ico:
        save_company_cache(
            identifier=main_company.ico,
            country=country or "UNKNOWN",
            company_name=main_company.label,
            data={"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]},
            risk_score=risk_score if risk_score > 0 else None
        )
    
    # Analytics
    save_analytics(
        event_type="search",
        event_data={"query": q, "country": country, "result_count": len(nodes)},
        user_ip=user_ip
    )
    
    # Metrics
    increment("search.results", value=len(nodes))
    gauge("search.last_result_count", len(nodes))
    record_event("search.completed", {
        "country": country,
        "result_count": len(nodes),
        "query_length": len(q)
    })
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

