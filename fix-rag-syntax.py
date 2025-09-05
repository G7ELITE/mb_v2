#!/usr/bin/env python3
# Script para corrigir erro de sintaxe no rag.py

import re

# Ler o arquivo
with open('/opt/manyblackv2/app/api/rag.py', 'r') as f:
    content = f.read()

# Remover linha problemática e adicionar no lugar correto  
# Encontrar o padrão e corrigir
fixed_content = content.replace(
    '''        )
        
        linhas = historico.split('\n')
        logger.info(f"📝 Prompt formatado com {len(linhas)} linhas de histórico")''',
    '''        )
        
        linhas = historico.split('\\n')
        logger.info(f"📝 Prompt formatado com {len(linhas)} linhas de histórico")'''
)

# Escrever arquivo corrigido
with open('/opt/manyblackv2/app/api/rag.py', 'w') as f:
    f.write(fixed_content)

print("✅ Arquivo rag.py corrigido!")
