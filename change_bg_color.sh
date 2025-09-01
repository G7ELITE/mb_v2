#!/bin/bash
if [ -z "$1" ]; then
    echo "🎨 Script de Mudança de Cor de Fundo"
    echo "=================================="
    echo ""
    echo "Uso: ./change_bg_color.sh #COR"
    echo ""
    echo "Exemplos:"
    echo "  ./change_bg_color.sh #000000  # Preto total"
    echo "  ./change_bg_color.sh #0a0a0a  # Preto suave"
    echo "  ./change_bg_color.sh #1a1a1a  # Cinza escuro"
    echo "  ./change_bg_color.sh #0d1117  # GitHub escuro"
    echo ""
    echo "Cor atual:"
    grep "background-color: #" studio/src/index.css | head -1
    exit 1
fi

echo "🎨 Alterando cor de fundo para: $1"
sed -i "s/background-color: #[0-9a-fA-F]\{6\}\s*!important;/background-color: $1 !important;/g" studio/src/index.css

echo "✅ Cor alterada com sucesso!"
echo "🌐 Acesse: http://127.0.0.1:5173"
echo "🌙 Ative o modo escuro para ver a mudança"
echo "🔄 Se não mudou, pressione Ctrl+Shift+R no navegador"

echo ""
echo "📄 Linhas alteradas:"
grep -n "$1" studio/src/index.css
