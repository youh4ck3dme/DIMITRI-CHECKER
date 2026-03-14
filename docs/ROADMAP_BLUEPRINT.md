# 🗺️ V4-Finstat Projekt - Roadmapa & Blueprint

**Aktuálny stav:** ~95% dokončené | **Test coverage:** 85%  
**Posledná aktualizácia:** December 20, 2024

---

## 📊 Aktuálny Stav Projektu

| Komponenta | Dokončenie | Status |
|------------|------------|--------|
| Backend Core | 95% | ✅ Takmer hotovo |
| Frontend Core | 90% | ✅ Takmer hotovo |
| Country Integrations (V4) | 100% | ✅ Hotovo |
| Risk Intelligence | 100% | ✅ Hotovo |
| Performance & Optimization | 100% | ✅ Hotovo |
| Documentation | 100% | ✅ Hotovo |
| Testing | 85% | ✅ Vylepšené |
| **Authentication & Monetization** | **100%** | ✅ **Hotovo** |
| Enterprise Features | **100%** | ✅ **Hotovo (API Keys + Webhooks + ERP + Analytics)** |

---

## 🎯 Fáza 5: Dokončenie Authentication & Monetization (Frontend) ✅ DOKONČENÉ

**Priorita:** 🔴 VYSOKÁ  
**Časový odhad:** 1-2 týždne  
**Status:** ✅ Backend 100%, Frontend 100% - DOKONČENÉ

### 5.1 Frontend Authentication Pages

#### Blueprint: Login Page
**Súbor:** `frontend/src/pages/Login.jsx`

```jsx
// Komponenty potrebné:
- LoginForm (email, password)
- "Forgot password?" link
- "Don't have account? Register" link
- Error handling (invalid credentials)
- Loading state
- Redirect po úspešnom login

// API endpoint:
POST /api/auth/login
Body: { email, password }
Response: { access_token, token_type, user }

// State management:
- AuthContext (React Context)
- localStorage pre token
- Redirect na /dashboard po login
```

#### Blueprint: Register Page
**Súbor:** `frontend/src/pages/Register.jsx`

```jsx
// Komponenty potrebné:
- RegisterForm (email, password, full_name, confirm_password)
- Email validation
- Password strength indicator
- Terms & Conditions checkbox
- Error handling (email exists, weak password)
- Success message + auto redirect to login

// API endpoint:
POST /api/auth/register
Body: { email, password, full_name }
Response: { user_id, email, message }

// Validácia:
- Email format
- Password min 8 chars
- Password match
```

#### Blueprint: User Dashboard
**Súbor:** `frontend/src/pages/Dashboard.jsx`

```jsx
// Sekcie:
1. User Profile Card
   - Email, Full Name
   - Current Tier (Free/Pro/Enterprise)
   - Subscription status
   - Upgrade button (ak Free)

2. Search History
   - Zoznam posledných vyhľadávaní
   - Filtrovanie podľa dátumu
   - Export histórie

3. Favorite Companies
   - Zoznam obľúbených firiem
   - Quick search
   - Remove favorite

4. Usage Statistics
   - Searches today/month
   - Remaining searches (podľa tieru)
   - Graph nodes limit

// API endpoints:
GET /api/auth/me
GET /api/search/history
GET /api/user/favorites
GET /api/auth/tier/limits
```

### 5.2 Protected Routes & Auth Context

#### Blueprint: AuthContext
**Súbor:** `frontend/src/contexts/AuthContext.jsx`

```jsx
// Context API:
- user: { id, email, full_name, tier }
- token: string
- isAuthenticated: boolean
- login(email, password)
- logout()
- register(email, password, full_name)
- refreshUser()

// localStorage:
- access_token
- user_data

// Auto-refresh token ak expirovaný
```

#### Blueprint: ProtectedRoute Component
**Súbor:** `frontend/src/components/ProtectedRoute.jsx`

