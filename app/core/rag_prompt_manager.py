"""
Gerenciador de prompt RAG personalizado.
Permite usar prompt personalizado se existir, senão usa o padrão.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Template padrão para RAG (formato especificado pelo usuário)
DEFAULT_TEMPLATE = """[OBJETIVO]
Responder a mensagem atual do lead analisando TODOS os contextos disponíveis da FAQ.

[HISTÓRICO]
{historico_mensagens}

[CONTEXTO DA FAQ DE CONHECIMENTO]
{kb_context}

[RESPONDA ESSA MENSAGEM ATUAL DO LEAD]
{mensagem_atual}

[REGRAS]
1. ANALISE TODOS os contextos fornecidos acima
2. Se houver informações complementares ou específicas, COMBINE-as na resposta
3. Responda em tom simples, como WhatsApp
4. Seja preciso e complete, usando informações de MÚLTIPLOS contextos quando relevante
5. Não adicione informações que não estejam nos contextos fornecidos
6. Se há contextos contraditórios ou específicos (ex: sinais em geral vs sinais para OTC), explique as diferenças

🎯[EXEMPLO ESPERADO]
Pergunta: Ele usa sinais? Se sim, opera todo dia?
Contextos: 1) "Não depende de sinais, opera sozinho" 2) "Para OTC usa sinais só sábado e domingo"
Resposta correta: Não depende de sinais em geral, mas para OTC usa sinais só nos fins de semana."""

def get_current_rag_prompt():
    """
    Retorna o template de prompt RAG atual.
    Usa personalizado se existir, senão usa o padrão.
    """
    custom_prompt_path = "/app/policies/rag_prompt_custom.txt"
    
    try:
        if os.path.exists(custom_prompt_path):
            with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                custom_template = f.read().strip()
                if custom_template:  # Só usa se não estiver vazio
                    logger.debug("Usando prompt RAG personalizado")
                    return custom_template
    except Exception as e:
        logger.warning(f"Erro ao carregar prompt personalizado: {e}")
    
    logger.debug("Usando prompt RAG padrão")
    return DEFAULT_TEMPLATE.strip()

def save_custom_rag_prompt(template: str):
    """
    Salva um template de prompt personalizado.
    """
    custom_prompt_path = "/app/policies/rag_prompt_custom.txt"
    
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(custom_prompt_path), exist_ok=True)
        
        with open(custom_prompt_path, 'w', encoding='utf-8') as f:
            f.write(template)
            
        logger.info(f"Prompt RAG personalizado salvo: {len(template)} caracteres")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar prompt personalizado: {e}")
        return False

def is_using_custom_prompt():
    """
    Retorna True se está usando prompt personalizado, False se padrão.
    """
    custom_prompt_path = "/app/policies/rag_prompt_custom.txt"
    try:
        if os.path.exists(custom_prompt_path):
            with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                return bool(f.read().strip())
    except:
        pass
    return False
