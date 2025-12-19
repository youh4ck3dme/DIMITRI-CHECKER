#!/bin/bash

# ILUMINATI SYSTEM - Start Script
# Spustí backend a frontend server

echo "🚀 ILUMINATI SYSTEM - Spúšťanie serverov..."
echo ""

# Zastaviť existujúce procesy
echo "🛑 Zastavujem existujúce procesy..."
pkill -f 'python.*main.py' 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
sleep 2

# Spustiť backend
echo "🔧 Spúšťam backend server (port 8000)..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..
sleep 3

# Spustiť frontend
echo "🎨 Spúšťam frontend server (port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Servery spustené!"
echo ""
echo "📊 Backend: http://localhost:8000"
echo "🎨 Frontend: http://localhost:5173"
echo ""
echo "📝 API Docs: http://localhost:8000/docs"
echo ""
echo "⚠️  Pre zastavenie serverov stlačte Ctrl+C alebo spustite: ./stop.sh"
echo ""

# Počakať na ukončenie
wait

