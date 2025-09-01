#!/bin/bash
# 🛑 ManyBlack V2 - Script para Parar Todos os Processos
# Para backend e frontend com limpeza completa

echo "🛑 Parando ManyBlack V2..."
echo "=========================="

# Mostrar processos que serão mortos
echo "🔍 Processos encontrados:"
echo "Backend (uvicorn):"
pgrep -f "uvicorn.*app.main" 2>/dev/null | while read pid; do
    echo "  PID $pid: $(ps -p $pid -o command= 2>/dev/null | cut -c1-80)"
done || echo "  Nenhum processo backend encontrado"

echo "Frontend (vite/npm):"
pgrep -f "vite\|npm run dev" 2>/dev/null | while read pid; do
    echo "  PID $pid: $(ps -p $pid -o command= 2>/dev/null | cut -c1-80)"
done || echo "  Nenhum processo frontend encontrado"

echo ""

# Parar processos graciosamente
echo "🛑 Enviando SIGTERM para processos..."
pkill -f "uvicorn.*app.main" 2>/dev/null && echo "✅ Backend: SIGTERM enviado" || echo "ℹ️ Backend: nenhum processo encontrado"
pkill -f "vite" 2>/dev/null && echo "✅ Frontend (vite): SIGTERM enviado" || echo "ℹ️ Frontend (vite): nenhum processo encontrado"
pkill -f "npm run dev" 2>/dev/null && echo "✅ Frontend (npm): SIGTERM enviado" || echo "ℹ️ Frontend (npm): nenhum processo encontrado"

# Aguardar encerramento gracioso
echo "⏳ Aguardando encerramento gracioso (5s)..."
sleep 5

# Verificar se ainda há processos e forçar se necessário
REMAINING_BACKEND=$(pgrep -f "uvicorn.*app.main" 2>/dev/null | wc -l)
REMAINING_FRONTEND=$(pgrep -f "vite\|npm run dev" 2>/dev/null | wc -l)

if [ "$REMAINING_BACKEND" -gt 0 ] || [ "$REMAINING_FRONTEND" -gt 0 ]; then
    echo "🔨 Processos resistentes encontrados. Forçando encerramento..."
    
    pkill -9 -f "uvicorn.*app.main" 2>/dev/null && echo "💀 Backend: SIGKILL enviado" || true
    pkill -9 -f "vite" 2>/dev/null && echo "💀 Frontend (vite): SIGKILL enviado" || true
    pkill -9 -f "npm run dev" 2>/dev/null && echo "💀 Frontend (npm): SIGKILL enviado" || true
    pkill -9 -f "node.*vite" 2>/dev/null && echo "💀 Node/Vite: SIGKILL enviado" || true
    
    sleep 2
fi

# Verificação final
echo "🔍 Verificação final..."
FINAL_CHECK_BACKEND=$(pgrep -f "uvicorn.*app.main" 2>/dev/null | wc -l)
FINAL_CHECK_FRONTEND=$(pgrep -f "vite\|npm run dev" 2>/dev/null | wc -l)

if [ "$FINAL_CHECK_BACKEND" -eq 0 ] && [ "$FINAL_CHECK_FRONTEND" -eq 0 ]; then
    echo "✅ Todos os processos foram encerrados com sucesso!"
else
    echo "⚠️ Alguns processos podem ainda estar rodando:"
    pgrep -f "uvicorn\|vite\|npm run dev" 2>/dev/null | while read pid; do
        echo "  PID $pid: $(ps -p $pid -o command= 2>/dev/null | cut -c1-80)"
    done
fi

# Limpeza de portas (opcional)
echo ""
echo "🧹 Limpeza adicional..."

# Verificar se as portas estão liberadas
if ss -ltn | grep -q ":8000 "; then
    echo "⚠️ Porta 8000 ainda em uso. Pode ser necessário aguardar alguns segundos."
else
    echo "✅ Porta 8000 liberada"
fi

if ss -ltn | grep -q ":5173 "; then
    echo "⚠️ Porta 5173 ainda em uso. Pode ser necessário aguardar alguns segundos."
else
    echo "✅ Porta 5173 liberada"
fi

# Limpeza de logs (opcional)
if [ -f "backend.log" ] || [ -f "frontend.log" ]; then
    echo ""
    read -p "🗑️ Deseja limpar os arquivos de log? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f backend.log frontend.log
        echo "✅ Logs limpos"
    else
        echo "📄 Logs mantidos (backend.log, frontend.log)"
    fi
fi

echo ""
echo "🏁 ManyBlack V2 parado!"
echo "======================"
echo "Para reiniciar: ./start.sh ou ./restart.sh"
