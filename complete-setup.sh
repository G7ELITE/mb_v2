#!/bin/bash
# 🚀 ManyBlack V2 - Setup Completo de Produção

set -e

echo "🚀 INICIANDO SETUP COMPLETO DE PRODUÇÃO"
echo "======================================"

# 1. Definir ambiente
export APP_ENV=production

# 2. Parar containers existentes
echo "🛑 Parando containers existentes..."
docker compose -f docker-compose.prod.yml down || true

# 3. Build e iniciar serviços
echo "🔨 Building e iniciando serviços..."
docker compose -f docker-compose.prod.yml up -d --build

# 4. Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 30

# 5. Verificar status
echo "📊 Status dos containers:"
docker ps

# 6. Testar aplicação localmente
echo "🔍 Testando aplicação..."
sleep 5
curl -f http://localhost/health && echo "✅ Health check OK" || echo "❌ Health check falhou"

# 7. Testar via domínio
curl -f https://equipe.manyblack.com/health && echo "✅ Domínio OK" || echo "❌ Domínio falhou"

# 8. Configurar webhook do Telegram
echo "📱 Configurando webhook do Telegram..."
TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d'=' -f2)
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://equipe.manyblack.com/channels/telegram/webhook"}' \
     && echo "✅ Webhook configurado" || echo "❌ Webhook falhou"

echo "🎉 SETUP COMPLETO FINALIZADO!"
echo "🌐 Acesse: https://equipe.manyblack.com"
