#!/bin/bash
# 🌐 ManyBlack V2 - Script de Configuração Automática de Webhook
# Configura ngrok e registra webhook automaticamente

set -e

# Configurações
BACKEND_PORT=8000
NGROK_CONFIG_FILE="$HOME/.ngrok2/ngrok.yml"
WEBHOOK_ENDPOINT="/webhook/telegram"

# Função para mostrar ajuda
show_help() {
    echo "🌐 ManyBlack V2 - Configuração de Webhook"
    echo "========================================"
    echo ""
    echo "Este script automatiza a configuração do webhook do Telegram"
    echo "usando ngrok para expor o backend local."
    echo ""
    echo "Uso: ./webhook.sh [opção]"
    echo ""
    echo "Opções:"
    echo "  start, s       - Iniciar ngrok e configurar webhook"
    echo "  stop           - Parar ngrok"
    echo "  status         - Ver status do ngrok e webhook"
    echo "  url            - Mostrar apenas a URL pública"
    echo "  logs           - Ver logs do ngrok"
    echo "  install        - Instalar ngrok (se necessário)"
    echo "  help, h        - Esta ajuda"
    echo ""
    echo "Pré-requisitos:"
    echo "  - Backend rodando na porta $BACKEND_PORT"
    echo "  - Token do bot Telegram configurado em .env"
    echo "  - ngrok instalado e autenticado"
    echo ""
    echo "Exemplo:"
    echo "  ./webhook.sh start    # Configurar tudo automaticamente"
}

# Função para verificar se ngrok está instalado
check_ngrok() {
    if ! command -v ngrok &> /dev/null; then
        echo "❌ ngrok não está instalado"
        echo ""
        echo "Para instalar o ngrok:"
        echo "1. Acesse: https://ngrok.com/download"
        echo "2. Baixe e instale para seu sistema"
        echo "3. Crie conta gratuita em: https://dashboard.ngrok.com/signup"
        echo "4. Configure o authtoken: ngrok authtoken SEU_TOKEN"
        echo ""
        echo "Ou execute: ./webhook.sh install"
        return 1
    fi
    return 0
}

# Função para instalar ngrok (Ubuntu/Debian)
install_ngrok() {
    echo "📦 Instalando ngrok..."
    
    if command -v snap &> /dev/null; then
        echo "📦 Instalando via snap..."
        sudo snap install ngrok
    else
        echo "📦 Instalando via download direto..."
        cd /tmp
        wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
        tar xzf ngrok-v3-stable-linux-amd64.tgz
        sudo mv ngrok /usr/local/bin/
        rm ngrok-v3-stable-linux-amd64.tgz
    fi
    
    echo "✅ ngrok instalado!"
    echo ""
    echo "🔑 Agora você precisa configurar o authtoken:"
    echo "1. Acesse: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "2. Copie seu authtoken"
    echo "3. Execute: ngrok authtoken SEU_TOKEN"
    echo ""
    read -p "Pressione Enter quando tiver configurado o authtoken..."
}

# Função para verificar se backend está rodando
check_backend() {
    if ! curl -s http://127.0.0.1:$BACKEND_PORT/health > /dev/null; then
        echo "❌ Backend não está rodando na porta $BACKEND_PORT"
        echo ""
        echo "Inicie o backend primeiro:"
        echo "  ./start.sh"
        echo "  ou"
        echo "  source .venv/bin/activate && uvicorn app.main:app --port $BACKEND_PORT"
        return 1
    fi
    return 0
}

# Função para obter token do Telegram
get_telegram_token() {
    if [ -f ".env" ]; then
        TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [ -n "$TOKEN" ]; then
            echo "$TOKEN"
            return 0
        fi
    fi
    
    echo "❌ Token do Telegram não encontrado em .env" >&2
    echo "Configure TELEGRAM_BOT_TOKEN no arquivo .env" >&2
    return 1
}

# Função para iniciar ngrok
start_ngrok() {
    echo "🚀 Iniciando ngrok para porta $BACKEND_PORT..."
    
    # Verificar se já está rodando
    if pgrep -f "ngrok.*http.*$BACKEND_PORT" > /dev/null; then
        echo "⚠️ ngrok já está rodando para a porta $BACKEND_PORT"
        return 0
    fi
    
    # Iniciar ngrok em background
    ngrok http $BACKEND_PORT --log stdout > ngrok.log 2>&1 &
    NGROK_PID=$!
    
    echo "⏳ Aguardando ngrok inicializar..."
    sleep 5
    
    # Verificar se iniciou corretamente
    if ! pgrep -f "ngrok.*http.*$BACKEND_PORT" > /dev/null; then
        echo "❌ Erro ao iniciar ngrok. Verificar ngrok.log:"
        tail -10 ngrok.log
        return 1
    fi
    
    echo "✅ ngrok iniciado (PID: $NGROK_PID)"
    return 0
}

# Função para obter URL pública do ngrok
get_ngrok_url() {
    # Tentar pela API local do ngrok
    local url=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null)
    
    if [ "$url" != "null" ] && [ -n "$url" ]; then
        echo "$url"
        return 0
    fi
    
    # Fallback: buscar no log
    if [ -f "ngrok.log" ]; then
        url=$(grep -o 'https://[^.]*\.ngrok\.io' ngrok.log | tail -1)
        if [ -n "$url" ]; then
            echo "$url"
            return 0
        fi
    fi
    
    return 1
}

