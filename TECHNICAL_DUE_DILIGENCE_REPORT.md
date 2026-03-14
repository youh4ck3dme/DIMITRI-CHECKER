# 📊 V4-Finstat Projekt v5.0 - Technical Due Diligence & Architecture Report

**Dátum:** 14. marec 2026  
**Verzia:** 5.0  
**Autor:** Senior CTO  
**Status:** Enterprise Ready

---

## 1. EXECUTIVE TECHNICAL SUMMARY

### Tech Stack Overview

#### Frontend
- **Framework:** React 18 + Vite (modulárny build system)
- **Styling:** Tailwind CSS + PostCSS (atomic CSS framework)
- **Visualization:** react-force-graph-2d (d3-force pre backend)
- **Routing:** React Router v6 (SPA navigation)
- **State Management:** React Context API (AuthContext)
- **Performance:** Code splitting, memoization, lazy loading
- **PWA:** Service Worker, offline capabilities

#### Backend
- **Framework:** FastAPI (Python 3.10+) - ASGI server
- **Database:** PostgreSQL 15 (primary) + Redis 7 (cache)
- **Authentication:** JWT + bcrypt (OAuth2PasswordBearer)
- **Payments:** Stripe integration (subscription management)
- **Monitoring:** Custom metrics system (TimerContext, gauges)
- **Testing:** Pytest + Vitest (frontend)

#### Infrastructure
- **Containerization:** Docker + Docker Compose (multi-service)
- **Caching:** Redis (distributed cache, rate limiting)
- **Load Balancing:** Built-in FastAPI + Docker orchestration
- **Security:** CORS, rate limiting, circuit breaker pattern
- **Monitoring:** Custom metrics, health checks

### Architecture Decision Rationale

**Why This Stack?**

1. **Scalability:** Microservice-ready monolith with clear separation
2. **Performance:** React virtualization + FastAPI async + Redis caching
3. **Developer Experience:** TypeScript/Python typing + hot reload
4. **Production Ready:** Docker, health checks, monitoring, logging
5. **Cost Efficiency:** Single server deployment with horizontal scaling

**Key Performance Targets:**
- **Response Time:** <1s for cached queries, <3s for live scraping
- **Concurrent Users:** 1000+ with current architecture
- **Data Freshness:** Real-time with intelligent caching (TTL-based)
- **Uptime:** 99.9% with circuit breaker and fallback mechanisms

---

## 2. ARCHITEKTÚRA SYSTÉMU

### Data Flow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   API Gateway    │    │   Rate Limiter  │
│   (React App)   │───▶│   (FastAPI)      │───▶│   (Token Bucket)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌──────────────────┐    ┌─────────────────┐
         │              │   Auth Service   │    │   Circuit       │
         │              │   (JWT/OAuth2)   │    │   Breaker       │
         │              └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Search API    │    │   Cache Layer    │    │   Fallback      │
│   (V4 Countries)│───▶│   (Redis)        │───▶│   Mechanisms    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Country       │    │   Database       │    │   External      │
│   Integrations  │───▶│   (PostgreSQL)   │───▶│   APIs          │
│   (SK/CZ/PL/HU) │    │   (Analytics)    │    │   (ARES/RPO)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Modules Deep Dive

#### a) Scraper Engine

**Purpose:** High-performance data collection from V4 state registries

**Key Features:**
- **Proxy Rotation:** Automatic IP rotation for anti-blocking
- **Rate Limiting:** Per-country limits (SK: 60/min, CZ: 100/min, PL: 50/min, HU: 30/min)
- **Circuit Breaker:** Automatic fallback when external APIs fail
- **Retry Logic:** Exponential backoff with jitter

**Implementation:**
```python
# services/proxy_rotation.py
class ProxyRotator:
    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.current_index = 0
        self.failed_proxies = set()
    
    def get_next_proxy(self) -> Optional[str]:
        # Round-robin with failure tracking
        for _ in range(len(self.proxies)):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            if proxy not in self.failed_proxies:
                return proxy
        return None
```

**Country-Specific Optimizations:**
- **Slovakia (SK):** RPO API primary, ORSR scraping fallback
- **Czech Republic (CZ):** ARES API with direct HTTP requests
- **Poland (PL):** KRS + CEIDG + Biała Lista integration
- **Hungary (HU):** NAV Online API with XML parsing

#### b) Nexus Resolver

**Purpose:** Advanced entity linking and relationship discovery