```jsx
// Funkcionalita:
- Check authentication
- Redirect to /login ak nie je authenticated
- Check tier permissions (pre premium features)
- Loading state počas auth check

// Použitie:
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>

<ProtectedRoute requiredTier="pro">
  <AdvancedFeatures />
</ProtectedRoute>
```

### 5.3 Stripe Integration (Frontend)

#### Blueprint: Payment Checkout Flow
**Súbor:** `frontend/src/pages/PaymentCheckout.jsx`

```jsx
// Komponenty:
1. Tier Selection
   - Free (current)
   - Pro ($19.99/month) - Upgrade button
   - Enterprise ($99.99/month) - Upgrade button

2. Stripe Checkout
   - Redirect to Stripe Checkout Session
   - Success callback
   - Cancel callback

3. Subscription Management
   - Current subscription status
   - Cancel subscription button
   - Update payment method

// API endpoints:
POST /api/payment/checkout (tier)
GET /api/payment/subscription
POST /api/payment/cancel

// Stripe integration:
- Stripe Checkout Session
- Webhook handling (backend)
```

#### Blueprint: Payment Success/Cancel Pages
**Súbory:** 
- `frontend/src/pages/PaymentSuccess.jsx`
- `frontend/src/pages/PaymentCancel.jsx`

```jsx
// PaymentSuccess:
- Thank you message
- Subscription details
- Redirect to dashboard after 3s

// PaymentCancel:
- Cancel message
- "Try again" button
- Back to dashboard link
```

### 5.4 Rate Limiting UI

#### Blueprint: Rate Limit Indicator
**Súbor:** `frontend/src/components/RateLimitIndicator.jsx`

```jsx
// Zobrazenie:
- Progress bar (searches used / searches limit)
- Text: "5 / 10 searches today"
- Warning ak blízko limitu
- Upgrade prompt ak limit dosiahnutý

// API endpoint:
GET /api/auth/tier/limits
Response: { searches_per_day, searches_used, searches_per_month, ... }
```

---

## 🚀 Fáza 6: Enterprise Features ✅ DOKONČENÉ

**Priorita:** 🟡 STREDNÁ  
**Časový odhad:** 2-3 týždne  
**Status:** ✅ DOKONČENÉ (API Keys + Webhooks)

### 6.1 API Keys Management

#### Blueprint: API Keys Dashboard
**Súbor:** `frontend/src/pages/ApiKeys.jsx`

```jsx
// Funkcionalita:
1. Generate API Key
   - Name (description)
   - Expiration date (optional)
   - Permissions (read, write)
   - Generate button

2. API Keys List
   - Name, Created date, Last used
   - Active/Revoked status
   - Revoke button
   - Copy to clipboard

3. API Documentation
   - Endpoints list
   - Request/Response examples
   - Rate limits
   - Authentication (Bearer token)

// Backend endpoints:
POST /api/enterprise/keys (generate)
GET /api/enterprise/keys (list)
DELETE /api/enterprise/keys/{key_id} (revoke)
GET /api/enterprise/usage/{key_id} (usage stats)
```

#### Blueprint: API Authentication Middleware
**Súbor:** `backend/middleware/api_auth.py`

```python
# Funkcionalita:
- API key validation
- Rate limiting per API key
- Usage tracking
- IP whitelisting (optional)

# Database:
- api_keys table
  - id, user_id, key_hash, name, created_at, expires_at
  - last_used_at, usage_count, is_active
```

### 6.2 Webhooks

#### Blueprint: Webhooks Management
**Súbor:** `frontend/src/pages/Webhooks.jsx`

```jsx
// Funkcionalita:
1. Create Webhook
   - URL endpoint
   - Events (company_updated, new_risk_score, ...)
   - Secret key
   - Active/Inactive toggle

2. Webhooks List
   - URL, Events, Status
   - Last delivery status
   - Retry button
   - Delete button

3. Webhook Logs
   - Delivery history
   - Request/Response
   - Status codes
   - Error messages

// Backend endpoints:
POST /api/enterprise/webhooks
GET /api/enterprise/webhooks
PUT /api/enterprise/webhooks/{id}
DELETE /api/enterprise/webhooks/{id}
GET /api/enterprise/webhooks/{id}/logs
```

