#!/bin/bash
# 🚀 ManyBlack V2 - Deploy para PRODUÇÃO na VPS
# Script para executar NA VPS após git pull

set -e

echo "🚀 ManyBlack V2 - Deploy PRODUÇÃO"
echo "================================="

# Verificar se está em produção
if [ "$APP_ENV" != "production" ] && [ ! -f ".env.production" ]; then
    echo "⚠️  Este script deve ser executado na VPS de produção"
    echo "📝 Certifique-se de ter o arquivo .env configurado"
    exit 1
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker compose -f docker-compose.prod.yml down

# Build das imagens
echo "🔨 Building containers..."
docker compose -f docker-compose.prod.yml build --no-cache

# Subir serviços
echo "🚀 Iniciando serviços..."
docker compose -f docker-compose.prod.yml up -d

# Aguardar serviços iniciarem
echo "⏳ Aguardando serviços..."
sleep 30

# Verificar saúde
echo "🔍 Verificando saúde dos serviços..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Deploy realizado com sucesso!"
    echo "🌐 Acesse: https://equipe.manyblack.com"
else
    echo "❌ Erro no deploy. Verificando logs..."
    docker compose -f docker-compose.prod.yml logs --tail=50
    exit 1
fi
