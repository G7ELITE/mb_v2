#!/bin/bash
# 🚀 ManyBlack V2 - Script de Inicialização Completa
# Inicia backend + frontend em modo desenvolvimento

set -e

echo "🚀 Iniciando ManyBlack V2..."
echo "=================================="

# Verificar se está na raiz do projeto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Execute este script da raiz do projeto ManyBlack V2"
    exit 1
fi

# Ativar virtual environment
echo "🐍 Ativando virtual environment..."
source .venv/bin/activate

# Verificar dependências Python
echo "📦 Verificando dependências Python..."
if ! pip show fastapi > /dev/null 2>&1; then
    echo "🔧 Instalando dependências Python..."
    pip install -r requirements.txt
fi

# Verificar dependências Node.js
echo "📦 Verificando dependências Node.js..."
cd studio/
if [ ! -d "node_modules" ]; then
    echo "🔧 Instalando dependências Node.js..."
    npm install
fi
cd ..

# Verificar se PostgreSQL está rodando
echo "🗄️ Verificando PostgreSQL..."
if ! pg_isready -h 127.0.0.1 -p 5432 > /dev/null 2>&1; then
    echo "⚠️ PostgreSQL não está rodando. Inicie-o manualmente:"
    echo "   sudo systemctl start postgresql"
    echo "   ou sudo service postgresql start"
    read -p "Pressione Enter quando PostgreSQL estiver rodando..."
fi

# Aplicar migrações se necessário
echo "🔄 Aplicando migrações do banco..."
alembic upgrade head || echo "⚠️ Erro nas migrações - continuando..."

# Matar processos existentes
echo "🧹 Limpando processos anteriores..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
sleep 2

# Iniciar backend
echo "⚙️ Iniciando backend (porta 8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

# Verificar se backend iniciou
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "✅ Backend iniciado com sucesso!"
else
    echo "❌ Erro ao iniciar backend. Verifique backend.log"
    exit 1
fi

# Iniciar frontend
echo "🎨 Iniciando frontend (porta 5173)..."
cd studio/
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Aguardar frontend inicializar
echo "⏳ Aguardando frontend inicializar..."
sleep 5

# Verificar se frontend iniciou
if curl -s http://127.0.0.1:5173 > /dev/null; then
    echo "✅ Frontend iniciado com sucesso!"
else
    echo "⚠️ Frontend pode estar inicializando ainda..."
fi

echo ""
echo "🎉 ManyBlack V2 iniciado com sucesso!"
echo "=================================="
echo "🌐 Frontend: http://localhost:5173"
echo "⚙️ Backend:  http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 PIDs dos processos:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📄 Logs disponíveis:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 Para parar tudo: ./stop.sh"
