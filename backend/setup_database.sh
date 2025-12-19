#!/bin/bash

# Setup script pre PostgreSQL databázu

echo ""
echo "═══════════════════════════════════════"
echo "🗄️  ILUMINATI SYSTEM - Database Setup"
echo "═══════════════════════════════════════"
echo ""

# Farba
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Kontrola PostgreSQL
echo -e "${YELLOW}1. Kontrola PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL je nainštalovaný${NC}"
    psql --version
else
    echo -e "${RED}❌ PostgreSQL nie je nainštalovaný${NC}"
    echo ""
    echo "Inštalácia (macOS):"
    echo "  brew install postgresql@14"
    echo "  brew services start postgresql@14"
    echo ""
    echo "Inštalácia (Linux):"
    echo "  sudo apt-get install postgresql postgresql-contrib"
    echo "  sudo systemctl start postgresql"
    echo ""
    exit 1
fi

echo ""

# 2. Vytvorenie databázy
echo -e "${YELLOW}2. Vytváranie databázy...${NC}"
DB_NAME="iluminati_db"
DB_USER="postgres"
DB_PASSWORD="postgres"

# Skúsiť vytvoriť databázu
psql -U postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null && \
    echo -e "${GREEN}✅ Databáza '$DB_NAME' vytvorená${NC}" || \
    echo -e "${YELLOW}⚠️  Databáza už existuje alebo chyba (možno potrebuje heslo)${NC}"

echo ""

# 3. Inštalácia Python dependencies
echo -e "${YELLOW}3. Inštalácia Python dependencies...${NC}"
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || echo "⚠️  venv nie je aktivovaný"

pip install psycopg2-binary sqlalchemy alembic --quiet && \
    echo -e "${GREEN}✅ Dependencies nainštalované${NC}" || \
    echo -e "${RED}❌ Chyba pri inštalácii${NC}"

echo ""

# 4. Inicializácia databázy
echo -e "${YELLOW}4. Inicializácia databázy...${NC}"
python3 -c "
from services.database import init_database
if init_database():
    print('✅ Databáza inicializovaná')
else:
    print('⚠️  Databáza nie je dostupná - používa sa len cache')
" 2>&1

echo ""
echo "═══════════════════════════════════════"
echo -e "${GREEN}✅ SETUP DOKONČENÝ!${NC}"
echo "═══════════════════════════════════════"
echo ""
echo "📋 Database URL:"
echo "   postgresql://postgres:postgres@localhost:5432/iluminati_db"
echo ""
echo "💡 Pre zmenu nastavení:"
echo "   export DATABASE_URL='postgresql://user:pass@host:port/db'"
echo ""
echo "🔧 Pre manuálnu kontrolu:"
echo "   psql -U postgres -d iluminati_db"
echo ""

