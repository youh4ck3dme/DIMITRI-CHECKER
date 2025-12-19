# 🚀 ILUMINATE SYSTEM - Server Status

## ✅ Servery sú spustené a funkčné!

### 📊 Backend API (FastAPI)
- **URL:** http://localhost:8000
- **Status:** ✅ Beží
- **API Dokumentácia:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc
- **Verzia:** 1.1

**Dostupné endpointy:**
- `GET /` - Root endpoint (status)
- `GET /api/search?q={query}` - Vyhľadávanie firiem

**Príklad požiadavky:**
```bash
curl "http://localhost:8000/api/search?q=Agrofert"
```

**Odpoveď:**
```json
{
  "nodes": [
    {
      "id": "cz_24188581",
      "label": "Nadace AGROFERT",
      "type": "company",
      "country": "CZ",
      "risk_score": 2,
      "details": "IČO: 24188581"
    },
    ...
  ],
  "edges": [
    {
      "source": "cz_24188581",
      "target": "addr_24188581",
      "type": "LOCATED_AT"
    },
    ...
  ]
}
```

### 🎨 Frontend (React + Vite)
- **URL:** http://localhost:5173
- **Status:** ✅ Beží
- **Build Tool:** Vite 5.4.21
- **Framework:** React 18.3.1

**Dostupné stránky:**
- `/` - Hlavná stránka s vyhľadávaním
- `/vop` - Všeobecné obchodné podmienky
- `/privacy` - Zásady ochrany osobných údajov
- `/disclaimer` - Vyhlásenie o zodpovednosti
- `/cookies` - Cookie Policy
- `/dpa` - Data Processing Agreement

## 🧪 Testovanie

### Backend API Test
```bash
# Status check
curl http://localhost:8000/

# Vyhľadávanie
curl "http://localhost:8000/api/search?q=Agrofert"
```

### Frontend Test
1. Otvorte prehliadač: http://localhost:5173
2. Zadajte názov firmy (napr. "Agrofert")
3. Kliknite na "Analyzovať"
4. Graf sa zobrazí s uzlami a hranami

## 📝 Logy

Backend logy: `/tmp/cbn_backend.log`

## 🛑 Zastavenie serverov

```bash
# Zastaviť backend
pkill -f "python main.py"

# Zastaviť frontend
pkill -f "vite"
```

## 🔄 Reštart

**Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

