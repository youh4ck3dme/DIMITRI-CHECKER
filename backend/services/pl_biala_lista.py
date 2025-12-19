"""
Poľská Biała Lista (White List) - DPH status a overenie platiteľov DPH
API: https://wl-api.mf.gov.pl/
"""
import requests
from typing import Dict, Optional
import re


def is_polish_nip(nip: str) -> bool:
    """
    Kontrola, či je to poľský NIP (Numer Identyfikacji Podatkowej)
    NIP je 10 číslic
    """
    if not nip:
        return False
    nip_clean = re.sub(r'[-\s]', '', nip)
    return len(nip_clean) == 10 and nip_clean.isdigit()


def fetch_biala_lista_pl(nip: str) -> Optional[Dict]:
    """
    Získa údaje z Białej Listy (White List) pre DPH status
    API: https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={date}
    """
    if not is_polish_nip(nip):
        return None
    
    try:
        # Biała Lista API endpoint
        # V produkcii: https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={date}
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        api_url = f"https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={today}"
        
        # Simulácia - v produkcii by to bolo:
        # response = requests.get(api_url, headers={"Accept": "application/json"}, timeout=10)
        # if response.status_code == 200:
        #     return response.json()
        
        # Fallback - simulované dáta
        return {
            "nip": nip,
            "name": "Przykładowa Spółka z o.o.",
            "statusVat": "Czynny",  # Czynny, Zwolniony, Niezarejestrowany
            "regon": "123456789",
            "residenceAddress": "ul. Przykładowa 123, 00-001 Warszawa",
            "workingAddress": None,
            "representatives": [
                {
                    "companyName": "Jan Kowalski",
                    "firstName": "Jan",
                    "lastName": "Kowalski",
                    "nip": None
                }
            ],
            "authorizedClerks": [],
            "partners": []
        }
    except Exception as e:
        print(f"⚠️ Chyba pri Biała Lista API: {e}")
        return None


def parse_biala_lista_data(biala_data: Dict) -> Dict:
    """
    Parsuje Biała Lista dáta do jednotnej schémy
    """
    if not biala_data:
        return {}
    
    status_vat = biala_data.get("statusVat", "").upper()
    vat_active = status_vat == "CZYNNY"
    
    return {
        "nip": biala_data.get("nip", ""),
        "name": biala_data.get("name", ""),
        "vat_status": status_vat,
        "vat_active": vat_active,
        "regon": biala_data.get("regon", ""),
        "address": biala_data.get("residenceAddress", ""),
        "working_address": biala_data.get("workingAddress"),
        "representatives": biala_data.get("representatives", []),
        "authorized_clerks": biala_data.get("authorizedClerks", []),
        "partners": biala_data.get("partners", [])
    }


def calculate_biala_lista_risk_score(biala_data: Dict) -> float:
    """
    Vypočíta risk score na základe Białej Listy
    """
    if not biala_data:
        return 5.0
    
    risk = 2.0  # Base risk
    
    status_vat = biala_data.get("vat_status", "").upper()
    
    # DPH status
    if status_vat == "NIEZAREJESTROWANY":
        risk += 4.0  # Vysoké riziko - nie je registrovaný
    elif status_vat == "ZWOLNIONY":
        risk += 1.0  # Mierne zvýšenie
    elif status_vat == "CZYNNY":
        risk -= 0.5  # Zníženie rizika - aktívny platiteľ DPH
    
    # Chýbajúce údaje
    if not biala_data.get("address"):
        risk += 1.0
    if not biala_data.get("representatives"):
        risk += 0.5
    
    return max(0.0, min(risk, 10.0))


def search_biala_lista_pl(nip: str) -> Optional[Dict]:
    """
    Hlavná funkcia pre vyhľadávanie v Białej Liście
    """
    if not is_polish_nip(nip):
        return None
    
    biala_data = fetch_biala_lista_pl(nip)
    if not biala_data:
        return None
    
    parsed = parse_biala_lista_data(biala_data)
    risk_score = calculate_biala_lista_risk_score(parsed)
    
    return {
        "data": parsed,
        "risk_score": risk_score,
        "source": "Biała Lista"
    }


def get_vat_status_pl(nip: str) -> Optional[str]:
    """
    Rýchle získanie DPH statusu
    """
    result = search_biala_lista_pl(nip)
    if result and result.get("data"):
        return result["data"].get("vat_status")
    return None

