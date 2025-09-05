#!/bin/bash
# 🚀 ManyBlack V2 - Modo DESENVOLVIMENTO (ngrok)
# Este script mantém o comportamento atual para desenvolvimento local

set -e

echo "🚀 ManyBlack V2 - Modo DESENVOLVIMENTO"
echo "===================================="

# Verificar se .env existe, senão copiar do template de dev
if [ ! -f ".env" ]; then
    if [ -f "env.development.example" ]; then
        echo "📝 Criando .env para desenvolvimento..."
        cp env.development.example .env
        echo "⚠️  IMPORTANTE: Configure suas chaves API no arquivo .env"
    else
        echo "❌ Template de desenvolvimento não encontrado!"
        exit 1
    fi
fi

# Executar o script atual de start
./start.sh