#### Blueprint: Webhook Delivery System
**Súbor:** `backend/services/webhook_service.py`

```python
# Funkcionalita:
- Event detection (company updates, risk changes)
- Webhook delivery (async, retry logic)
- Signature generation (HMAC)
- Delivery logging
- Retry mechanism (exponential backoff)

# Events:
- company.created
- company.updated
- risk_score.changed
- subscription.activated
- subscription.cancelled
```

### 6.3 ERP Integrations

#### Blueprint: ERP Integration Hub
**Súbor:** `frontend/src/pages/ErpIntegrations.jsx`

```jsx
// Podporované ERP:
1. SAP
   - Connection setup
   - Field mapping
   - Sync schedule

2. Pohoda (SK)
   - API credentials
   - Company sync
   - Invoice integration

3. Money S3 (CZ)
   - Connection setup
   - Data sync

// Komponenty:
- Connection wizard
- Field mapping UI
- Sync status
- Error handling
- Logs viewer

// Backend endpoints:
POST /api/enterprise/erp/connect
GET /api/enterprise/erp/status
POST /api/enterprise/erp/sync
GET /api/enterprise/erp/logs
```

#### Blueprint: ERP Connectors
**Súbory:**
- `backend/services/erp/sap_connector.py`
- `backend/services/erp/pohoda_connector.py`
- `backend/services/erp/money_s3_connector.py`

```python
# Každý connector:
- Authentication
- Data fetching
- Data transformation
- Error handling
- Rate limiting
```

### 6.4 Advanced Analytics ✅ DOKONČENÉ

#### Blueprint: Analytics Dashboard
**Súbor:** `frontend/src/pages/Analytics.jsx` ✅ IMPLEMENTOVANÉ

```jsx
// Grafy a metriky:
1. Search Trends ✅
   - Searches per day/week/month
   - Peak hours
   - Popular countries

2. Risk Distribution ✅
   - Risk score distribution
   - High-risk companies count
   - Risk trends over time

3. User Activity ✅
   - Active users
   - Retention rate
   - Feature usage

4. API Usage ✅
   - API calls per day
   - Most used endpoints
   - Error rate

// Charts library: Recharts ✅ IMPLEMENTOVANÉ
// API endpoints: ✅ IMPLEMENTOVANÉ
GET /api/analytics/dashboard
GET /api/analytics/search-trends
GET /api/analytics/risk-distribution
GET /api/analytics/user-activity
GET /api/analytics/api-usage
```

---

## 🔧 Fáza 7: Vylepšenia & Polish

**Priorita:** 🟢 NÍZKA  
**Časový odhad:** 1-2 týždne

### 7.1 Frontend Vylepšenia

- [ ] ESLint konfigurácia (migrácia na ESLint 9)
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Internationalization (i18n) - SK, CZ, PL, HU, EN
- [x] Advanced search filters (country, risk score) ✅ DOKONČENÉ
- [ ] Export improvements (Excel, CSV s formátovaním)
- [ ] Graph improvements (3D view, custom layouts)

### 7.2 Backend Vylepšenia

- [ ] Redis cache (nahradiť in-memory)
- [ ] Background jobs (Celery alebo RQ)
- [ ] Email notifications (SendGrid/SES)
- [ ] Advanced search (Elasticsearch)
- [ ] Graph database (Neo4j pre komplexné vzťahy)

### 7.3 DevOps & Infrastructure

- [ ] Docker Compose setup
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Kubernetes deployment
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Logging (ELK stack alebo Loki)

---

## 📋 Implementačný Plán

### Sprint 1 (Týždeň 1-2): Authentication Frontend
**Úlohy:**
1. ✅ Vytvoriť AuthContext
2. ✅ Implementovať Login page
3. ✅ Implementovať Register page
4. ✅ Implementovať ProtectedRoute
5. ✅ Integrovať s backend auth API
6. ✅ Testy pre auth komponenty

**Deliverables:**
- Funkčný login/register flow
- Protected routes
- User session management

