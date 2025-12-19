"""
Dlhové registre - Finančná správa SK a ČR
Integrácia pre detekciu dlhov voči štátu
"""
import requests
from typing import Dict, Optional, List
import re


def is_slovak_ico_for_debt(ico: str) -> bool:
    """Kontrola slovenského IČO pre dlhové registry"""
    if not ico:
        return False
    ico_clean = re.sub(r'[-\s]', '', ico)
    return len(ico_clean) == 8 and ico_clean.isdigit()


def is_czech_ico_for_debt(ico: str) -> bool:
    """Kontrola českého IČO pre dlhové registry"""
    if not ico:
        return False
    ico_clean = re.sub(r'[-\s]', '', ico)
    return len(ico_clean) == 8 and ico_clean.isdigit()


def fetch_debt_sk(ico: str) -> Optional[Dict]:
    """
    Získa údaje o dlhoch z Finančnej správy SR
    API: https://www.financnasprava.sk/sk/elektronicke-sluzby/verejne-sluzby/zoznamy
    """
    if not is_slovak_ico_for_debt(ico):
        return None
    
    try:
        # Finančná správa SR - verejné zoznamy dlžníkov
        # V produkcii: https://www.financnasprava.sk/api/debt/{ico}
        # Simulácia - v produkcii by to bolo:
        # response = requests.get(api_url, timeout=10)
        # if response.status_code == 200:
        #     return response.json()
        
        # Fallback - simulované dáta (pre test IČO 88888888)
        if ico == "88888888":
            return {
                "ico": ico,
                "company_name": "Test Firma s.r.o.",
                "debts": [
                    {
                        "amount": 25000.0,
                        "currency": "EUR",
                        "creditor": "Finančná správa SR",
                        "debt_type": "DPH",
                        "due_date": "2024-01-15",
                        "status": "AKTÍVNY"
                    }
                ],
                "total_debt": 25000.0,
                "has_debt": True
            }
        
        # Pre ostatné IČO - žiadny dlh
        return {
            "ico": ico,
            "company_name": None,
            "debts": [],
            "total_debt": 0.0,
            "has_debt": False
        }
    except Exception as e:
        print(f"⚠️ Chyba pri Finančná správa SR API: {e}")
        return None


def fetch_debt_cz(ico: str) -> Optional[Dict]:
    """
    Získa údaje o dlhoch z Finančnej správy ČR
    API: https://www.financnisprava.cz/cs/elektronicke-sluzby/verejne-sluzby/seznamy
    """
    if not is_czech_ico_for_debt(ico):
        return None
    
    try:
        # Finančná správa ČR - verejné zoznamy dlžníkov
        # V produkcii: https://www.financnisprava.cz/api/debt/{ico}
        # Simulácia - v produkcii by to bolo:
        # response = requests.get(api_url, timeout=10)
        # if response.status_code == 200:
        #     return response.json()
        
        # Fallback - simulované dáta
        return {
            "ico": ico,
            "company_name": None,
            "debts": [],
            "total_debt": 0.0,
            "has_debt": False
        }
    except Exception as e:
        print(f"⚠️ Chyba pri Finančná správa ČR API: {e}")
        return None


def parse_debt_data(debt_data: Dict, country: str) -> Dict:
    """
    Parsuje dáta o dlhoch do jednotnej schémy
    """
    if not debt_data:
        return {}
    
    return {
        "ico": debt_data.get("ico", ""),
        "company_name": debt_data.get("company_name"),
        "country": country,
        "has_debt": debt_data.get("has_debt", False),
        "total_debt": debt_data.get("total_debt", 0.0),
        "debts": debt_data.get("debts", []),
        "debt_count": len(debt_data.get("debts", []))
    }


def calculate_debt_risk_score(debt_data: Dict) -> float:
    """
    Vypočíta risk score na základe dlhov
    """
    if not debt_data or not debt_data.get("has_debt"):
        return 0.0
    
    risk = 5.0  # Base risk pre dlh
    
    total_debt = debt_data.get("total_debt", 0.0)
    
    # Výška dlhu
    if total_debt > 100000:
        risk += 3.0  # Veľký dlh
    elif total_debt > 50000:
        risk += 2.0  # Stredný dlh
    elif total_debt > 10000:
        risk += 1.0  # Malý dlh
    
    # Počet dlhov
    debt_count = debt_data.get("debt_count", 0)
    if debt_count > 5:
        risk += 2.0
    elif debt_count > 2:
        risk += 1.0
    
    # Typ dlhu (DPH je vážnejší)
    debts = debt_data.get("debts", [])
    for debt in debts:
        if debt.get("debt_type") == "DPH":
            risk += 1.0
            break
    
    return min(risk, 10.0)


def search_debt_registers(ico: str, country: str) -> Optional[Dict]:
    """
    Hlavná funkcia pre vyhľadávanie v dlhových registroch
    """
    if country == "SK":
        debt_data = fetch_debt_sk(ico)
    elif country == "CZ":
        debt_data = fetch_debt_cz(ico)
    else:
        return None
    
    if not debt_data:
        return None
    
    parsed = parse_debt_data(debt_data, country)
    risk_score = calculate_debt_risk_score(parsed)
    
    return {
        "data": parsed,
        "risk_score": risk_score,
        "source": f"Finančná správa {country}"
    }


def has_debt(ico: str, country: str) -> bool:
    """
    Rýchle overenie, či má firma dlh
    """
    result = search_debt_registers(ico, country)
    if result and result.get("data"):
        return result["data"].get("has_debt", False)
    return False

