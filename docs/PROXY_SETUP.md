# 🔄 Proxy Rotation Setup Guide

## Prehľad

V4-Finstat Projekt podporuje proxy rotation pre externé API volania. Toto zlepšuje stabilitu, obchádza rate limiting a zvyšuje spoľahlivosť.

## Konfigurácia

### Environment Variables

Proxy pool sa automaticky inicializuje z environment variables pri štarte aplikácie.

#### Základná konfigurácia

```bash
# Comma-separated list of proxy URLs
export PROXY_LIST="http://proxy1.example.com:8080,http://proxy2.example.com:8080"
```

#### S autentifikáciou

```bash
export PROXY_LIST="http://proxy1.example.com:8080,http://proxy2.example.com:8080"
export PROXY_USERNAME="your_username"
export PROXY_PASSWORD="your_password"
```

### Programatická konfigurácia

```python
from services.proxy_rotation import init_proxy_pool

# Inicializovať proxy pool
init_proxy_pool([
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080"
])
```

## Ako to funguje

1. **Round-Robin Rotation**: Proxy sa rotujú v poradí
2. **Health Checking**: Zlyhané proxy sa automaticky označia a preskočia
3. **Cooldown Period**: Zlyhané proxy majú 5-minútový cooldown
4. **Fallback**: Ak nie sú dostupné proxy, používajú sa priame API volania

## Použitie v kóde

### Automatické použitie proxy

```python
from services.proxy_rotation import make_request_with_proxy

response = make_request_with_proxy(
    url="https://api.example.com/data",
    headers={"Accept": "application/json"},
    timeout=10
)
```

### Manuálne získanie proxy

```python
from services.proxy_rotation import get_proxy, mark_proxy_success, mark_proxy_failed
import requests

proxy = get_proxy()
if proxy:
    try:
        response = requests.get(url, proxies=proxy, timeout=10)
        mark_proxy_success(proxy)
    except Exception as e:
        mark_proxy_failed(proxy)
```

## Štatistiky

Zobraziť štatistiky proxy poolu:

```bash
curl http://localhost:8000/api/proxy/stats
```

Odpoveď:
```json
{
  "total_proxies": 2,
  "available_proxies": 2,
  "failed_proxies": 0,
  "proxy_stats": {
    "http://proxy1.com:8080": {
      "success": 150,
      "failed": 2,
      "last_used": "2024-12-19T20:00:00",
      "last_failed": null
    }
  }
}
```

## Prázdny Proxy Pool

Ak proxy pool je prázdny (žiadne proxy nastavené), systém automaticky používa priame API volania. Toto je v poriadku pre:
- Development prostredie
- Lokálne testovanie
- API ktoré nevyžadujú proxy

## Best Practices

1. **Použiť viacero proxy**: Pre lepšiu stabilitu použite aspoň 2-3 proxy
2. **Monitorovať štatistiky**: Pravidelne kontrolujte `/api/proxy/stats`
3. **Rotovať proxy**: Pravidelne meniť proxy pre bezpečnosť
4. **Health Checks**: Monitorovať failed_proxies a odstraňovať nefunkčné proxy

## Troubleshooting

### Proxy sa nepoužívajú

1. Skontrolujte, či sú nastavené environment variables:
   ```bash
   echo $PROXY_LIST
   ```

2. Skontrolujte logy pri štarte:
   ```
   ✅ Proxy pool inicializovaný s 2 proxy
   ```

3. Ak vidíte:
   ```
   ℹ️ Proxy pool prázdny - používajú sa priame API volania
   ```
   Znamená to, že proxy nie sú nastavené (to je OK pre development).

### Proxy zlyhávajú

1. Skontrolujte štatistiky: `/api/proxy/stats`
2. Overte, či proxy sú dostupné
3. Skontrolujte autentifikačné údaje
4. Zlyhané proxy sa automaticky preskočia počas cooldown periodu

## Príklady

### Docker Compose

```yaml
services:
  backend:
    environment:
      - PROXY_LIST=http://proxy1:8080,http://proxy2:8080
      - PROXY_USERNAME=user
      - PROXY_PASSWORD=pass
```

### .env súbor

```env
PROXY_LIST=http://proxy1.example.com:8080,http://proxy2.example.com:8080
PROXY_USERNAME=myuser
PROXY_PASSWORD=mypass
```

---

*Posledná aktualizácia: December 2024*