# Função para configurar webhook do Telegram
set_webhook() {
    local token="$1"
    local url="$2"
    local webhook_url="${url}${WEBHOOK_ENDPOINT}"
    
    echo "🔗 Configurando webhook: $webhook_url"
    
    local response=$(curl -s -X POST "https://api.telegram.org/bot${token}/setWebhook" \
        -d "url=${webhook_url}" \
        -d "drop_pending_updates=true")
    
    if echo "$response" | jq -e '.ok' > /dev/null 2>&1; then
        echo "✅ Webhook configurado com sucesso!"
        return 0
    else
        echo "❌ Erro ao configurar webhook:"
        echo "$response" | jq .
        return 1
    fi
}

# Função para verificar status do webhook
check_webhook_status() {
    local token="$1"
    
    echo "📊 Status do webhook:"
    local response=$(curl -s "https://api.telegram.org/bot${token}/getWebhookInfo")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '{url: .result.url, has_custom_certificate: .result.has_custom_certificate, pending_update_count: .result.pending_update_count, last_error_date: .result.last_error_date, last_error_message: .result.last_error_message}'
    else
        echo "$response"
    fi
}

# Função principal para configurar tudo
setup_webhook() {
    echo "🌐 Configuração Automática de Webhook"
    echo "====================================="
    
    # Verificações
    check_ngrok || return 1
    check_backend || return 1
    
    local token=$(get_telegram_token) || return 1
    
    # Iniciar ngrok
    start_ngrok || return 1
    
    # Obter URL pública
    echo "🔍 Obtendo URL pública do ngrok..."
    sleep 3  # Aguardar ngrok estabilizar
    
    local public_url=$(get_ngrok_url)
    if [ -z "$public_url" ]; then
        echo "❌ Não foi possível obter URL do ngrok"
        echo "Verificar ngrok.log:"
        tail -10 ngrok.log
        return 1
    fi
    
    echo "✅ URL pública: $public_url"
    
    # Configurar webhook
    set_webhook "$token" "$public_url" || return 1
    
    echo ""
    echo "🎉 Configuração concluída com sucesso!"
    echo "======================================"
    echo "🌐 URL pública: $public_url"
    echo "🔗 Webhook: ${public_url}${WEBHOOK_ENDPOINT}"
    echo "📱 Bot Telegram: Pronto para receber mensagens"
    echo ""
    echo "📊 Para verificar status: ./webhook.sh status"
    echo "📄 Logs do ngrok: tail -f ngrok.log"
    echo "🛑 Para parar: ./webhook.sh stop"
}

# Função para parar ngrok
stop_ngrok() {
    echo "🛑 Parando ngrok..."
    
    if pgrep -f "ngrok.*http" > /dev/null; then
        pkill -f "ngrok.*http"
        echo "✅ ngrok parado"
    else
        echo "ℹ️ ngrok não estava rodando"
    fi
    
    # Limpar logs se desejar
    if [ -f "ngrok.log" ]; then
        read -p "🗑️ Limpar ngrok.log? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f ngrok.log
            echo "✅ ngrok.log limpo"
        fi
    fi
}

# Função para mostrar status
show_status() {
    echo "📊 Status do Webhook e ngrok"
    echo "============================"
    
    # Status do ngrok
    if pgrep -f "ngrok.*http" > /dev/null; then
        local ngrok_pid=$(pgrep -f "ngrok.*http")
        echo "✅ ngrok: Rodando (PID: $ngrok_pid)"
        
        local public_url=$(get_ngrok_url)
        if [ -n "$public_url" ]; then
            echo "🌐 URL pública: $public_url"
        else
            echo "⚠️ URL pública: Não disponível"
        fi
    else
        echo "❌ ngrok: Não está rodando"
    fi
    
    echo ""
    
    # Status do backend
    if curl -s http://127.0.0.1:$BACKEND_PORT/health > /dev/null; then
        echo "✅ Backend: Rodando (porta $BACKEND_PORT)"
    else
        echo "❌ Backend: Não está rodando"
    fi
    
    echo ""
    
    # Status do webhook (se tiver token)
    if [ -f ".env" ]; then
        local token=$(get_telegram_token 2>/dev/null)
        if [ -n "$token" ]; then
            check_webhook_status "$token"
        else
            echo "❌ Token do Telegram não configurado"
        fi
    else
        echo "❌ Arquivo .env não encontrado"
    fi
}

# Parse de argumentos
case "${1:-help}" in
    "start"|"s")
        setup_webhook
        ;;
    
    "stop")
        stop_ngrok
        ;;
    
    "status")
        show_status
        ;;
    
    "url")
        if pgrep -f "ngrok.*http" > /dev/null; then
            local url=$(get_ngrok_url)
            if [ -n "$url" ]; then
                echo "$url"
            else
                echo "❌ URL não disponível" >&2
                exit 1
            fi
        else
            echo "❌ ngrok não está rodando" >&2
            exit 1
        fi
        ;;
    
    "logs")
        echo "📄 Logs do ngrok (Ctrl+C para sair)"
        echo "==================================="
        if [ -f "ngrok.log" ]; then
            tail -f ngrok.log
        else
            echo "❌ ngrok.log não encontrado"
            echo "Execute ./webhook.sh start primeiro"
        fi
        ;;
    
    "install")
        install_ngrok
        ;;
    
    "help"|"h"|"--help"|*)
        show_help
        ;;
esac
