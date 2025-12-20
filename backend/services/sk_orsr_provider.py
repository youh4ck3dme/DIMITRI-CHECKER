"""
Slovensko - ORSR Provider (Live Scraping)
Hybridný model: Cache → DB → Live Scraping
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup

from services.cache import get, get_cache_key
from services.cache import set as cache_set
from services.database import CompanyCache, get_db_session


class OrsrProvider:
    """
    Provider pre získavanie dát z ORSR.sk cez live scraping.
    Používa hybridný model: Cache → DB → Live Scraping
    """

    CACHE_TTL = timedelta(hours=12)  # Cache na 12 hodín
    DB_REFRESH_DAYS = 7  # Auto-refresh po 7 dňoch

    def __init__(self):
        self.session = requests.Session()
        # Obísť SSL overovanie pre ORSR (nutné)
        self.session.verify = False
        requests.packages.urllib3.disable_warnings()

    def lookup_by_ico(self, ico: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Vyhľadá firmu podľa IČO s hybridným modelom.

        Vrstvy:
        1. Cache (Redis/File) - najrýchlejšie
        2. DB - ak cache expirovala
        3. Live Scraping - ak DB je stará alebo neexistuje

        Args:
            ico: 8-miestne slovenské IČO
            force_refresh: Vynútiť nový scraping

        Returns:
            Dict s dátami firmy alebo None
        """
        # 1. Cache vrstva (najrýchlejšia)
        if not force_refresh:
            cache_key = get_cache_key(f"orsr_sk_{ico}")
            cached_data = get(cache_key)
            if cached_data:
                print(f"✅ Cache hit pre IČO {ico}")
                return cached_data

        # 2. DB vrstva
        with get_db_session() as db:
            if db:
                company = (
                    db.query(CompanyCache)
                    .filter(
                        CompanyCache.identifier == ico, CompanyCache.country == "SK"
                    )
                    .first()
                )

                if company:
                    # Kontrola, či je DB záznam aktuálny
                    days_old = (datetime.utcnow() - company.last_synced_at).days

                    if days_old < self.DB_REFRESH_DAYS and not force_refresh:
                        print(f"✅ DB hit pre IČO {ico} (staré {days_old} dní)")
                        data = (
                            company.company_data or company.data
                        )  # Fallback na legacy field
                        # Uložiť do cache
                        cache_set(cache_key, data, ttl=self.CACHE_TTL)
                        return data
                    else:
                        print(
                            f"⚠️ DB záznam starý ({days_old} dní), spúšťam live scraping..."
                        )

        # 3. Live Scraping (najpomalšie, ale najaktuálnejšie)
        print(f"🔄 Live scraping pre IČO {ico}...")
        live_data = self._scrape_orsr(ico)

        if live_data:
            # Uložiť do cache
            cache_set(cache_key, live_data, ttl=self.CACHE_TTL)

            # Uložiť do DB
            with get_db_session() as db:
                if db:
                    company = (
                        db.query(CompanyCache)
                        .filter(
                            CompanyCache.identifier == ico, CompanyCache.country == "SK"
                        )
                        .first()
                    )

                    if company:
                        # Aktualizovať existujúci záznam
                        company.company_data = live_data
                        company.data = live_data  # Legacy field
                        company.company_name = live_data.get("name")
                        company.risk_score = live_data.get("risk_score")
                        company.last_synced_at = datetime.utcnow()
                        company.updated_at = datetime.utcnow()
                    else:
                        # Vytvoriť nový záznam
                        company = CompanyCache(
                            identifier=ico,
                            country="SK",
                            company_data=live_data,
                            data=live_data,  # Legacy field
                            company_name=live_data.get("name"),
                            risk_score=live_data.get("risk_score"),
                            last_synced_at=datetime.utcnow(),
                        )
                        db.add(company)

                    db.commit()
                    print(f"✅ Dáta uložené do DB pre IČO {ico}")

            return live_data

        return None

    def _scrape_orsr(self, ico: str) -> Optional[Dict]:
        """
        Vykoná live scraping z ORSR.sk.

        Args:
            ico: 8-miestne slovenské IČO

        Returns:
            Dict s normalizovanými dátami alebo None
        """
        try:
            # 1. Vyhľadávanie podľa IČO
            search_url = f"https://www.orsr.sk/hladaj_subjekt.asp?ICO={ico}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            response = self.session.get(search_url, headers=headers, timeout=10)

            if response.status_code != 200:
                print(f"❌ ORSR search failed: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # 2. Nájsť link na detail výpisu
            detail_link = soup.find("a", href=lambda x: x and "vypis.asp?ID=" in x)
            if not detail_link:
                # Alternatíva: hľadať všetky linky obsahujúce "vypis"
                all_links = soup.find_all("a", href=True)
                for link in all_links:
                    href = link.get("href", "")
                    if "vypis.asp?ID=" in href:
                        detail_link = link
                        break
            if not detail_link:
                print(f"⚠️ IČO {ico} sa nenašlo v ORSR")
                # Debug: uložiť HTML pre analýzu
                print(f"   HTML preview: {response.text[:500]}")
                return None

            detail_id = detail_link["href"].split("ID=")[1].split("&")[0]
            detail_url = f"https://www.orsr.sk/vypis.asp?ID={detail_id}&SID=2&P=0"

            # 3. Stiahnuť detail výpisu
            detail_response = self.session.get(detail_url, headers=headers, timeout=10)
            if detail_response.status_code != 200:
                print(f"❌ ORSR detail failed: {detail_response.status_code}")
                return None

            detail_soup = BeautifulSoup(detail_response.text, "html.parser")

            # 4. Parsovať HTML a extrahovať dáta
            data = self._parse_orsr_html(detail_soup, ico)

            return data if data.get("name") else None

        except Exception as e:
            print(f"❌ Chyba pri scraping ORSR: {e}")
            return None

    def _parse_orsr_html(self, soup: BeautifulSoup, ico: str) -> Dict:
        """
        Parsuje HTML z ORSR výpisu a extrahuje dáta.

        Returns:
            Dict s normalizovanými dátami (12-poľový formát)
        """
        data = {
            "ico": ico,
            "country": "SK",
            "name": None,
            "legal_form": None,
            "address": None,
            "postal_code": None,
            "city": None,
            "region": None,
            "district": None,
            "executives": [],
            "shareholders": [],
            "founded": None,
            "status": "Aktívna",
            "dic": None,  # DIČ - často chýba v ORSR
            "ic_dph": None,  # IČ DPH - často chýba v ORSR
        }

        # Názov firmy
        name_elem = soup.find("td", string=lambda x: x and "Obchodné meno:" in str(x))
        if not name_elem:
            # Alternatíva: hľadať <td> obsahujúci text "Obchodné meno:"
            tds = soup.find_all("td")
            for td in tds:
                if "Obchodné meno:" in td.get_text():
                    name_elem = td
                    break
        if name_elem:
            name_row = name_elem.find_next_sibling("td")
            if name_row:
                name_text = name_row.get_text(strip=True)
                # Odstrániť dátum v zátvorkách
                data["name"] = re.sub(r"\s*\(od:.*?\)", "", name_text).strip()

        # Právna forma
        form_elem = soup.find("td", string=lambda x: x and "Právna forma:" in str(x))
        if not form_elem:
            # Alternatíva: hľadať <td> obsahujúci text "Právna forma:"
            tds = soup.find_all("td")
            for td in tds:
                if "Právna forma:" in td.get_text():
                    form_elem = td
                    break
        if form_elem:
            form_row = form_elem.find_next_sibling("td")
            if form_row:
                form_text = form_row.get_text(strip=True)
                data["legal_form"] = re.sub(r"\s*\(od:.*?\)", "", form_text).strip()

        # Adresa (Sídlo)
        address_elem = soup.find("td", string=lambda x: x and "Sídlo:" in str(x))
        if not address_elem:
            # Alternatíva: hľadať <td> obsahujúci text "Sídlo:"
            tds = soup.find_all("td")
            for td in tds:
                if "Sídlo:" in td.get_text():
                    address_elem = td
                    break
        if address_elem:
            address_row = address_elem.find_next_sibling("td")
            if address_row:
                address_text = address_row.get_text(strip=True)
                # Odstrániť dátum v zátvorkách
                address_text = re.sub(r"\s*\(od:.*?\)", "", address_text).strip()
                data["address"] = address_text

                # Extrahovať PSČ a mesto
                postal_match = re.search(r"\b\d{5}\b", address_text)
                if postal_match:
                    data["postal_code"] = postal_match.group()

                # Mesto (posledné slovo pred PSČ alebo po PSČ)
                city_parts = address_text.split(",")
                if len(city_parts) > 1:
                    data["city"] = (
                        city_parts[-1].strip().split()[0]
                        if city_parts[-1].strip()
                        else None
                    )

        # Konatelia (Štatutárny orgán)
        exec_elem = soup.find(
            "td", string=lambda x: x and "štatutárny orgán:" in str(x)
        )
        if exec_elem:
            exec_row = exec_elem.find_next_sibling("td")
            if exec_row:
                exec_links = exec_row.find_all("a")
                for link in exec_links:
                    exec_name = link.get_text(strip=True)
                    if exec_name:
                        data["executives"].append(exec_name)

        # Spoločníci
        share_elem = soup.find("td", string=lambda x: x and "Spoločníci:" in str(x))
        if share_elem:
            share_row = share_elem.find_next_sibling("td")
            if share_row:
                share_links = share_row.find_all("a")
                for link in share_links:
                    share_name = link.get_text(strip=True)
                    if share_name:
                        data["shareholders"].append(share_name)

        # Deň zápisu (founded)
        founded_elem = soup.find("td", string=lambda x: x and "Deň zápisu:" in str(x))
        if founded_elem:
            founded_row = founded_elem.find_next_sibling("td")
            if founded_row:
                founded_text = founded_row.get_text(strip=True)
                founded_text = re.sub(r"\s*\(od:.*?\)", "", founded_text).strip()
                try:
                    # Parsovať dátum DD.MM.YYYY
                    data["founded"] = datetime.strptime(
                        founded_text, "%d.%m.%Y"
                    ).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    pass

        # Status (ak je v likvidácii alebo konkurze)
        if "likvidácia" in str(soup).lower() or "konkurz" in str(soup).lower():
            data["status"] = "Likvidácia/Konkurz"

        # Obohatenie o geolokáciu (Kraj, Okres z PSČ)
        if data.get("postal_code"):
            from services.sk_region_resolver import enrich_address_with_region

            region_data = enrich_address_with_region(
                data.get("address", ""), data["postal_code"]
            )
            data["region"] = region_data.get("region")
            data["district"] = region_data.get("district")
            if region_data.get("city"):
                data["city"] = region_data.get("city")

        # Obohatenie o DIČ/IČ DPH (ak chýba)
        if not data.get("dic") and not data.get("ic_dph"):
            print(f"🔍 Hľadám DIČ/IČ DPH pre IČO {ico}...")
            try:
                from services.sk_zrsr_provider import get_zrsr_provider

                zrsr_provider = get_zrsr_provider()
                zrsr_data = zrsr_provider.lookup_dic_ic_dph(ico, data.get("name"))
                if zrsr_data:
                    # Aktualizovať len ak sú dostupné
                    if zrsr_data.get("dic"):
                        data["dic"] = zrsr_data.get("dic")
                    if zrsr_data.get("ic_dph"):
                        data["ic_dph"] = zrsr_data.get("ic_dph")
                    print(
                        f"✅ Nájdené DIČ/IČ DPH: dic={data.get('dic')}, ic_dph={data.get('ic_dph')}"
                    )
            except Exception as e:
                print(f"⚠️ ZRSR obohatenie zlyhalo: {e}")

        # Obohatenie o finančné ukazovatele z RUZ (voliteľné)
        try:
            from services.sk_ruz_provider import get_ruz_provider

            ruz_provider = get_ruz_provider()
            financial_data = ruz_provider.get_financial_indicators(ico)
            if financial_data:
                data["financial_data"] = financial_data
                print(
                    f"✅ Nájdené finančné dáta: rok={financial_data.get('year')}, revenue={financial_data.get('revenue')}"
                )
        except Exception as e:
            print(f"⚠️ RUZ obohatenie zlyhalo: {e}")

        return data


# Singleton instance
_orsr_provider = None


def get_orsr_provider() -> OrsrProvider:
    """Vráti singleton inštanciu OrsrProvider."""
    global _orsr_provider
    if _orsr_provider is None:
        _orsr_provider = OrsrProvider()
    return _orsr_provider
