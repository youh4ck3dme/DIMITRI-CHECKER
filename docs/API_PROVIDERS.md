# 🔌 API Providers - Dokumentácia

**Dátum:** December 20, 2024  
**Verzia:** 1.0

---

## 📋 Prehľad

V4-Finstat Projekt používa hybridný model pre získavanie dát o firmách:
- **Cache → DB → Live Scraping**
- **Obohatenie dát** (DIČ/IČ DPH, geolokácia, finančné ukazovatele)
- **Full-text search** v lokálnej DB

---

## 🏗️ Architektúra

### Hybridný Model

```
┌─────────┐
│ Request │
└────┬────┘
     │
     ▼
┌─────────┐  Cache Miss
│  Cache  │ ──────────┐
└─────────┘           │
     │                 │
     │ Cache Hit       │
     ▼                 ▼
┌─────────┐      ┌─────────┐
│ Return  │      │   DB   │
└─────────┘      └────┬───┘
                       │ DB Miss
                       ▼
                  ┌─────────┐
                  │ Scraping│
                  └────┬────┘
                       │
                       ▼
                  ┌─────────┐
                  │  Save   │
                  └─────────┘
```

---

## 🇸🇰 Slovensko - Providers

### 1. OrsrProvider

**Súbor:** `backend/services/sk_orsr_provider.py`

**Funkcia:** Live scraping z ORSR.sk (Obchodný register SR)

**Metódy:**
- `lookup_by_ico(ico: str, force_refresh: bool = False) -> Optional[Dict]`

**Vrstvy:**
1. **Cache** (12 hodín TTL)
2. **DB** (auto-refresh po 7 dňoch)
3. **Live Scraping** (ORSR.sk)

**Príklad použitia:**
```python
from services.sk_orsr_provider import get_orsr_provider

provider = get_orsr_provider()
data = provider.lookup_by_ico("52374220")

# Výstup:
# {
#   "ico": "52374220",
#   "name": "Tavira, s. r. o.",
#   "legal_form": "Spoločnosť s ručením obmedzeným",
#   "address": "Drieňová 1J, Bratislava - mestská časť Ružinov 821 01",
#   "postal_code": "82101",
#   "city": "Bratislava",
#   "region": "Bratislavský",
#   "district": "Bratislava II",
#   "executives": ["Dimitri Cohen"],
#   "founded": "2019-08-08",
#   "status": "Aktívna",
#   "dic": "SK202374220",  # Z ZRSR
#   "ic_dph": "202374220"  # Z ZRSR
# }
```

**API Endpoint:**
```
GET /api/search?q=52374220
```

---

### 2. ZrsrProvider

**Súbor:** `backend/services/sk_zrsr_provider.py`

**Funkcia:** Obohatenie o DIČ/IČ DPH z Živnostenského registra SR

**Metódy:**
- `lookup_dic_ic_dph(ico: str, company_name: Optional[str] = None) -> Optional[Dict[str, str]]`

**Volá sa:** Automaticky z OrsrProvider ak chýba DIČ/IČ DPH

**Príklad použitia:**
```python
from services.sk_zrsr_provider import get_zrsr_provider

provider = get_zrsr_provider()
data = provider.lookup_dic_ic_dph("52374220", "Tavira, s. r. o.")

# Výstup:
# {
#   "dic": "SK202374220",
#   "ic_dph": "202374220"
# }
```

**Status:** ⚠️ Základná implementácia - potrebuje skutočný API endpoint alebo scraping flow

---

### 3. RuzProvider

**Súbor:** `backend/services/sk_ruz_provider.py`

**Funkcia:** Účtovné závierky a finančné ukazovatele

**Metódy:**
- `lookup_financial_statements(ico: str, year: Optional[int] = None) -> Optional[List[Dict]]`
- `get_financial_indicators(ico: str, year: Optional[int] = None) -> Optional[Dict]`

**Príklad použitia:**
```python
from services.sk_ruz_provider import get_ruz_provider

provider = get_ruz_provider()
statements = provider.lookup_financial_statements("52374220", year=2023)

# Výstup:
# [
#   {
#     "year": 2023,
#     "revenue": 150000.00,
#     "profit": 5000.00,
#     "assets": 200000.00,
#     "liabilities": 50000.00,
#     "equity": 150000.00
#   }
# ]
```

**Status:** ⚠️ Základná implementácia - potrebuje skutočný API endpoint

---

### 4. RegionResolver

**Súbor:** `backend/services/sk_region_resolver.py`

**Funkcia:** Geolokácia z PSČ (Kraj, Okres)

