#!/bin/bash
# 🔄 ManyBlack V2 - Script de Restart Rápido
# Para todos os processos e reinicia backend + frontend

set -e

echo "🔄 Reiniciando ManyBlack V2..."
echo "==============================="

# Verificar se está na raiz do projeto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Execute este script da raiz do projeto ManyBlack V2"
    exit 1
fi

# Parar todos os processos relacionados
echo "🛑 Parando processos existentes..."
pkill -f "uvicorn.*app.main" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true

# Aguardar processos terminarem
echo "⏳ Aguardando processos terminarem..."
sleep 3

# Verificar se ainda há processos rodando
if pgrep -f "uvicorn.*app.main" > /dev/null || pgrep -f "vite" > /dev/null; then
    echo "🔨 Forçando encerramento de processos resistentes..."
    pkill -9 -f "uvicorn.*app.main" 2>/dev/null || true
    pkill -9 -f "vite" 2>/dev/null || true
    sleep 2
fi

# Limpar logs antigos
echo "🧹 Limpando logs antigos..."
rm -f backend.log frontend.log 2>/dev/null || true

# Ativar virtual environment
echo "🐍 Ativando virtual environment..."
source .venv/bin/activate

# Verificar saúde do banco (quick check)
echo "🗄️ Verificando conexão com banco..."
if ! python -c "
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
async def check_db():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'manyblack_v2'),
            user=os.getenv('DB_USER', 'mbuser'),
            password=os.getenv('DB_PASSWORD', 'change-me')
        )
        await conn.close()
        print('✅ Banco conectado')
    except Exception as e:
        print(f'❌ Erro no banco: {e}')
        exit(1)

asyncio.run(check_db())
" 2>/dev/null; then
    echo "⚠️ Problema de conexão com banco. Continuando mesmo assim..."
fi

# Iniciar backend
echo "⚙️ Iniciando backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!

# Aguardar backend inicializar
echo "⏳ Aguardando backend (5s)..."
sleep 5

# Verificar saúde do backend
if curl -s http://127.0.0.1:8000/health | grep -q "healthy"; then
    echo "✅ Backend reiniciado com sucesso!"
else
    echo "❌ Backend com problemas. Verificar backend.log:"
    tail -10 backend.log
    exit 1
fi

# Iniciar frontend
echo "🎨 Iniciando frontend..."
cd studio/
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Aguardar frontend
echo "⏳ Aguardando frontend (5s)..."
sleep 5

# Verificar se frontend iniciou
if curl -s http://127.0.0.1:5173 > /dev/null; then
    echo "✅ Frontend OK na porta 5173"
else
    echo "⚠️ Frontend ainda inicializando"
fi

echo ""
echo "🎉 Restart concluído com sucesso!"
echo "================================"
echo "🌐 Frontend: http://localhost:5173"
echo "⚙️ Backend:  http://localhost:8000"
echo ""
echo "📋 Novos PIDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📊 Status rápido:"
curl -s http://127.0.0.1:8000/health | jq . 2>/dev/null || curl -s http://127.0.0.1:8000/health
echo ""
echo ""
echo "📄 Para ver logs em tempo real:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
