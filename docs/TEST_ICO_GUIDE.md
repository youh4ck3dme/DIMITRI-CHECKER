# 🧪 Testovacie IČO 88888888 - Simulované Vyhodnotenie

## ✅ Implementované

Testovacie slovenské IČO **88888888** (8-miestne podľa slovenského zákona) je plne funkčné a vracia komplexnú simulovanú štruktúru.

## 📊 Simulované Dáta

### Hlavná Firma
- **IČO:** 88888888
- **Názov:** Testovacia Spoločnosť s.r.o.
- **Krajina:** SK (Slovensko)
- **Risk Score:** 7/10 (Vysoké riziko)
- **Status:** Aktívna, DPH: Áno

### Štruktúra Grafu

**Uzly (9 celkom):**
1. **3 Firmy:**
   - Testovacia Spoločnosť s.r.o. (SK) - Risk: 7
   - Dcérska Firma CZ s.r.o. (CZ) - Risk: 6
   - Sesterská Spoločnosť s.r.o. (SK) - Risk: 8 (Likvidácia)

2. **3 Osoby:**
   - Ján Novák (Konateľ, 15+ firiem) - Risk: 5
   - Peter Horváth (Spoločník, 8% podiel) - Risk: 4
   - Mária Kováčová (Konateľ v 12+ firmách - White Horse Detector) - Risk: 6

3. **2 Adresy:**
   - Bratislava, Hlavná 1 (Virtual Seat - 52 firiem) - Risk: 3
   - Košice, Mierová 5 - Risk: 0

4. **1 Dlh:**
   - Dlh Finančnej správe (25,000 EUR) - Risk: 9

**Vzťahy (9 celkom):**
- `LOCATED_AT` - Firma → Adresa
- `MANAGED_BY` - Firma → Osoba (Konateľ)
- `OWNED_BY` - Firma → Osoba/Spoločnosť (Vlastníctvo)
- `HAS_DEBT` - Firma → Dlh

## 🎯 Detekované Riziká

1. **Virtual Seat** - Adresa s 52+ firmami (Bratislava, Hlavná 1)
2. **White Horse Detector** - Osoba (Mária Kováčová) figuruje v 12+ firmách
3. **Likvidácia** - Dcérska spoločnosť v likvidácii
4. **Dlh** - Dlh 25,000 EUR Finančnej správe
5. **Cross-Border** - Vlastníctvo cez hranice (SK → CZ)

## 🧪 Ako Testovať

### 1. Cez API
```bash
curl "http://localhost:8000/api/search?q=88888888"
```

### 2. Cez Frontend
1. Otvorte http://localhost:5173
2. Zadajte do vyhľadávacieho poľa: **88888888**
3. Kliknite "Analyzovať"
4. Graf zobrazí kompletnú štruktúru s:
   - Modrými uzlami = Firmy
   - Zelenými uzlami = Osoby
   - Oranžovými uzlami = Adresy
   - Červenými uzlami = Dlhy
   - Šípkami = Vzťahy

## 📈 Risk Score Výpočet

- **7/10** - Hlavná firma (vysoké riziko kvôli virtual seat, dlhom, likvidovanej dcérskej spoločnosti)
- **8/10** - Sesterská spoločnosť (likvidácia + dlh)
- **9/10** - Dlh (najvyššie riziko)
- **6/10** - White Horse osoba (konateľ v 12+ firmách)
- **5/10** - Konateľ s 15+ firmami
- **3/10** - Virtual Seat adresa

## 🔍 Detekované Vzory

1. **Karuselová Štruktúra:**
   - SK → CZ → SK (cross-border vlastníctvo)
   
2. **White Horse Pattern:**
   - Mária Kováčová je konateľom v 12+ firmách
   
3. **Virtual Seat:**
   - 52 firiem na jednej adrese
   
4. **Likvidácia + Dlh:**
   - Dcérska spoločnosť v likvidácii s dlhom

## ✅ Výsledok

Testovacie IČO **88888888** úspešne simuluje komplexnú podnikateľskú štruktúru s:
- ✅ Cross-border vzťahmi (SK ↔ CZ)
- ✅ Rizikovými faktormi (virtual seat, dlhy, likvidácia)
- ✅ White Horse detekciou
- ✅ Kompletným grafom s 9 uzlami a 9 vzťahmi

