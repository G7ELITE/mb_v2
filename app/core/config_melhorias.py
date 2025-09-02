"""
Configurações para as melhorias implementadas.

Centraliza parâmetros configuráveis como limiares, timeouts, etc.
"""
from typing import Dict, Any

# Configurações do comparador semântico
LIMIAR_SIMILARIDADE_DEFAULT = 0.8
TIMEOUT_GERACAO_RESPOSTA = 3.0

# Configurações do LLM de resposta curta
TIMEOUT_LLM_CONFIRMACAO = 1.5

# Configurações do RAG
CACHE_TTL_RAG = 60  # 60 segundos
RAG_TOP_K_DEFAULT = 3

# Configurações do contexto do lead
TTL_AGUARDANDO_DEFAULT = 30 * 60  # 30 minutos

# Padronização de action_type
ACTION_TYPE_MAPPING = {
    "message": "send_message",
    "send_message": "send_message",
    "msg": "send_message",
    "text": "send_message"
}

# Tipos de decisão padronizados
DECISION_TYPES = {
    "CATALOGO": "CATALOGO",
    "RAG": "RAG", 
    "PROCEDIMENTO": "PROCEDIMENTO",
    "KB_FALLBACK": "KB_FALLBACK",
    "CONFIRMACAO_CURTA": "CONFIRMACAO_CURTA"
}

# Headers de idempotência
IDEMPOTENCY_HEADER = "X-Idempotency-Key"

# Configurações de log estruturado
LOG_CORRELATION_FIELDS = [
    "decision_id",
    "lead_id", 
    "turn_id",
    "action_type",
    "decision_type",
    "latencia_ms",
    "tools_used",
    "canal"
]


def normalizar_action_type(action_type: str) -> str:
    """
    Normaliza action_type para padrão consistente.
    
    Args:
        action_type: Tipo original da action
        
    Returns:
        Tipo normalizado
    """
    return ACTION_TYPE_MAPPING.get(action_type, action_type)


def get_config() -> Dict[str, Any]:
    """
    Retorna configuração completa das melhorias.
    
    Returns:
        Dicionário com todas as configurações
    """
    return {
        "comparador_semantico": {
            "limiar_similaridade": LIMIAR_SIMILARIDADE_DEFAULT,
            "timeout_geracao": TIMEOUT_GERACAO_RESPOSTA
        },
        "resposta_curta": {
            "timeout_llm": TIMEOUT_LLM_CONFIRMACAO
        },
        "rag": {
            "cache_ttl": CACHE_TTL_RAG,
            "top_k_default": RAG_TOP_K_DEFAULT
        },
        "contexto_lead": {
            "ttl_aguardando": TTL_AGUARDANDO_DEFAULT
        },
        "padronizacao": {
            "action_types": ACTION_TYPE_MAPPING,
            "decision_types": DECISION_TYPES,
            "idempotency_header": IDEMPOTENCY_HEADER
        },
        "logging": {
            "correlation_fields": LOG_CORRELATION_FIELDS
        }
    }
