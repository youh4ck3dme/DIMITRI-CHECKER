#!/bin/bash

# Komplexný test script pre ILUMINATI SYSTEM

echo ""
echo "═══════════════════════════════════════"
echo "🧪 ILUMINATI SYSTEM - KOMPLEXNÉ TESTY"
echo "═══════════════════════════════════════"
echo ""

# Farba output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Backend testy
echo -e "${YELLOW}1. BACKEND TESTS${NC}"
echo "─────────────────────────────────────"
cd "$(dirname "$0")"
python3 tests/test_backend_api.py
BACKEND_RESULT=$?
echo ""

# 1.5. Nové features testy
echo -e "${YELLOW}1.5. NEW FEATURES TESTS${NC}"
echo "─────────────────────────────────────"
python3 tests/test_new_features.py
NEW_FEATURES_RESULT=$?
echo ""

# 1.6. Performance testy
echo -e "${YELLOW}1.6. PERFORMANCE TESTS${NC}"
echo "─────────────────────────────────────"
python3 tests/test_performance.py
PERFORMANCE_RESULT=$?
echo ""
node tests/test_frontend_performance.js
FRONTEND_PERFORMANCE_RESULT=$?
echo ""

# 1.7. Proxy rotation testy
echo -e "${YELLOW}1.7. PROXY ROTATION TESTS${NC}"
echo "─────────────────────────────────────"
python3 tests/test_proxy_rotation.py
PROXY_RESULT=$?
echo ""

# 2. Frontend testy
echo -e "${YELLOW}2. FRONTEND TESTS${NC}"
echo "─────────────────────────────────────"
python3 tests/test_frontend_build.py
FRONTEND_RESULT=$?
echo ""

# 3. Integračné testy
echo -e "${YELLOW}3. INTEGRATION TESTS${NC}"
echo "─────────────────────────────────────"
python3 tests/test_integration.py
INTEGRATION_RESULT=$?
echo ""

# Finálny súhrn
echo ""
echo "═══════════════════════════════════════"
echo "📊 FINÁLNY SÚHRN"
echo "═══════════════════════════════════════"
echo ""

TOTAL_TESTS=6
PASSED=0

if [ $BACKEND_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Backend tests: PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Backend tests: FAILED${NC}"
fi

if [ $NEW_FEATURES_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ New features tests: PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ New features tests: FAILED${NC}"
fi

if [ $PERFORMANCE_RESULT -eq 0 ] && [ $FRONTEND_PERFORMANCE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Performance tests: PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Performance tests: FAILED${NC}"
fi

if [ $PROXY_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Proxy rotation tests: PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Proxy rotation tests: FAILED${NC}"
fi

if [ $FRONTEND_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend tests: PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Frontend tests: FAILED${NC}"
fi

if [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests: PASSED${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Integration tests: FAILED${NC}"
fi

echo ""
SUCCESS_RATE=$((PASSED * 100 / TOTAL_TESTS))
echo "📈 Celková úspešnosť: ${PASSED}/${TOTAL_TESTS} (${SUCCESS_RATE}%)"
echo ""

if [ $PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 VŠETKY TESTY ÚSPEŠNÉ!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️ Niektoré testy zlyhali${NC}"
    exit 1
fi