### Sprint 2 (Týždeň 3-4): Stripe Integration Frontend
**Úlohy:**
1. ✅ Implementovať PaymentCheckout page
2. ✅ Stripe Checkout Session integration
3. ✅ Payment Success/Cancel pages
4. ✅ Subscription management UI
5. ✅ Rate limit indicator
6. ✅ User Dashboard

**Deliverables:**
- Kompletný payment flow
- Subscription management
- User dashboard

### Sprint 3 (Týždeň 5-7): Enterprise Features - API Keys
**Úlohy:**
1. ✅ API Keys backend (endpoints, middleware)
2. ✅ API Keys frontend (dashboard, management)
3. ✅ API Documentation page
4. ✅ Usage tracking
5. ✅ Tests

**Deliverables:**
- API Keys management
- API Documentation
- Usage tracking

### Sprint 4 (Týždeň 8-10): Enterprise Features - Webhooks
**Úlohy:**
1. ✅ Webhooks backend (delivery system)
2. ✅ Webhooks frontend (management, logs)
3. ✅ Event system
4. ✅ Retry mechanism
5. ✅ Tests

**Deliverables:**
- Webhooks management
- Event delivery system
- Webhook logs

### Sprint 5 (Týždeň 11-13): Enterprise Features - ERP Integrations
**Úlohy:**
1. ✅ SAP connector (basic)
2. ✅ Pohoda connector
3. ✅ Money S3 connector
4. ✅ ERP Integration Hub UI
5. ✅ Sync mechanism
6. ✅ Tests

**Deliverables:**
- ERP connectors
- Integration management UI
- Data sync

---

## 🎯 Prioritizácia & Odporúčania

### Okamžite (Týždeň 1-2)
1. **Authentication Frontend** - Kritické pre monetizáciu
2. **Stripe Integration Frontend** - Potrebné pre príjmy

### Krátkodobo (Týždeň 3-6)
3. **User Dashboard** - Zlepšuje UX
4. **API Keys Management** - Enterprise feature #1

### Strednodobo (Týždeň 7-13)
5. **Webhooks** - Enterprise feature #2
6. **ERP Integrations** - Enterprise feature #3

### Dlhodobo (Mesiac 4+)
7. **Advanced Analytics** - Business intelligence
8. **DevOps & Infrastructure** - Škálovanie

---

## 📊 Metriky Úspechu

### Authentication & Monetization
- [x] 100% frontend coverage pre auth flow ✅ DOKONČENÉ
- [x] Stripe checkout funguje end-to-end ✅ DOKONČENÉ
- [x] User dashboard kompletný ✅ DOKONČENÉ
- [x] Rate limiting UI implementovaný ✅ DOKONČENÉ

### Enterprise Features
- [x] API Keys management funkčný ✅ DOKONČENÉ
- [x] Webhooks delivery system funkčný ✅ DOKONČENÉ
- [x] ERP connectors (SAP, Pohoda, Money S3) ✅ DOKONČENÉ
- [x] Analytics dashboard základný ✅ DOKONČENÉ

### Kvalita
- [x] Test coverage 85% (cieľ 90%) ⚠️ Vylepšuje sa
- [x] Všetky lintery OK ✅ DOKONČENÉ
- [x] Dokumentácia aktuálna ✅ DOKONČENÉ
- [x] Performance metrics OK ✅ DOKONČENÉ

---

## 🔗 Súvisiace Dokumenty

- [PROJECT_STATUS.md](./PROJECT_STATUS.md) - Aktuálny stav projektu
- [NEXT_STEPS.md](./NEXT_STEPS.md) - Pôvodný plán
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architektúra systému
- [AUTH_IMPLEMENTATION.md](./AUTH_IMPLEMENTATION.md) - Auth backend dokumentácia
- [STRIPE_INTEGRATION.md](./STRIPE_INTEGRATION.md) - Stripe backend dokumentácia

---

**Poznámka:** Táto roadmapa je živý dokument a bude aktualizovaná podľa pokroku a zmien v prioritách.

