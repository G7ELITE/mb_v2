"""
Gerenciador de prompt RAG personalizado.
Permite usar prompt personalizado se existir, senão usa o padrão.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Template padrão para RAG (formato especificado pelo usuário)
DEFAULT_TEMPLATE = """[OBJETIVO]
Responder a mensagem atual do lead seguindo as fielmente [REGRAS]

[HISTÓRICO]
{historico_mensagens}

[CONTEXTO DA FAQ DE CONHECIMENTO]
{kb_context}

[RESPONDA ESSA MENSAGEM ATUAL DO LEAD]
{mensagem_atual}

[REGRAS]
"Responda em tom simples, como se fosse WhatsApp.
Use apenas a resposta correspondente da FAQ, sem mudar nada.
Não adicione frases extras como 'estou à disposição', 'espero ter ajudado', ou qualquer outra informação que não esteja escrita exatamente na resposta da FAQ.
A resposta deve ser apenas uma linha, curta e direta."
Gere apenas 1 frase de até 4 palavras baseado no faq.

🎯[EXEMPLO ESPERADO]
Pergunta: Funciona em OTC?
Resposta correta: Funciona sim, mas o ideal é usar no mercado aberto que é mais estável."""

def get_current_rag_prompt():
    """
    Retorna o template de prompt RAG atual.
    Usa personalizado se existir, senão usa o padrão.
    """
    custom_prompt_path = "/home/devbael/mb-v2/policies/rag_prompt_custom.txt"
    
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
    custom_prompt_path = "/home/devbael/mb-v2/policies/rag_prompt_custom.txt"
    
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
    custom_prompt_path = "/home/devbael/mb-v2/policies/rag_prompt_custom.txt"
    try:
        if os.path.exists(custom_prompt_path):
            with open(custom_prompt_path, 'r', encoding='utf-8') as f:
                return bool(f.read().strip())
    except:
        pass
    return False