**Metódy:**
- `resolve_region(postal_code: str) -> Optional[Dict[str, str]]`
- `enrich_address_with_region(address: str, postal_code: Optional[str] = None) -> Dict[str, Optional[str]]`

**Dáta:** Načítava z `backend/data/postal_codes_sk.csv`

**Príklad použitia:**
```python
from services.sk_region_resolver import resolve_region, enrich_address_with_region

# Jednoduché vyriešenie
region = resolve_region("82101")
# {"kraj": "Bratislavský", "okres": "Bratislava II"}

# Obohatenie adresy
enriched = enrich_address_with_region(
    "Drieňová 1J, Bratislava 821 01",
    postal_code="82101"
)
# {
#   "address": "Drieňová 1J, Bratislava 821 01",
#   "postal_code": "82101",
#   "city": "Bratislava",
#   "region": "Bratislavský",
#   "district": "Bratislava II"
# }
```

**Status:** ✅ Funkčné - potrebuje kompletný CSV so všetkými PSČ (~1 800 položiek)

---

## 🔍 Vyhľadávanie

### Search by Name

**Súbor:** `backend/services/search_by_name.py`

**Funkcia:** Full-text search v lokálnej DB (nie live scraping)

**Metódy:**
- `search_by_name(query: str, country: Optional[str] = None, limit: int = 20) -> List[Dict]`
- `search_by_address(query: str, country: Optional[str] = None, limit: int = 20) -> List[Dict]`

**Technológie:**
- PostgreSQL full-text search (pg_trgm)
- Fallback na ILIKE

**Príklad použitia:**
```python
from services.search_by_name import search_by_name

# Vyhľadávanie podľa názvu
companies = search_by_name("Tavira", country="SK", limit=10)

# Výstup:
# [
#   {
#     "identifier": "52374220",
#     "country": "SK",
#     "name": "Tavira, s. r. o.",
#     "legal_form": "Spoločnosť s ručením obmedzeným",
#     "address": "Drieňová 1J, Bratislava 821 01",
#     "risk_score": 2.0,
#     "last_synced_at": "2024-12-20T10:00:00"
#   }
# ]
```

**API Endpoint:**
```
GET /api/search?q=Tavira
```

**Poznámka:** Vyhľadá len firmy, ktoré už boli "objavené" cez IČO a uložené do DB.

---

## 📊 API Endpoints

### Search Company

```
GET /api/search?q={query}
```

**Parametre:**
- `q` (required): IČO alebo názov firmy

**Príklady:**
```bash
# Podľa IČO (live scraping)
curl "http://localhost:8000/api/search?q=52374220"

# Podľa názvu (lokálna DB)
curl "http://localhost:8000/api/search?q=Tavira"
```

**Response:**
```json
{
  "nodes": [
    {
      "id": "sk_52374220",
      "label": "Tavira, s. r. o.",
      "type": "company",
      "country": "SK",
      "risk_score": 2,
      "details": "IČO: 52374220, Status: Aktívna, Forma: Spoločnosť s ručením obmedzeným",
      "ico": "52374220"
    }
  ],
  "edges": []
}
```

---

## 🔧 Konfigurácia

### PostgreSQL Full-Text Search

**Migration:** `backend/migrations/add_fulltext_search.py`

**Vykonanie:**
```bash
cd backend
source venv/bin/activate
python migrations/add_fulltext_search.py
```

**Vytvorí:**
- `pg_trgm` rozšírenie
- GIN indexy pre full-text search
- Trigram indexy pre podobnosť

---

## 📝 TODO

### ZRSR Provider
- [ ] Skutočný API endpoint alebo scraping flow
- [ ] Príklady request/response
- [ ] Testy

### RUZ Provider
- [ ] Skutočný API endpoint
- [ ] JSON štruktúra odpovede
- [ ] HTML scraping fallback
- [ ] Testy

### RegionResolver
- [ ] Kompletný CSV so všetkými PSČ (~1 800 položiek)
- [ ] Automatické načítanie z CSV

### Full-Text Search
- [ ] PostgreSQL GIN indexy (hotové)
- [ ] Testy performance
- [ ] Optimalizácia dotazov

---

## 📚 Referencie

- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [pg_trgm Extension](https://www.postgresql.org/docs/current/pgtrgm.html)
- [ORSR.sk](https://www.orsr.sk)
- [ZRSR.sk](https://www.zrsr.sk)
- [RUZ.sk](https://www.registeruz.sk)

---

*Posledná aktualizácia: December 20, 2024*

