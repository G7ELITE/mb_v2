#!/bin/bash
# 🤖 Script para ativar webhook do Telegram com nova implementação ngrok
# Uso: ./activate_webhook.sh

set -e

echo "🤖 Ativando Webhook Telegram (Nova Implementação)"
echo "================================================"
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado"
    echo "💡 Copie env.example para .env e configure o token"
    exit 1
fi

# Carregar variáveis
source .env

# Verificar token
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ ${#TELEGRAM_BOT_TOKEN} -lt 20 ]; then
    echo "❌ Token do Telegram não configurado ou inválido"
    echo ""
    echo "📋 Para configurar:"
    echo "1. Acesse @BotFather no Telegram"
    echo "2. Crie um bot com /newbot"
    echo "3. Copie o token fornecido"
    echo "4. Edite .env: TELEGRAM_BOT_TOKEN=seu_token_aqui"
    echo ""
    exit 1
fi

# Obter URL do ngrok
echo "🔍 Obtendo URL do ngrok..."
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('ERRO')
" 2>/dev/null)

if [ "$NGROK_URL" = "ERRO" ] || [ -z "$NGROK_URL" ]; then
    echo "❌ Ngrok não está rodando"
    echo "💡 Execute primeiro: ngrok http 5173"
    exit 1
fi

echo "✅ URL ngrok: $NGROK_URL"

# Configurar webhook
WEBHOOK_URL="$NGROK_URL/channels/telegram/webhook?secret=$TELEGRAM_WEBHOOK_SECRET"
echo "🔗 Configurando webhook: $WEBHOOK_URL"

RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
    -d "url=$WEBHOOK_URL")

echo ""
echo "📤 Resposta do Telegram:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Verificar configuração
echo ""
echo "🔍 Verificando configuração..."
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo")
echo "$WEBHOOK_INFO" | python3 -m json.tool

# Extrair status
IS_OK=$(echo "$WEBHOOK_INFO" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('true' if data.get('ok') and data.get('result', {}).get('url') else 'false')
except:
    print('false')
" 2>/dev/null)

echo ""
if [ "$IS_OK" = "true" ]; then
    echo "🎉 WEBHOOK ATIVADO COM SUCESSO!"
    echo ""
    echo "🧪 COMO TESTAR:"
    echo "1. Envie mensagem para seu bot no Telegram"
    echo "2. Acompanhe logs: ./logs.sh live"
    echo "3. Acesse dashboard: $NGROK_URL"
    echo ""
    echo "🎯 Sistema pronto para testes realistas!"
else
    echo "❌ Erro ao configurar webhook"
    echo "💡 Verifique token e tente novamente"
fi
