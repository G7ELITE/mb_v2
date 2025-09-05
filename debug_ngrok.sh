#!/bin/bash
# 🔍 ManyBlack V2 - Debug Ngrok
# Script para diagnosticar problemas com ngrok

echo "🔍 ManyBlack V2 - Debug Ngrok"
echo "============================="
echo ""

# Verificar se ngrok está instalado
echo "📦 Verificando instalação do ngrok..."
if command -v ngrok &> /dev/null; then
    echo "✅ Ngrok instalado: $(ngrok version 2>/dev/null | head -1)"
else
    echo "❌ Ngrok não está instalado"
    echo "💡 Instale em: https://ngrok.com/download"
    exit 1
fi

echo ""

# Verificar processos ngrok
echo "🔍 Verificando processos ngrok..."
NGROK_PROCESSES=$(pgrep -f ngrok 2>/dev/null | wc -l)
if [ $NGROK_PROCESSES -gt 0 ]; then
    echo "✅ Ngrok está rodando ($NGROK_PROCESSES processo(s))"
    pgrep -f ngrok 2>/dev/null | while read pid; do
        echo "  PID $pid: $(ps -p $pid -o command= 2>/dev/null | cut -c1-80)"
    done
else
    echo "❌ Ngrok não está rodando"
fi

echo ""

# Verificar API do ngrok
echo "🔍 Verificando API do ngrok (porta 4040)..."
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "✅ API ngrok acessível"
    
    # Mostrar tunnels
    echo ""
    echo "📋 Tunnels ativos:"
    TUNNELS_JSON=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null)
    
    if echo "$TUNNELS_JSON" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    if not tunnels:
        print('  Nenhum tunnel ativo')
    else:
        for i, tunnel in enumerate(tunnels, 1):
            name = tunnel.get('name', 'N/A')
            proto = tunnel.get('proto', 'N/A')
            public_url = tunnel.get('public_url', 'N/A')
            config_addr = tunnel.get('config', {}).get('addr', 'N/A')
            print(f'  {i}. {name} ({proto})')
            print(f'     URL pública: {public_url}')
            print(f'     Destino: {config_addr}')
            print()
except Exception as e:
    print(f'  Erro ao processar JSON: {e}')
" 2>/dev/null; then
        echo "✅ Tunnels listados com sucesso"
    else
        echo "❌ Erro ao processar lista de tunnels"
        echo "🔍 JSON bruto:"
        echo "$TUNNELS_JSON" | python3 -m json.tool 2>/dev/null || echo "$TUNNELS_JSON"
    fi
    
else
    echo "❌ API ngrok não acessível"
    echo "💡 Ngrok pode estar parado ou rodando em porta diferente"
fi

echo ""

# Verificar backend e frontend
echo "🔍 Verificando backend e frontend..."
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✅ Backend acessível (porta 8000)"
else
    echo "❌ Backend não acessível (porta 8000)"
fi

if curl -s http://127.0.0.1:5173 > /dev/null 2>&1; then
    echo "✅ Frontend acessível (porta 5173)"
else
    echo "❌ Frontend não acessível (porta 5173)"
fi

echo ""

# Verificar portas ocupadas
echo "🔍 Verificando portas ocupadas..."
echo "Porta 4040 (ngrok API):"
ss -ltn | grep ":4040 " && echo "  ✅ Porta 4040 em uso" || echo "  ❌ Porta 4040 livre"

echo "Porta 8000 (backend):"
ss -ltn | grep ":8000 " && echo "  ✅ Porta 8000 em uso" || echo "  ❌ Porta 8000 livre"

echo "Porta 5173 (frontend):"
ss -ltn | grep ":5173 " && echo "  ✅ Porta 5173 em uso" || echo "  ❌ Porta 5173 livre"

echo ""

# Logs do ngrok se existirem
if [ -f "ngrok.log" ]; then
    echo "📄 Últimas linhas do log ngrok:"
    tail -10 ngrok.log
else
    echo "📄 Arquivo ngrok.log não encontrado"
fi

echo ""

# Sugestões
echo "💡 SUGESTÕES DE SOLUÇÃO:"
echo "1. Se ngrok não está rodando: ./setup_ngrok.sh"
echo "2. Se backend/frontend não estão rodando: ./start.sh"
echo "3. Se API ngrok não responde: parar e reiniciar ngrok"
echo "4. Se tunnel não existe: verificar se ngrok foi iniciado na porta 5173"
echo ""
echo "🔧 COMANDOS ÚTEIS:"
echo "   Parar ngrok: pkill ngrok"
echo "   Ver dashboard: http://localhost:4040"
echo "   Logs em tempo real: tail -f ngrok.log"