**Algorithm Overview:**
1. **Entity Normalization:** Standardize names, addresses, identifiers
2. **Fuzzy Matching:** Levenshtein distance for name variations
3. **Graph Analysis:** Detect circular ownership, white horses
4. **Risk Scoring:** Multi-factor risk assessment

**Key Components:**
```python
# services/risk_intelligence.py
class NexusResolver:
    def resolve_connections(self, nodes: List[Node], edges: List[Edge]) -> GraphResponse:
        # 1. Detect white horses (same person in multiple companies)
        white_horses = self._detect_white_horses(nodes)
        
        # 2. Find circular structures
        circular_structures = self._detect_circular_ownership(edges)
        
        # 3. Calculate enhanced risk scores
        enhanced_nodes = self._calculate_enhanced_risk(nodes, edges)
        
        # 4. Add relationship insights
        insight_edges = self._generate_insight_edges(nodes, edges)
        
        return GraphResponse(
            nodes=enhanced_nodes + white_horses,
            edges=edges + insight_edges
        )
```

**Advanced Features:**
- **White Horse Detection:** Identify shell company patterns
- **Circular Ownership:** Detect money laundering structures
- **Virtual Seat Analysis:** Flag high-risk addresses
- **Cross-Border Links:** Map international ownership chains

#### c) ERP Integration Hub

**Purpose:** Seamless integration with enterprise resource planning systems

**Supported Systems:**
- **SAP:** RFC connection with BAPI integration
- **Pohoda:** REST API with XML data exchange
- **Money S3:** SOAP API with custom connector

**Architecture:**
```python
# services/erp/base_connector.py
class ERPConnector(ABC):
    @abstractmethod
    async def connect(self) -> bool: pass
    
    @abstractmethod
    async def sync_suppliers(self) -> List[Dict]: pass
    
    @abstractmethod
    async def sync_payments(self, supplier_ico: str) -> List[Dict]: pass
    
    @abstractmethod
    async def get_company_data(self, ico: str) -> Dict: pass
```

**Integration Features:**
- **Real-time Sync:** Webhook-based updates
- **Batch Processing:** Scheduled data synchronization
- **Error Handling:** Retry mechanisms with exponential backoff
- **Data Validation:** Cross-reference with state registries

---

## 3. ŠTRUKTÚRA PROJEKTU

### Directory Structure

