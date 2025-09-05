#!/bin/bash
# 📄 ManyBlack V2 - Script de Visualização de Logs
# Mostra logs do backend e frontend em tempo real

# Função para mostrar ajuda
show_help() {
    echo "📄 ManyBlack V2 - Visualização de Logs"
    echo "====================================="
    echo ""
    echo "Uso: ./logs.sh [opção]"
    echo ""
    echo "Opções:"
    echo "  backend, b     - Apenas logs do backend"
    echo "  frontend, f    - Apenas logs do frontend"
    echo "  both, all      - Ambos os logs (padrão)"
    echo "  live, l        - Logs em tempo real (tail -f)"
    echo "  errors, e      - Apenas linhas com erro"
    echo "  clean, c       - Limpar arquivos de log"
    echo "  status, s      - Status dos processos"
    echo "  help, h        - Esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  ./logs.sh               # Mostrar todos os logs"
    echo "  ./logs.sh backend       # Apenas backend"
    echo "  ./logs.sh live          # Acompanhar em tempo real"
    echo "  ./logs.sh errors        # Apenas erros"
}

# Função para verificar status dos processos
show_status() {
    echo "📊 Status dos Processos ManyBlack V2"
    echo "===================================="
    
    # Backend
    BACKEND_PORT_CHECK=$(ss -tulpn | grep ":8000 ")
    if [ -n "$BACKEND_PORT_CHECK" ]; then
        BACKEND_PID=$(echo "$BACKEND_PORT_CHECK" | grep -o 'pid=[0-9]*' | head -1 | cut -d'=' -f2)
        echo "✅ Backend: Rodando (PID $BACKEND_PID)"
        if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
            echo "   🌐 API: Respondendo em http://127.0.0.1:8000"
            curl -s http://127.0.0.1:8000/health | jq . 2>/dev/null || curl -s http://127.0.0.1:8000/health
        else
            echo "   ❌ API: Não responde em http://127.0.0.1:8000"
        fi
    else
        echo "❌ Backend: Não está rodando"
    fi
    
    echo ""
    
    # Frontend
    FRONTEND_PORT_CHECK=$(ss -tulpn | grep ":5173 ")
    if [ -n "$FRONTEND_PORT_CHECK" ]; then
        FRONTEND_PID=$(echo "$FRONTEND_PORT_CHECK" | grep -o 'pid=[0-9]*' | head -1 | cut -d'=' -f2)
        echo "✅ Frontend: Rodando (PID $FRONTEND_PID)"
        if curl -s http://127.0.0.1:5173 > /dev/null 2>&1; then
            echo "   🌐 Interface: Disponível em http://127.0.0.1:5173"
        else
            echo "   ⚠️ Interface: Ainda inicializando ou com problema"
        fi
    else
        echo "❌ Frontend: Não está rodando"
    fi
    
    echo ""
    
    # Logs disponíveis
    echo "📄 Arquivos de Log:"
    if [ -f "backend.log" ]; then
        BACKEND_SIZE=$(du -h backend.log | cut -f1)
        BACKEND_LINES=$(wc -l < backend.log)
        echo "   📄 backend.log: $BACKEND_SIZE ($BACKEND_LINES linhas)"
    else
        echo "   📄 backend.log: Não encontrado"
    fi
    
    if [ -f "frontend.log" ]; then
        FRONTEND_SIZE=$(du -h frontend.log | cut -f1)
        FRONTEND_LINES=$(wc -l < frontend.log)
        echo "   📄 frontend.log: $FRONTEND_SIZE ($FRONTEND_LINES linhas)"
    else
        echo "   📄 frontend.log: Não encontrado"
    fi
}

