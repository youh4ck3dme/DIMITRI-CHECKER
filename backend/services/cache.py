"""
Cache služba pre API odpovede.
V MVP používame in-memory cache, neskôr Redis.
"""

from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import hashlib
import json

# In-memory cache
_cache: Dict[str, tuple[Any, datetime]] = {}
_default_ttl = timedelta(hours=24)  # 24 hodín pre firmy


def get_cache_key(query: str, source: str = "default") -> str:
    """
    Generuje cache key z query a source.
    """
    key_string = f"{source}:{query}"
    return hashlib.md5(key_string.encode()).hexdigest()


def get(key: str) -> Optional[Any]:
    """
    Získa hodnotu z cache.
    
    Returns:
        Cached hodnota alebo None ak nie je v cache alebo expirovala
    """
    if key not in _cache:
        return None
    
    value, expiry_time = _cache[key]
    
    if datetime.now() > expiry_time:
        # Expired - odstrániť
        del _cache[key]
        return None
    
    return value


def set(key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
    """
    Uloží hodnotu do cache.
    
    Args:
        key: Cache key
        value: Hodnota na uloženie
        ttl: Time to live (ak None, použije sa default)
    """
    if ttl is None:
        ttl = _default_ttl
    
    expiry_time = datetime.now() + ttl
    _cache[key] = (value, expiry_time)


def delete(key: str) -> None:
    """Odstráni hodnotu z cache."""
    if key in _cache:
        del _cache[key]


def clear() -> None:
    """Vyčistí celý cache."""
    global _cache
    _cache = {}


def get_stats() -> Dict:
    """Vráti štatistiky cache."""
    now = datetime.now()
    expired_count = sum(1 for _, (_, expiry) in _cache.items() if now > expiry)
    
    # Vyčistiť expirované
    if expired_count > 0:
        keys_to_delete = [k for k, (_, expiry) in _cache.items() if now > expiry]
        for k in keys_to_delete:
            del _cache[k]
    
    return {
        "total_items": len(_cache),
        "expired_items": expired_count,
        "cache_size_mb": _estimate_cache_size()
    }


def _estimate_cache_size() -> float:
    """Odhad veľkosti cache v MB."""
    try:
        total_size = sum(
            len(json.dumps(value, default=str).encode())
            for value, _ in _cache.values()
        )
        return round(total_size / (1024 * 1024), 2)
    except (TypeError, ValueError, KeyError):
        return 0.0