```
V4-Finstat-Projekt/
├── backend/                          # FastAPI Backend Service
│   ├── main.py                      # API Gateway & Orchestrator
│   ├── requirements.txt             # Python Dependencies
│   ├── pyrightconfig.json           # Type Checking Config
│   ├── Dockerfile                   # Container Definition
│   ├── setup_database.sh            # DB Initialization
│   ├── data/                        # Static Data Files
│   │   └── postal_codes_sk.csv      # Slovak Postal Codes
│   ├── middleware/                  # Custom Middleware
│   │   └── api_auth.py              # Authentication Middleware
│   ├── migrations/                  # Database Migrations
│   │   ├── add_company_data_column.py
│   │   ├── add_consent_fields.py
│   │   ├── add_fulltext_search.py
│   │   ├── add_stripe_customer_id.py
│   │   ├── create_api_keys_table.py
│   │   └── create_webhooks_tables.py
│   ├── scripts/                     # Utility Scripts
│   │   └── convert_postal_codes.py  # Data Processing
│   ├── services/                    # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── analytics.py             # Usage Analytics
│   │   ├── api_keys.py              # API Key Management
│   │   ├── auth.py                  # Authentication Service
│   │   ├── cache.py                 # Redis Cache Service
│   │   ├── circuit_breaker.py       # Circuit Breaker Pattern
│   │   ├── database.py              # PostgreSQL ORM
│   │   ├── debt_registers.py        # Financial Registry Integration
│   │   ├── error_handler.py         # Global Error Handling
│   │   ├── export_service.py        # Excel/PDF Export
│   │   ├── favorites.py             # User Favorites
│   │   ├── hu_nav.py                # Hungarian NAV Integration
│   │   ├── metrics.py               # Performance Metrics
│   │   ├── performance.py           # Performance Optimization
│   │   ├── pl_biala_lista.py        # Polish VAT Status
│   │   ├── pl_ceidg.py              # Polish CEIDG Integration
│   │   ├── pl_krs.py                # Polish KRS Integration
│   │   ├── proxy_rotation.py        # Proxy Management
│   │   ├── rate_limiter.py          # Rate Limiting Service
│   │   ├── redis_cache.py           # Redis Operations
│   │   ├── risk_intelligence.py     # Advanced Risk Analysis
│   │   ├── search_by_name.py        # Name-based Search
│   │   ├── sk_orsr_provider.py      # Slovak ORSR Provider
│   │   ├── sk_region_resolver.py    # Slovak Region Mapping
│   │   ├── sk_rpo.py                # Slovak RPO Integration
│   │   ├── sk_ruz_provider.py       # Slovak RÚZ Provider
│   │   ├── sk_zrsr_provider.py      # Slovak ZRSR Provider
│   │   ├── stripe_service.py        # Payment Processing
│   │   ├── webhooks.py              # Webhook Management
│   │   └── erp/                     # ERP Integration Module
│   │       ├── __init__.py
│   │       ├── base_connector.py    # Base ERP Connector
│   │       ├── erp_service.py       # ERP Service Manager
│   │       ├── models.py            # ERP Data Models
│   │       ├── money_s3_connector.py # Money S3 Integration
│   │       ├── pohoda_connector.py   # Pohoda Integration
│   │       └── sap_connector.py      # SAP Integration
│   └── tests/                       # Backend Tests
│       ├── __init__.py
│       ├── test_api.py              # API Endpoint Tests
│       ├── test_cache.py            # Cache Logic Tests
│       ├── test_database.py         # Database Tests
│       ├── test_risk_intelligence.py # Risk Analysis Tests
│       └── test_erp_integration.py   # ERP Integration Tests
│
├── frontend/                         # React Frontend Application
│   ├── index.html                    # Main HTML Template
│   ├── package.json                  # NPM Dependencies
│   ├── vite.config.js                # Vite Build Configuration
│   ├── tailwind.config.js            # Tailwind CSS Config
│   ├── postcss.config.js             # PostCSS Configuration
│   ├── vitest.config.js              # Testing Configuration
│   ├── Dockerfile                    # Frontend Container
│   ├── public/                       # Static Assets
│   │   ├── favicon.ico               # Application Icon
│   │   ├── favicon.svg               # SVG Icon
│   │   ├── offline.html              # Offline Page
│   │   └── sw-offline.js             # Service Worker
│   ├── src/                          # Source Code
│   │   ├── main.jsx                  # Application Entry Point
│   │   ├── index.css                 # Global Styles
│   │   ├── App.jsx                   # Main App Component
│   │   ├── components/               # Reusable Components
│   │   │   ├── Disclaimer.jsx        # Legal Disclaimer
│   │   │   ├── ErrorBoundary.jsx     # Error Handling
│   │   │   ├── Footer.jsx            # Application Footer
│   │   │   ├── ForceGraph.jsx        # Graph Visualization
│   │   │   ├── IluminatiLogo.jsx     # Brand Logo
│   │   │   ├── Layout.jsx            # Layout Wrapper
│   │   │   ├── LoadingSkeleton.jsx   # Loading States
│   │   │   ├── Logo.jsx              # Application Logo
│   │   │   ├── ProtectedRoute.jsx    # Authenticated Routes
│   │   │   ├── RateLimitIndicator.jsx # Rate Limit Status
│   │   │   ├── SEOHead.jsx           # SEO Meta Tags
│   │   │   ├── __tests__/            # Component Tests
│   │   │   │   ├── ErrorBoundary.test.jsx
│   │   │   │   ├── Footer.test.jsx
│   │   │   │   ├── IluminatiLogo.test.jsx
│   │   │   │   └── LoadingSkeleton.test.jsx
│   │   │   └── ui/                   # UI Components
│   │   │       ├── Button.jsx        # Custom Button
│   │   │       ├── Input.jsx         # Form Input
│   │   │       ├── Modal.jsx         # Modal Dialog
│   │   │       └── Toast.jsx         # Notification System
│   │   ├── config/                   # Configuration
│   │   │   └── api.js                # API Configuration
│   │   ├── contexts/                 # React Context
│   │   │   └── AuthContext.jsx       # Authentication Context
│   │   ├── hooks/                    # Custom Hooks
│   │   │   ├── useKeyboardShortcuts.js # Keyboard Navigation
│   │   │   ├── useOffline.js         # Offline Detection
│   │   │   └── useTheme.js           # Theme Management
│   │   ├── pages/                    # Application Pages
│   │   │   ├── Analytics.jsx         # Analytics Dashboard
│   │   │   ├── ApiKeys.jsx           # API Key Management
│   │   │   ├── CookiePolicy.jsx      # Cookie Policy
│   │   │   ├── Dashboard.jsx         # User Dashboard
│   │   │   ├── DataProcessingAgreement.jsx # DPA Page
