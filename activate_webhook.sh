#!/bin/bash
# 🤖 Script para ativar webhook do Telegram com nova implementação ngrok
# Uso: ./activate_webhook.sh

set -e

echo "🤖 Ativando Webhook Telegram (Ngrok Unificado)"
echo "================================================"
echo "🔗 Usando um único link ngrok para frontend + backend"
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

# Função para obter URL do ngrok (mais robusta)
get_ngrok_url() {
    local max_attempts=15
    local attempt=1
    
    echo "🔍 Obtendo URL atual do ngrok..."
    
    while [ $attempt -le $max_attempts ]; do
        local url=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    if tunnels:
        # Pegar a primeira URL pública ativa (não filtrar por porta específica)
        for tunnel in tunnels:
            public_url = tunnel.get('public_url', '')
            if public_url and ('https://' in public_url):
                print(public_url)
                sys.exit(0)
    print('WAITING')
except Exception as e:
    print('ERROR')
" 2>/dev/null)
        
        if [ "$url" != "WAITING" ] && [ "$url" != "ERROR" ] && [ -n "$url" ]; then
            echo "$url"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "ERROR"
            return 1
        fi
        
        echo "⏳ Tentativa $attempt/$max_attempts - aguardando ngrok..."
        sleep 1
        attempt=$((attempt + 1))
    done
}

# Obter URL do ngrok
NGROK_URL=$(get_ngrok_url)

if [ "$NGROK_URL" = "ERROR" ] || [ -z "$NGROK_URL" ]; then
    echo "❌ Ngrok não está rodando ou tunnel não encontrado"
    echo "💡 Execute primeiro: ./setup_ngrok.sh"
    echo "🔗 O ngrok unificado expõe frontend + backend via proxy"
    echo ""
    echo "🔍 Debug - Verificando tunnels disponíveis:"
    curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    if tunnels:
        for i, tunnel in enumerate(tunnels):
            print(f'{i+1}. {tunnel.get(\"public_url\", \"N/A\")} -> {tunnel.get(\"config\", {}).get(\"addr\", \"N/A\")}')
    else:
        print('Nenhum tunnel ativo')
except:
    print('Erro ao parsear resposta do ngrok')
" 2>/dev/null || echo "API ngrok não disponível"
    exit 1
fi

echo "✅ URL ngrok detectado: $NGROK_URL"

# Configurar webhook
WEBHOOK_URL="$NGROK_URL/channels/telegram/webhook?secret=$TELEGRAM_WEBHOOK_SECRET"
echo "🔗 Configurando webhook URL:"
echo "   $WEBHOOK_URL"

# Testar conectividade do webhook antes de configurar
echo ""
echo "🧪 Testando conectividade do webhook..."

# Testar backend local primeiro
if curl -s --connect-timeout 5 "http://localhost:8000/health" > /dev/null; then
    echo "✅ Backend local OK"
else
    echo "❌ Backend local não responde"
    echo "💡 Execute './start.sh' primeiro"
    exit 1
fi

# Testar ngrok
if curl -s --connect-timeout 10 "$NGROK_URL/health" > /dev/null; then
    echo "✅ Backend acessível via ngrok"
else
    echo "❌ Backend não acessível via ngrok"
    echo "⏳ Aguardando ngrok estabilizar (5s)..."
    sleep 5
    if curl -s --connect-timeout 10 "$NGROK_URL/health" > /dev/null; then
        echo "✅ Backend agora acessível via ngrok"
    else
        echo "❌ Ngrok não está funcionando corretamente"
        echo "💡 Verifique se ngrok foi configurado corretamente"
        exit 1
    fi
fi

echo ""
echo "📤 Enviando setWebhook para Telegram API..."
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
    -d "url=$WEBHOOK_URL" \
    --connect-timeout 10)

echo "📤 Resposta do setWebhook:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Verificar configuração via getWebhookInfo
echo ""
echo "🔍 Verificando configuração via getWebhookInfo..."
WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" --connect-timeout 10)

echo "📥 Informações do webhook:"
echo "$WEBHOOK_INFO" | python3 -m json.tool 2>/dev/null || echo "$WEBHOOK_INFO"

# Extrair e validar status
VALIDATION=$(echo "$WEBHOOK_INFO" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    result = data.get('result', {})
    webhook_url = result.get('url', '')
    max_connections = result.get('max_connections', 0)
    pending_updates = result.get('pending_update_count', 0)
    
    print(f'URL: {webhook_url}')
    print(f'Max connections: {max_connections}')
    print(f'Pending updates: {pending_updates}')
    
    # Verificar se webhook está configurado corretamente
    is_ok = data.get('ok', False) and bool(webhook_url)
    print(f'Status: {\"OK\" if is_ok else \"ERROR\"}')
    print('true' if is_ok else 'false')
except Exception as e:
    print(f'Erro ao processar: {e}')
    print('false')
" 2>/dev/null)

echo "📊 Validação:"
echo "$VALIDATION" | head -n -1  # Todas as linhas exceto a última
IS_OK=$(echo "$VALIDATION" | tail -n 1)  # Última linha com true/false

echo ""
if [ "$IS_OK" = "true" ]; then
    echo "🎉 WEBHOOK ATIVADO COM SUCESSO!"
    echo ""
    echo "🧪 COMO TESTAR:"
    echo "1. Envie mensagem para seu bot no Telegram"
    echo "2. Acompanhe logs: ./logs.sh live"
    echo "3. Acesse frontend: $NGROK_URL"
    echo "4. Acesse backend: $NGROK_URL/health"
    echo ""
    echo "🎯 Sistema pronto para testes realistas!"
    echo "🔗 Um único link ngrok para tudo!"
else
    echo "❌ Erro ao configurar webhook"
    echo "💡 Verifique token e tente novamente"
fi
