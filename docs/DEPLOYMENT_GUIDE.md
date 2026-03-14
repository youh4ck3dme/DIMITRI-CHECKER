# 🚀 V4-Finstat Projekt - Deployment Guide

Kompletný návod na nasadenie ILUMINATI SYSTEM do produkcie.

## 📋 Obsah

1. [Predpoklady](#predpoklady)
2. [Produkčné prostredie](#produkčné-prostredie)
3. [Backend deployment](#backend-deployment)
4. [Frontend deployment](#frontend-deployment)
5. [Databáza setup](#databáza-setup)
6. [Reverse proxy (Nginx)](#reverse-proxy-nginx)
7. [SSL/TLS certifikáty](#ssltls-certifikáty)
8. [Monitoring](#monitoring)
9. [Backup stratégia](#backup-stratégia)
10. [Troubleshooting](#troubleshooting)

## ✅ Predpoklady

### Server požiadavky

- **OS:** Ubuntu 22.04 LTS alebo Debian 11+ (odporúčané)
- **RAM:** Minimálne 2GB (odporúčané 4GB+)
- **CPU:** 2+ jadrá
- **Disk:** 20GB+ voľného miesta
- **Network:** Statická IP adresa

### Softvér

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Nginx (pre reverse proxy)
- Certbot (pre SSL certifikáty)

## 🖥️ Produkčné prostredie

### 1. Server setup

```bash
# Aktualizovať systém
sudo apt update && sudo apt upgrade -y

# Inštalovať základné nástroje
sudo apt install -y git curl wget build-essential

# Inštalovať Python
sudo apt install -y python3 python3-pip python3-venv

# Inštalovať Node.js (pomocou nvm alebo priamo)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Inštalovať PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Inštalovať Nginx
sudo apt install -y nginx
```

### 2. Vytvorenie používateľa

```bash
# Vytvoriť dedikovaného používateľa
sudo adduser iluminati
sudo usermod -aG sudo iluminati

# Prepnúť sa na používateľa
su - iluminati
```

### 3. Klonovanie repozitára

```bash
cd /home/iluminati
git clone <repository-url> iluminati-system
cd iluminati-system
```

## 🔧 Backend deployment

### 1. Setup virtual environment

```bash
cd /home/iluminati/iluminati-system/backend

# Vytvoriť venv
python3 -m venv venv

# Aktivovať
source venv/bin/activate

# Inštalovať závislosti
pip install -r requirements.txt

# Inštalovať produkčné závislosti
pip install gunicorn uvicorn[standard]
```

### 2. Environment premenné

Vytvorte `.env` súbor:

```bash
nano /home/iluminati/iluminati-system/backend/.env
```

```env
# Databáza
DATABASE_URL=postgresql://iluminati:secure_password@localhost:5432/iluminati_db

# Proxy (ak používate)
PROXY_LIST=http://proxy1.com:8080,http://proxy2.com:8080

# API Keys
ARES_API_KEY=your_key_here
RPO_API_KEY=your_key_here

# Environment
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=your_secret_key_here
```

**⚠️ Dôležité:** Nikdy necommitnite `.env` súbor do Git!

### 3. Systemd service

Vytvorte systemd service súbor:

```bash
sudo nano /etc/systemd/system/iluminati-backend.service
```

```ini
[Unit]
Description=ILUMINATI System Backend
After=network.target postgresql.service

[Service]
Type=notify
User=iluminati
Group=iluminati
WorkingDirectory=/home/iluminati/iluminati-system/backend
Environment="PATH=/home/iluminati/iluminati-system/backend/venv/bin"
ExecStart=/home/iluminati/iluminati-system/backend/venv/bin/gunicorn \
    main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/iluminati/backend-access.log \
    --error-logfile /var/log/iluminati/backend-error.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Vytvorte log directory:

```bash
sudo mkdir -p /var/log/iluminati
sudo chown iluminati:iluminati /var/log/iluminati
```

Spustiť service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable iluminati-backend
sudo systemctl start iluminati-backend
sudo systemctl status iluminati-backend
```

### 4. Logy

```bash
# Zobraziť logy
sudo journalctl -u iluminati-backend -f

# Zobraziť posledných 100 riadkov
sudo journalctl -u iluminati-backend -n 100
```

## 🎨 Frontend deployment

### 1. Build produkčnej verzie

```bash
cd /home/iluminati/iluminati-system/frontend

# Inštalovať závislosti
npm install

# Build produkčnej verzie
npm run build
```

Build vytvorí `dist/` adresár s optimalizovanými súbormi.

### 2. Nginx konfigurácia

Vytvorte Nginx konfiguráciu:

```bash
sudo nano /etc/nginx/sites-available/iluminati-system
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect to HTTPS (po nastavení SSL)
    # return 301 https://$server_name$request_uri;

    # Frontend
    root /home/iluminati/iluminati-system/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Aktivovať konfiguráciu:

```bash
sudo ln -s /etc/nginx/sites-available/iluminati-system /etc/nginx/sites-enabled/
sudo nginx -t  # Test konfigurácie
sudo systemctl reload nginx
```

## 🗄️ Databáza setup

### 1. Vytvorenie databázy

```bash
sudo -u postgres psql
```

```sql
-- Vytvoriť používateľa
CREATE USER iluminati WITH PASSWORD 'secure_password';

-- Vytvoriť databázu
CREATE DATABASE iluminati_db OWNER iluminati;

-- Povoliť prístup
GRANT ALL PRIVILEGES ON DATABASE iluminati_db TO iluminati;

-- Ukončiť
\q
```

### 2. Inicializácia schémy

```bash
cd /home/iluminati/iluminati-system/backend
source venv/bin/activate

# Spustiť setup script
./setup_database.sh

# Alebo manuálne pomocou Python
python -c "from services.database import init_database; init_database()"
```

### 3. Backup

Vytvorte backup script:

```bash
nano /home/iluminati/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/iluminati/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U iluminati iluminati_db > $BACKUP_DIR/db_backup_$DATE.sql

# Odstrániť staršie ako 30 dní
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +30 -delete
```

Nastaviť cron job pre automatické backupy:

```bash
crontab -e
```

Pridať:

```
0 2 * * * /home/iluminati/backup-db.sh
```

## 🔒 SSL/TLS certifikáty

### 1. Inštalácia Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Získanie certifikátu

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Certbot automaticky:
- Získa certifikát
- Upraví Nginx konfiguráciu
- Nastaví auto-renewal

### 3. Auto-renewal

Certbot automaticky nastaví cron job. Overiť:

```bash
sudo certbot renew --dry-run
```

## 📊 Monitoring

### 1. Health checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend
curl http://localhost/
```

### 2. System monitoring

```bash
# CPU a RAM
htop

# Disk usage
df -h

# Network
netstat -tulpn
```

### 3. Application monitoring

Použite endpointy:

- `/api/health` - Health check
- `/api/metrics` - Metríky
- `/api/cache/stats` - Cache štatistiky
- `/api/proxy/stats` - Proxy štatistiky

### 4. Log monitoring

```bash
# Backend logy
sudo journalctl -u iluminati-backend -f

# Nginx access logy
sudo tail -f /var/log/nginx/access.log

# Nginx error logy
sudo tail -f /var/log/nginx/error.log
```

## 💾 Backup stratégia

### 1. Databáza

Použite backup script z vyššie (automatické denné backupy).

### 2. Aplikácia

```bash
# Backup aplikácie
tar -czf /home/iluminati/backups/app_backup_$(date +%Y%m%d).tar.gz \
    /home/iluminati/iluminati-system
```

### 3. Konfigurácia

```bash
# Backup Nginx konfigurácie
sudo cp -r /etc/nginx/sites-available /home/iluminati/backups/nginx-config
```

## 🔧 Troubleshooting

### Backend sa nespustí

```bash
# Skontrolovať status
sudo systemctl status iluminati-backend

# Skontrolovať logy
sudo journalctl -u iluminati-backend -n 50

# Skontrolovať port
sudo netstat -tulpn | grep 8000

# Skontrolovať permissions
ls -la /home/iluminati/iluminati-system/backend
```

### Frontend sa nezobrazuje

```bash
# Skontrolovať Nginx
sudo nginx -t
sudo systemctl status nginx

# Skontrolovať permissions
ls -la /home/iluminati/iluminati-system/frontend/dist

# Skontrolovať logy
sudo tail -f /var/log/nginx/error.log
```

### Databáza connection error

```bash
# Skontrolovať PostgreSQL
sudo systemctl status postgresql

# Test pripojenia
psql -U iluminati -d iluminati_db -h localhost

# Skontrolovať .env súbor
cat /home/iluminati/iluminati-system/backend/.env
```

### SSL certifikát expiroval

```bash
# Obnoviť certifikát
sudo certbot renew

# Reload Nginx
sudo systemctl reload nginx
```

## 🔄 Deployment workflow

### 1. Update aplikácie

```bash
cd /home/iluminati/iluminati-system

# Pull najnovšie zmeny
git pull origin main

# Backend update
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart iluminati-backend

# Frontend update
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

### 2. Rollback

```bash
# Vrátiť sa na predchádzajúcu verziu
git checkout <previous-commit>

# Rebuild a restart
cd backend && sudo systemctl restart iluminati-backend
cd ../frontend && npm run build && sudo systemctl reload nginx
```

## 📝 Checklist pre deployment

- [ ] Server setup dokončený
- [ ] PostgreSQL nainštalovaný a nakonfigurovaný
- [ ] Backend service beží
- [ ] Frontend build vytvorený
- [ ] Nginx nakonfigurovaný
- [ ] SSL certifikát nainštalovaný
- [ ] Backup stratégia nastavená
- [ ] Monitoring nastavený
- [ ] Firewall pravidlá nastavené
- [ ] Environment premenné nastavené
- [ ] Logy fungujú
- [ ] Health checks fungujú

---

*Posledná aktualizácia: December 2024*

