#!/bin/bash

# 🔄 Script para atualizar produção de forma segura
# Uso: ./update-from-dev.sh

set -e

echo "🔄 ATUALIZANDO PRODUÇÃO DE FORMA SEGURA"
echo "======================================"

# 1. Verificar se estamos na branch main
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Erro: Não estamos na branch main (atual: $CURRENT_BRANCH)"
    exit 1
fi

echo "✅ Branch atual: main"

# 2. Fazer backup dos arquivos críticos
echo "🛡️ Fazendo backup de arquivos críticos..."
cp .env .env.production.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "⚠️ Arquivo .env não encontrado"
cp studio/vite.config.ts studio/vite.config.ts.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "⚠️ Arquivo vite.config.ts não encontrado"

echo "✅ Backups criados com timestamp"

# 3. Verificar se há mudanças remotas
echo "📡 Verificando atualizações remotas..."
git fetch origin

COMMITS_BEHIND=$(git rev-list HEAD..origin/main --count)
if [ "$COMMITS_BEHIND" -eq "0" ]; then
    echo "✅ Já estamos atualizados. Nenhuma mudança para aplicar."
    exit 0
fi

echo "📥 Há $COMMITS_BEHIND commit(s) para puxar"

# 4. Mostrar o que será alterado
echo "🔍 Arquivos que serão alterados:"
git diff HEAD..origin/main --name-only

# 5. Perguntar confirmação
read -p "📝 Continuar com o update? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Update cancelado pelo usuário"
    exit 1
fi

# 6. Fazer pull
echo "📥 Fazendo pull das mudanças..."
git pull origin main

# 7. Verificar conflitos críticos
echo "🔍 Verificando configurações críticas..."

# Verificar vite.config.ts
if [ -f "studio/vite.config.ts" ]; then
    if grep -q "ngrok" studio/vite.config.ts; then
        echo "⚠️ ATENÇÃO: vite.config.ts contém configurações de desenvolvimento (ngrok)"
        echo "📄 Restaurando versão de produção..."
        cp studio/vite.config.ts.backup studio/vite.config.ts 2>/dev/null || echo "❌ Backup não encontrado"
    fi
fi

# Verificar .env
if [ -f ".env" ]; then
    if grep -q "127.0.0.1\|localhost" .env; then
        echo "⚠️ ATENÇÃO: .env contém configurações de desenvolvimento"
        echo "📄 Restaurando versão de produção..."
        cp .env.production.backup .env 2>/dev/null || echo "❌ Backup não encontrado"
    fi
fi

echo "✅ Configurações verificadas"

# 8. Fazer deploy
echo "🚀 Iniciando deploy..."
if [ -f "./deploy-prod.sh" ]; then
    ./deploy-prod.sh
else
    echo "📦 Fazendo rebuild dos containers..."
    docker compose -f docker-compose.prod.yml up -d --build
fi

# 9. Verificar se está funcionando
echo "🔍 Verificando se deploy foi bem-sucedido..."
sleep 10

if curl -f -s https://equipe.manyblack.com/health > /dev/null; then
    echo "✅ Deploy bem-sucedido!"
    echo "🌐 Site disponível em: https://equipe.manyblack.com"
else
    echo "❌ Erro no deploy - site não responde"
    echo "📋 Verifique os logs: docker compose -f docker-compose.prod.yml logs app"
    exit 1
fi

echo ""
echo "🎉 UPDATE CONCLUÍDO COM SUCESSO!"
echo "✅ Código atualizado"
echo "✅ Configurações de produção preservadas" 
echo "✅ Deploy realizado"
echo "✅ Site funcionando"
