# 🔌 V4-Finstat Projekt - API Dokumentácia

## Prehľad
API je postavené na **FastAPI** (Python 3.13) a je navrhnuté pre vysoký výkon a bezpečnosť. Podporuje real-time vyhľadávanie v registroch V4 krajín, risk intelligence, exporty a enterprise funkcie.

## 🌐 Interaktívna Dokumentácia
Po spustení backend servera je dokumentácia dostupná na:
- **Swagger UI:** `http://localhost:8000/api/docs` (Interaktívne testovanie)
- **ReDoc:** `http://localhost:8000/api/redoc` (Čistá dokumentácia)

---

## 🔐 Autentifikácia
Väčšina endpointov vyžaduje JWT (Bearer) token alebo API Key.

### 1. JWT Token (OAuth2)
Používa sa pre frontend a bežných používateľov.
- **Header:** `Authorization: Bearer <your_token>`

### 2. Enterprise API Key
Používa sa pre B2B integrácie a server-to-server komunikáciu.
- **Header:** `X-API-Key: ilmn_xxxxxx`

---

## 🚀 Hlavné Endpointy

### 🔎 Vyhľadávanie (Search)
Získa dáta o firme a jej vzťahoch (grafové dáta).
- **Endpoint:** `GET /api/search`
- **Params:** `q` (IČO/Názov), `country` (SK, CZ, PL, HU)
- **Status:** 200 OK

### 🛡️ Risk Intelligence
Vygeneruje podrobný risk report pre daný subjekt.
- **Endpoint:** `GET /api/risk/report/{country}/{identifier}`
- **Status:** 200 OK

### 🎁 ERP Integrácie
Správa a synchronizácia dát s ERP systémami.
- **Endpoint:** `GET /api/erp/connections` (Zoznam prepojení)
- **Endpoint:** `POST /api/erp/sync` (Manuálna synchronizácia)

### 📊 Analytics
Metriky a štatistiky pre dashboard.
- **Endpoint:** `GET /api/analytics/dashboard`
- **Output:** Trendy, distribúcia rizika, využitie API.

---

## 📥 Exporty
Platforma podporuje generovanie reportov v rôznych formátoch.
- **Excel (XLSX):** `POST /api/export/excel`
- **Batch Excel:** `POST /api/export/batch-excel`
- **Supported Formats:** JSON, CSV, PDF, XLSX.

---

## ⚙️ Technické Vlastnosti
- **Circuit Breakers:** Automatické odpojenie nedostupných registrov (zabráni pádu appky).
- **Proxy Rotation:** Bypasovanie rate limitov štátnych registrov.
- **Caching (Redis):** Extrémne rýchle odpovede pre známe subjekty.
- **Event-Driven:** Podpora pre Webhooks pri zmene stavu subjektu.

---

## 🧪 Príklad requestu (Search)
```bash
curl -X GET "http://localhost:8000/api/search?q=88888888&country=SK" \
     -H "Authorization: Bearer <token>"
```

*Dokumentácia bola vygenerovaná pre verziu 5.0 (V4-Finstat Edition)*
