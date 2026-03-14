# 🔐 SSL/HTTPS Konfigurácia

## Prehľad

V4-Finstat Projekt podporuje HTTPS pre lokálny vývoj aj produkciu. Pre lokálny vývoj sa používajú self-signed certifikáty, pre produkciu odporúčame Let's Encrypt alebo komerčný certifikát.

## Lokálny vývoj (Self-signed certifikát)

### Vytvorenie certifikátov

Certifikáty sú už vytvorené v `ssl/` adresári:
- `ssl/cert.pem` - SSL certifikát
- `ssl/key.pem` - Privátny kľúč

Ak potrebuješ vytvoriť nové certifikáty:

```bash
cd ssl
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/C=SK/ST=Slovakia/L=Bratislava/O=ILUMINATI/CN=localhost"
```

### Spustenie serverov s SSL

**Backend:**
```bash
cd backend
python main.py
# Server automaticky detekuje SSL súbory a spustí sa s HTTPS
```

**Frontend:**
```bash
cd frontend
npm run dev
# Vite automaticky detekuje SSL súbory a spustí sa s HTTPS
```

### Prístup k aplikácii

- Frontend: `https://localhost:8009/`
- Backend API: `https://localhost:8000/`
- API Docs: `https://localhost:8000/api/docs`

### Varovanie prehliadača

Prehliadač môže zobraziť varovanie o self-signed certifikáte. To je normálne pre lokálny vývoj:

1. Klikni na "Advanced" / "Pokročilé"
2. Klikni na "Proceed to localhost" / "Pokračovať na localhost"

## Produkcia

### Let's Encrypt (odporúčané)

```bash
# Inštalácia certbot
sudo apt-get install certbot

# Získanie certifikátu
sudo certbot certonly --standalone -d yourdomain.com

# Certifikáty budú v:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Konfigurácia pre produkciu

Uprav `backend/main.py`:

```python
ssl_keyfile = "/etc/letsencrypt/live/yourdomain.com/privkey.pem"
ssl_certfile = "/etc/letsencrypt/live/yourdomain.com/fullchain.pem"
```

### Automatické obnovenie

Let's Encrypt certifikáty expirujú každých 90 dní. Nastav cron job:

```bash
# Pridať do crontab
0 0 * * * certbot renew --quiet && systemctl reload nginx
```

## Bezpečnosť

- SSL súbory sú v `.gitignore` (necommitovať!)
- Pre produkciu vždy používajte platné certifikáty
- Self-signed certifikáty sú len pre lokálny vývoj

## Riešenie problémov

### Certifikát nie je dôveryhodný

Pre lokálny vývoj je to normálne. Pre produkciu použite Let's Encrypt.

### Port už používaný

```bash
# Zistiť, ktorý proces používa port
lsof -i :8000
lsof -i :8009

# Zastaviť proces
kill -9 <PID>
```

### SSL chyby v prehliadači

1. Vymaž cache prehliadača
2. Skús iný prehliadač
3. Skontroluj, či sú certifikáty v správnom formáte

## Podpora

Pre otázky alebo problémy kontaktujte tím ILUMINATI SYSTEM.

