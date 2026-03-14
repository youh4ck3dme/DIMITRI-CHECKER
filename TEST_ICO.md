# 🧪 Testovanie s Reálnym IČO - V4-Finstat Projekt

## 📍 Kde môžeš napísať IČO?

### **SPÔSOB 1: Frontend (najjednoduchšie)** ⭐ ODORÚČANÉ

1. **Spusti frontend server:**
```bash
cd frontend
npm run dev
```

2. **Otvori prehliadač:**
```
http://localhost:5173
```

3. **Zadaj IČO do vyhľadávacieho poľa** a klikni "Overiť subjekt"

---

### **SPÔSOB 2: API priamo (curl)**

```bash
# České IČO
curl "http://localhost:8000/api/search?q=27074358"

# Slovenské IČO
curl "http://localhost:8000/api/search?q=31333501"

# Poľské KRS
curl "http://localhost:8000/api/search?q=0000123456"

# Maďarské adószám
curl "http://localhost:8000/api/search?q=12345678"
```

---

### **SPÔSOB 3: API dokumentácia (Swagger UI)** ⭐ NAJLEPŠIE PRE TESTOVANIE

1. **Otvori Swagger UI:**
```
http://localhost:8000/docs
```

2. **Nájsť endpoint:** `GET /api/search`
3. **Kliknúť "Try it out"**
4. **Zadať IČO do parametra `q`**
5. **Kliknúť "Execute"**

---

## 🔍 Testovacie IČO (Reálne)

### 🇨🇿 **Česká republika (ARES)**
```
27074358 - Agrofert, a.s. ✅ Už testované
47114983 - ČEZ, a.s.
00001234 - Neplatné (test error handling)
```

### 🇸🇰 **Slovensko (RPO)**
```
31333501 - Agrofert Holding a.s.
36070961 - Slovnaft, a.s.
88888888 - Testovacie (fallback dáta)
```

### 🇵🇱 **Poľsko (KRS)**
```
0000123456 - Testovacie KRS (9-10 miest)
0000001234 - Testovacie KRS
```

### 🇭🇺 **Maďarsko (NAV)**
```
12345678 - Testovacie adószám (8 miest)
12345678901 - Testovacie adószám (11 miest)
```

---

## 🧪 Testovacie Scenáre

### **Scenár 1: Happy Path**
```bash
# Testovať každú krajinu s reálnym IČO
curl "http://localhost:8000/api/search?q=27074358"  # CZ
curl "http://localhost:8000/api/search?q=31333501"  # SK
curl "http://localhost:8000/api/search?q=0000123456"  # PL
curl "http://localhost:8000/api/search?q=12345678"  # HU
```

### **Scenár 2: Error Handling**
```bash
# Neplatné IČO
curl "http://localhost:8000/api/search?q=99999999"

# Prázdny query
curl "http://localhost:8000/api/search?q="
```

### **Scenár 3: S Filtrami**
```bash
# Filtrovanie podľa krajiny
curl "http://localhost:8000/api/search?q=27074358&country=CZ"

# Filtrovanie podľa risk skóre
curl "http://localhost:8000/api/search?q=27074358&min_risk_score=5&max_risk_score=10"
```

---

## 📊 Čo Overiť

1. ✅ **Správne dáta** - zobrazujú sa správne informácie o firme
2. ✅ **Graf** - graf je správne vykreslený s uzlami a hranami
3. ✅ **Risk score** - risk score je vypočítaný
4. ✅ **Cache** - druhé volanie je rýchlejšie (cache hit)
5. ✅ **Error handling** - neplatné IČO zobrazí správnu chybu
6. ✅ **Performance** - response time < 10s

---

## 🚀 Rýchly Start

**Najjednoduchší spôsob:**
1. Spusti backend: `cd backend && source venv/bin/activate && python main.py`
2. Spusti frontend: `cd frontend && npm run dev`
3. Otvor: http://localhost:5173
4. Zadaj IČO: `27074358` (české) alebo `31333501` (slovenské)
5. Klikni "Overiť subjekt"

---

*Posledná aktualizácia: December 20, 2024*

