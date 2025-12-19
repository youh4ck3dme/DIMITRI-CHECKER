"""
Proxy rotation služba pre externé API volania.
Zabezpečuje stabilitu a obchádza rate limiting.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict


class ProxyPool:
    """Pool proxy serverov s rotáciou a health checking"""
    
    def __init__(self):
        self.proxies: List[Dict[str, str]] = []
        self.current_index = 0
        self.failed_proxies: Dict[str, datetime] = {}
        self.proxy_stats: Dict[str, Dict] = defaultdict(lambda: {
            'success': 0,
            'failed': 0,
            'last_used': None,
            'last_failed': None
        })
        self.failure_cooldown = timedelta(minutes=5)  # 5 minút cooldown po chybe
    
    def add_proxy(self, proxy_url: str, auth: Optional[Dict[str, str]] = None):
        """
        Pridať proxy do poolu.
        
        Args:
            proxy_url: URL proxy (napr. "http://proxy.example.com:8080")
            auth: Autentifikačné údaje {"username": "...", "password": "..."}
        """
        proxy_config = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        if auth:
            # Formát: http://user:pass@proxy.example.com:8080
            if "://" in proxy_url:
                protocol = proxy_url.split("://")[0]
                rest = proxy_url.split("://")[1]
                proxy_config["http"] = f"{protocol}://{auth['username']}:{auth['password']}@{rest}"
                proxy_config["https"] = proxy_config["http"]
        
        self.proxies.append(proxy_config)
        print(f"✅ Proxy pridané: {proxy_url}")
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Získať ďalší dostupný proxy (round-robin s health checking).
        
        Returns:
            Proxy config dict alebo None ak nie sú dostupné proxy
        """
        if not self.proxies:
            return None
        
        # Skúsiť nájsť dostupný proxy
        attempts = 0
        max_attempts = len(self.proxies)
        
        while attempts < max_attempts:
            proxy = self.proxies[self.current_index]
            proxy_key = str(proxy)
            
            # Skontrolovať, či proxy nie je v cooldown
            if proxy_key in self.failed_proxies:
                last_failed = self.failed_proxies[proxy_key]
                if datetime.now() - last_failed < self.failure_cooldown:
                    # Proxy je stále v cooldown, preskočiť
                    self.current_index = (self.current_index + 1) % len(self.proxies)
                    attempts += 1
                    continue
            
            # Proxy je dostupný
            self.current_index = (self.current_index + 1) % len(self.proxies)
            self.proxy_stats[proxy_key]['last_used'] = datetime.now()
            return proxy
        
        # Všetky proxy sú v cooldown, vrátiť prvý dostupný
        return self.proxies[0] if self.proxies else None
    
    def mark_success(self, proxy: Dict[str, str]):
        """Označiť proxy ako úspešné"""
        proxy_key = str(proxy)
        self.proxy_stats[proxy_key]['success'] += 1
        
        # Odstrániť z failed_proxies ak tam bol
        if proxy_key in self.failed_proxies:
            del self.failed_proxies[proxy_key]
    
    def mark_failed(self, proxy: Dict[str, str]):
        """Označiť proxy ako zlyhané"""
        proxy_key = str(proxy)
        self.proxy_stats[proxy_key]['failed'] += 1
        self.proxy_stats[proxy_key]['last_failed'] = datetime.now()
        self.failed_proxies[proxy_key] = datetime.now()
    
    def get_stats(self) -> Dict:
        """Získať štatistiky proxy poolu"""
        return {
            'total_proxies': len(self.proxies),
            'available_proxies': len(self.proxies) - len(self.failed_proxies),
            'failed_proxies': len(self.failed_proxies),
            'proxy_stats': dict(self.proxy_stats)
        }


# Globálny proxy pool
_proxy_pool = ProxyPool()


def init_proxy_pool(proxy_list: Optional[List[str]] = None):
    """
    Inicializovať proxy pool s proxy servermi.
    
    Args:
        proxy_list: Zoznam proxy URL (napr. ["http://proxy1.com:8080", "http://proxy2.com:8080"])
    """
    global _proxy_pool
    
    if proxy_list:
        for proxy_url in proxy_list:
            _proxy_pool.add_proxy(proxy_url)
        print(f"✅ Proxy pool inicializovaný s {len(proxy_list)} proxy")
    else:
        # V produkcii by sme načítali z env alebo config súboru
        proxy_env = None  # os.getenv("PROXY_LIST", "")
        if proxy_env:
            proxies = [p.strip() for p in proxy_env.split(",") if p.strip()]
            for proxy_url in proxies:
                _proxy_pool.add_proxy(proxy_url)
        else:
            print("ℹ️ Proxy pool prázdny - používajú sa priame API volania")


def get_proxy() -> Optional[Dict[str, str]]:
    """
    Získať ďalší proxy z poolu.
    
    Returns:
        Proxy config dict alebo None ak nie sú dostupné proxy
    """
    return _proxy_pool.get_next_proxy()


def mark_proxy_success(proxy: Dict[str, str]):
    """Označiť proxy ako úspešné"""
    _proxy_pool.mark_success(proxy)


def mark_proxy_failed(proxy: Dict[str, str]):
    """Označiť proxy ako zlyhané"""
    _proxy_pool.mark_failed(proxy)


def get_proxy_stats() -> Dict:
    """Získať štatistiky proxy poolu"""
    return _proxy_pool.get_stats()


def make_request_with_proxy(url: str, headers: Optional[Dict] = None, timeout: int = 10, max_retries: int = 3):
    """
    Vykonať HTTP request s proxy rotation.
    
    Args:
        url: URL na volanie
        headers: HTTP headers
        timeout: Timeout v sekundách
        max_retries: Maximálny počet pokusov s rôznymi proxy
        
    Returns:
        Response object alebo None pri chybe
    """
    import requests
    
    if headers is None:
        headers = {}
    
    # Ak nie sú proxy, použiť priame volanie
    proxy = get_proxy()
    
    for attempt in range(max_retries):
        try:
            if proxy:
                response = requests.get(
                    url,
                    headers=headers,
                    proxies=proxy,
                    timeout=timeout
                )
                mark_proxy_success(proxy)
                return response
            else:
                # Priame volanie bez proxy
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout
                )
                return response
                
        except requests.exceptions.ProxyError as e:
            if proxy:
                mark_proxy_failed(proxy)
                print(f"⚠️ Proxy chyba: {e}, skúšam ďalší proxy...")
                proxy = get_proxy()
            else:
                print(f"⚠️ Request chyba: {e}")
                return None
                
        except requests.exceptions.RequestException as e:
            if proxy:
                mark_proxy_failed(proxy)
                proxy = get_proxy()
            print(f"⚠️ Request chyba: {e}")
            if attempt == max_retries - 1:
                return None
    
    return None