# Função para limpar logs
clean_logs() {
    echo "🧹 Limpando arquivos de log..."
    
    if [ -f "backend.log" ] || [ -f "frontend.log" ]; then
        echo "Arquivos encontrados:"
        [ -f "backend.log" ] && echo "  - backend.log ($(du -h backend.log | cut -f1))"
        [ -f "frontend.log" ] && echo "  - frontend.log ($(du -h frontend.log | cut -f1))"
        echo ""
        
        read -p "Confirma limpeza? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f backend.log frontend.log
            echo "✅ Logs limpos com sucesso!"
        else
            echo "❌ Operação cancelada"
        fi
    else
        echo "ℹ️ Nenhum arquivo de log encontrado"
    fi
}

# Função para mostrar logs com filtro de erro
show_errors() {
    echo "🔴 Erros nos Logs do ManyBlack V2"
    echo "=================================="
    
    if [ -f "backend.log" ]; then
        echo ""
        echo "📄 Backend Errors:"
        grep -i "error\|exception\|failed\|critical" backend.log | tail -20 || echo "Nenhum erro encontrado no backend"
    fi
    
    if [ -f "frontend.log" ]; then
        echo ""
        echo "📄 Frontend Errors:"
        grep -i "error\|failed\|cannot\|failed to\|warn" frontend.log | tail -20 || echo "Nenhum erro encontrado no frontend"
    fi
    
    if [ ! -f "backend.log" ] && [ ! -f "frontend.log" ]; then
        echo "ℹ️ Nenhum arquivo de log encontrado"
    fi
}

# Parse de argumentos
case "${1:-both}" in
    "backend"|"b")
        echo "📄 Backend Logs (backend.log)"
        echo "============================="
        if [ -f "backend.log" ]; then
            cat backend.log
        else
            echo "❌ Arquivo backend.log não encontrado"
            echo "Execute ./start.sh para iniciar o sistema"
        fi
        ;;
    
    "frontend"|"f")
        echo "📄 Frontend Logs (frontend.log)"
        echo "==============================="
        if [ -f "frontend.log" ]; then
            cat frontend.log
        else
            echo "❌ Arquivo frontend.log não encontrado"
            echo "Execute ./start.sh para iniciar o sistema"
        fi
        ;;
    
    "live"|"l")
        echo "📄 Logs em Tempo Real (Ctrl+C para sair)"
        echo "========================================"
        if [ -f "backend.log" ] && [ -f "frontend.log" ]; then
            echo "👀 Acompanhando backend.log e frontend.log..."
            tail -f backend.log frontend.log
        elif [ -f "backend.log" ]; then
            echo "👀 Acompanhando apenas backend.log..."
            tail -f backend.log
        elif [ -f "frontend.log" ]; then
            echo "👀 Acompanhando apenas frontend.log..."
            tail -f frontend.log
        else
            echo "❌ Nenhum arquivo de log encontrado"
            echo "Execute ./start.sh para iniciar o sistema"
        fi
        ;;
    
    "errors"|"e")
        show_errors
        ;;
    
    "clean"|"c")
        clean_logs
        ;;
    
    "status"|"s")
        show_status
        ;;
    
    "help"|"h"|"--help")
        show_help
        ;;
    
    "both"|"all"|*)
        echo "📄 Todos os Logs do ManyBlack V2"
        echo "================================"
        
        if [ -f "backend.log" ]; then
            echo ""
            echo "⚙️ Backend Logs (últimas 50 linhas):"
            echo "------------------------------------"
            tail -50 backend.log
        else
            echo ""
            echo "❌ Backend log não encontrado"
        fi
        
        if [ -f "frontend.log" ]; then
            echo ""
            echo "🎨 Frontend Logs (últimas 50 linhas):"
            echo "-------------------------------------"
            tail -50 frontend.log
        else
            echo ""
            echo "❌ Frontend log não encontrado"
        fi
        
        if [ ! -f "backend.log" ] && [ ! -f "frontend.log" ]; then
            echo ""
            echo "ℹ️ Nenhum arquivo de log encontrado"
            echo "Execute ./start.sh para iniciar o sistema"
        fi
        ;;
esac
