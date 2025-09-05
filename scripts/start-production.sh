#!/bin/bash
# Script de inicialização para produção

set -e

echo "🚀 Iniciando ManyBlack V2 em modo PRODUÇÃO..."

# Aguardar banco de dados
echo "⏳ Aguardando PostgreSQL..."
while ! nc -z postgres 5432; do
    sleep 1
done
echo "✅ PostgreSQL disponível"

# Executar migrações
echo "🔄 Executando migrações..."
alembic upgrade head

# Servir arquivos estáticos e API
echo "🌐 Iniciando servidor..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --access-log \
    --log-level info
