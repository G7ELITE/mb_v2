#!/bin/bash
# 🚀 ManyBlack V2 - Quick Start Completo
# Inicializa tudo: backend + frontend + ngrok + webhook

set -e

echo "🚀 ManyBlack V2 - Quick Start Completo"
echo "====================================="
echo "🎯 Iniciando: Backend + Frontend + Ngrok + Webhook"
echo ""

# Verificar se está na raiz do projeto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Execute este script da raiz do projeto ManyBlack V2"
    exit 1
fi

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado"
    echo "💡 Copie env.example para .env e configure suas variáveis"
    exit 1
fi

# Carregar variáveis
source .env

# Verificar se token do Telegram está configurado
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ ${#TELEGRAM_BOT_TOKEN} -lt 20 ]; then
    echo "❌ Token do Telegram não configurado"
    echo "💡 Configure TELEGRAM_BOT_TOKEN no arquivo .env"
    exit 1
fi

# Verificar se ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo "❌ Ngrok não está instalado"
    echo "💡 Instale o ngrok: https://ngrok.com/download"
    exit 1
fi

echo "✅ Pré-requisitos verificados"
echo ""

# Passo 1: Pré-voo DEV
echo "📋 PASSO 1: Executando pré-voo DEV..."
python3 dev_preflight.py

echo ""
echo "📋 PASSO 2: Iniciando sistemas..."
./start.sh

echo ""
echo "⏳ Aguardando sistemas estabilizarem (10s)..."
sleep 10

# Passo 3: Configurar ngrok
echo ""
echo "📋 PASSO 3: Configurando ngrok unificado..."
./setup_ngrok.sh

echo ""
echo "⏳ Aguardando ngrok estabilizar (5s)..."
sleep 5

# Passo 4: Ativar webhook
echo ""
echo "📋 PASSO 4: Ativando webhook do Telegram..."
./activate_webhook.sh

echo ""
echo "📋 PASSO 5: Validando smoke DEV..."
python3 smoke_dev.py

echo ""
echo "🎉 QUICK START CONCLUÍDO COM SUCESSO!"
echo "===================================="

# Obter URL do ngrok
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('N/A')
" 2>/dev/null)

echo ""
echo "🔗 SEUS LINKS ÚNICOS:"
echo "   Frontend:  $NGROK_URL"
echo "   Backend:   $NGROK_URL/health"
echo "   API Docs:  $NGROK_URL/docs"
echo "   Dashboard: http://localhost:4040"
echo ""
echo "🧪 COMO TESTAR:"
echo "1. 📱 Envie mensagem para seu bot no Telegram"
echo "2. 📊 Acompanhe logs: ./logs.sh live"
echo "3. 🌐 Acesse interface: $NGROK_URL"
echo "4. 🔍 Verifique webhook: $NGROK_URL/channels/telegram/webhook"
echo ""
echo "🛑 COMO PARAR TUDO:"
echo "   ./stop.sh && pkill ngrok"
echo ""
echo "📄 LOGS DISPONÍVEIS:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo "   Ngrok:    tail -f ngrok.log"
echo ""
echo "🎯 Sistema 100% operacional!"
