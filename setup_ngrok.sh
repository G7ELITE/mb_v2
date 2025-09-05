#!/bin/bash
# 🚀 ManyBlack V2 - Setup Ngrok Unificado
# Configura ngrok para frontend+backend em um único link

set -e

echo "🚀 ManyBlack V2 - Setup Ngrok Unificado"
echo "======================================="
echo "🔗 Configurando ngrok para expor frontend (5173) + backend (proxy)"
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado"
    echo "💡 Copie env.example para .env e configure suas variáveis"
    exit 1
fi

# Verificar se ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok não está instalado"
    echo ""
    echo "🔧 Para instalar o ngrok:"
    echo "1. Acesse: https://ngrok.com/download"
    echo "2. Baixe e instale para seu sistema"
    echo "3. Crie conta gratuita: https://dashboard.ngrok.com/signup"
    echo "4. Configure authtoken: ngrok authtoken SEU_TOKEN"
    echo ""
    exit 1
fi

# Verificar se backend e frontend estão rodando
echo "🔍 Verificando se sistemas estão rodando..."

if ! curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "❌ Backend não está rodando na porta 8000"
    echo "💡 Execute primeiro: ./start.sh ou ./restart.sh"
    exit 1
fi

if ! curl -s http://127.0.0.1:5173 > /dev/null; then
    echo "❌ Frontend não está rodando na porta 5173"
    echo "💡 Execute primeiro: ./start.sh ou ./restart.sh"
    exit 1
fi

echo "✅ Backend e frontend estão rodando"

# Verificar se ngrok já está rodando
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "⚠️ Ngrok já está rodando. Parando sessão anterior..."
    pkill -f ngrok || true
    sleep 2
fi

# Iniciar ngrok
echo "🌐 Iniciando ngrok na porta 5173 (frontend + proxy backend)..."
ngrok http 5173 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

# Aguardar ngrok inicializar
echo "⏳ Aguardando ngrok inicializar..."
for i in {1..20}; do
    if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        echo "✅ Ngrok API acessível!"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "❌ Timeout ao inicializar ngrok API"
        exit 1
    fi
    sleep 1
done

# Aguardar ngrok criar o tunnel
echo "⏳ Aguardando tunnel ser criado..."
for i in {1..15}; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    for tunnel in tunnels:
        if tunnel.get('config', {}).get('addr') == 'http://localhost:5173':
            print(tunnel['public_url'])
            exit(0)
    print('WAITING')
except Exception as e:
    print('ERROR')
" 2>/dev/null)
    
    if [ "$NGROK_URL" != "WAITING" ] && [ "$NGROK_URL" != "ERROR" ] && [ -n "$NGROK_URL" ]; then
        echo "✅ Tunnel criado com sucesso!"
        break
    fi
    
    if [ $i -eq 15 ]; then
        echo "❌ Timeout ao criar tunnel"
        echo "🔍 Debug: Verificando tunnels disponíveis..."
        curl -s http://localhost:4040/api/tunnels | python3 -m json.tool 2>/dev/null || echo "Erro ao acessar API"
        exit 1
    fi
    sleep 2
done

# URL já foi validada no loop acima

echo ""
echo "🎉 NGROK CONFIGURADO COM SUCESSO!"
echo "================================="
echo "🔗 URL pública: $NGROK_URL"
echo ""
echo "🧪 TESTE AS ROTAS:"
echo "✅ Frontend:   $NGROK_URL"
echo "✅ Backend:    $NGROK_URL/health"
echo "✅ API:        $NGROK_URL/api/..."
echo "✅ Webhook:    $NGROK_URL/channels/telegram/webhook"
echo ""

# Testar rotas automaticamente
echo "🔍 Testando rotas automaticamente..."
if curl -s "$NGROK_URL" > /dev/null; then
    echo "✅ Frontend acessível via ngrok"
else
    echo "❌ Frontend não acessível via ngrok"
fi

if curl -s "$NGROK_URL/health" | grep -q "healthy"; then
    echo "✅ Backend acessível via ngrok"
else
    echo "❌ Backend não acessível via ngrok"
fi

echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Configure webhook: ./activate_webhook.sh"
echo "2. Teste no Telegram: envie mensagem para seu bot"
echo "3. Acompanhe logs: ./logs.sh live"
echo "4. Acesse interface: $NGROK_URL"
echo ""
echo "🛑 Para parar ngrok: pkill ngrok"
echo "📄 PID do ngrok: $NGROK_PID"
echo ""
echo "📊 Dashboard ngrok: http://localhost:4040"
