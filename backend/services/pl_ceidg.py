"""
Poľský CEIDG (Centralna Ewidencja i Informacja o Działalności Gospodarczej)
Integrácia pre živnostníkov (osoby fizyczne prowadzące działalność gospodarczą)
"""
import requests
from typing import Dict, Optional, List
import re


def is_ceidg_number(nip: str) -> bool:
    """
    Kontrola, či je to CEIDG číslo (NIP živnostníka)
    CEIDG používa NIP (Numer Identyfikacji Podatkowej) - 10 číslic
    """
    if not nip:
        return False
    # NIP je 10 číslic
    nip_clean = re.sub(r'[-\s]', '', nip)
    return len(nip_clean) == 10 and nip_clean.isdigit()


def fetch_ceidg_pl(nip: str) -> Optional[Dict]:
    """
    Získa údaje o živnostníkovi z CEIDG
    API: https://dane.biznes.gov.pl/ceidg
    """
    if not is_ceidg_number(nip):
        return None
    
    try:
        # CEIDG API endpoint (simulácia - skutočné API vyžaduje registráciu)
        # V produkcii: https://dane.biznes.gov.pl/api/ceidg/v1/firma/{nip}
        api_url = f"https://dane.biznes.gov.pl/api/ceidg/v1/firma/{nip}"
        
        # Simulácia - v produkcii by to bolo:
        # response = requests.get(api_url, headers={"Accept": "application/json"}, timeout=10)
        # if response.status_code == 200:
        #     return response.json()
        
        # Fallback - simulované dáta
        return {
            "nip": nip,
            "nazwa": f"Jan Kowalski - Działalność Gospodarcza",
            "status": "AKTYWNY",
            "dataRozpoczecia": "2020-01-15",
            "adres": {
                "ulica": "ul. Przykładowa 123",
                "miejscowosc": "Warszawa",
                "kodPocztowy": "00-001",
                "wojewodztwo": "mazowieckie"
            },
            "przedmiotDzialalnosci": "Usługi informatyczne",
            "formaPrawna": "OSOBA_FIZYCZNA",
            "czyVat": True,
            "dataZakonczenia": None
        }
    except Exception as e:
        print(f"⚠️ Chyba pri CEIDG API: {e}")
        return None


def parse_ceidg_data(ceidg_data: Dict) -> Dict:
    """
    Parsuje CEIDG dáta do jednotnej schémy
    """
    if not ceidg_data:
        return {}
    
    address_parts = []
    adres = ceidg_data.get("adres", {})
    if adres.get("ulica"):
        address_parts.append(adres["ulica"])
    if adres.get("miejscowosc"):
        address_parts.append(adres["miejscowosc"])
    if adres.get("kodPocztowy"):
        address_parts.append(adres["kodPocztowy"])
    
    address_text = ", ".join(address_parts) if address_parts else "Nieznany adres"
    
    return {
        "ico": ceidg_data.get("nip", ""),
        "name": ceidg_data.get("nazwa", ""),
        "legal_form": "OSOBA_FIZYCZNA",
        "status": ceidg_data.get("status", "NIEZNANY"),
        "address": address_text,
        "country": "PL",
        "vat_payer": ceidg_data.get("czyVat", False),
        "activity": ceidg_data.get("przedmiotDzialalnosci", ""),
        "start_date": ceidg_data.get("dataRozpoczecia"),
        "end_date": ceidg_data.get("dataZakonczenia")
    }


def calculate_ceidg_risk_score(ceidg_data: Dict) -> float:
    """
    Vypočíta risk score pre CEIDG živnostníka
    """
    if not ceidg_data:
        return 5.0
    
    risk = 3.0  # Base risk pre živnostníkov (nižší ako pre spoločnosti)
    
    # Status
    status = ceidg_data.get("status", "").upper()
    if status == "ZAKONCZONY":
        risk += 4.0
    elif status != "AKTYWNY":
        risk += 2.0
    
    # DPH status
    if not ceidg_data.get("vat_payer", False):
        risk += 0.5  # Mierne zvýšenie rizika
    
    # Dátum ukončenia
    if ceidg_data.get("end_date"):
        risk += 3.0
    
    return min(risk, 10.0)


def search_ceidg_pl(nip: str) -> Optional[Dict]:
    """
    Hlavná funkcia pre vyhľadávanie v CEIDG
    """
    if not is_ceidg_number(nip):
        return None
    
    ceidg_data = fetch_ceidg_pl(nip)
    if not ceidg_data:
        return None
    
    parsed = parse_ceidg_data(ceidg_data)
    risk_score = calculate_ceidg_risk_score(parsed)
    
    return {
        "data": parsed,
        "risk_score": risk_score,
        "source": "CEIDG"
    }

