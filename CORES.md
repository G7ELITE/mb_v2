# 🎨 Guia de Cores - ManyBlack Studio

## 📍 Localização dos Arquivos de Cor

### 🎯 Arquivo Principal: `studio/src/index.css`

## 🌙 Cores do Modo Escuro

### Fundo Principal (Linhas 78, 82, 87, 92):
```css
background-color: #0f0f0f !important;  /* Cinza quase preto - ATUAL */
```

### 🎨 Opções de Cores Escuras:
```css
#000000  /* Preto total */
#0a0a0a  /* Preto suave */
#0f0f0f  /* Cinza quase preto (ATUAL) */
#1a1a1a  /* Cinza escuro */
#0d1117  /* Cinza azulado escuro (estilo GitHub) */
#1c1c1c  /* Cinza médio escuro */
#2d2d2d  /* Cinza mais claro */
```

## 🔧 Como Alterar:

### Método 1: Manual
1. Editar `studio/src/index.css`
2. Buscar por `#0f0f0f`
3. Substituir pela nova cor
4. Salvar (mudança é automática)

### Método 2: Script Rápido
```bash
# Usar o script de mudança rápida:
./change_bg_color.sh #000000  # Para preto total
./change_bg_color.sh #1a1a1a  # Para cinza escuro
```

## 🌞 Cores do Modo Claro

### Fundo Principal (Linha 12):
```css
background-color: #f8fafc;  /* Cinza muito claro - ATUAL */
```

### 🎨 Opções de Cores Claras:
```css
#ffffff  /* Branco puro */
#f8fafc  /* Cinza muito claro (ATUAL) */
#f0f0f0  /* Cinza claro */
#e3f2fd  /* Azul muito claro */
#f1f8e9  /* Verde muito claro */
#fff3e0  /* Laranja muito claro */
```

## 🃏 Cores dos Cards

### Modo Claro:
```css
.card { @apply bg-white ... }  /* Branco */
```

### Modo Escuro:
```css
.dark .card { @apply bg-gray-800 ... }  /* Cinza escuro */
```

## ⚡ Comandos Úteis

### Ver cor atual:
```bash
grep -n "#0f0f0f" studio/src/index.css
```

### Restart para aplicar mudanças:
```bash
./restart.sh
```

### Verificar frontend:
```bash
curl -s http://127.0.0.1:5173 > /dev/null && echo "OK" || echo "Problema"
```

## 🎯 Dicas

1. **Sempre use `!important`** para garantir que a cor seja aplicada
2. **Teste no navegador** com Ctrl+Shift+R para forçar reload
3. **Cores muito escuras** (#000000) podem ser cansativas
4. **Cores muito claras** em modo escuro quebram o design
5. **Use ferramentas online** para testar combinações de cores

## 🌈 Combinações Recomendadas

### Elegante:
- Fundo: `#0a0a0a`
- Cards: `bg-gray-800`
- Texto: `#f0f0f0`

### Profissional:
- Fundo: `#0d1117` 
- Cards: `bg-gray-800`
- Texto: `#ffffff`

### Suave:
- Fundo: `#1a1a1a`
- Cards: `bg-gray-700`
- Texto: `#e0e0e0`
