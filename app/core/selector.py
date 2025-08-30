"""
Selector - Escolhedor de automações

Escolhe automação por regras em PT-BR (compiladas para predicados).
Avalia elegibilidade do catálogo contra o snapshot do lead.
"""
import yaml
import pathlib
import logging
from typing import Dict, Any, Optional, List

from app.data.schemas import Env

logger = logging.getLogger(__name__)

# Cache do catálogo carregado
_CATALOG_CACHE: Optional[List[Dict[str, Any]]] = None


async def select_automation(env: Env) -> Optional[Dict[str, Any]]:
    """
    Seleciona automação adequada baseada no catálogo de regras.
    
    Args:
        env: Ambiente com snapshot do lead
        
    Returns:
        Automação selecionada ou None se nenhuma aplicável
    """
    catalog = load_catalog()
    
    if not catalog:
        logger.warning("Catálogo vazio ou não carregado")
        return None
    
    snapshot = env.snapshot
    text = ""
    if env.messages_window:
        text = env.messages_window[-1].text.lower()
    
    logger.info(f"Avaliando {len(catalog)} automações do catálogo")
    
    # Avaliar cada automação por prioridade
    eligible_automations = []
    
    for automation in catalog:
        if is_automation_eligible(automation, snapshot, text):
            eligible_automations.append(automation)
            logger.info(f"Automação elegível: {automation.get('id', 'unknown')}")
    
    if not eligible_automations:
        logger.info("Nenhuma automação elegível encontrada")
        return None
    
    # Ordenar por prioridade (maior primeiro)
    eligible_automations.sort(
        key=lambda x: x.get("priority", 0.0), 
        reverse=True
    )
    
    # Selecionar a de maior prioridade
    selected = eligible_automations[0]
    logger.info(f"Automação selecionada: {selected.get('id', 'unknown')} (prioridade: {selected.get('priority', 0)})")
    
    # Converter para formato de ação
    return convert_automation_to_action(selected)


def load_catalog() -> List[Dict[str, Any]]:
    """
    Carrega catálogo de automações do arquivo YAML.
    
    Returns:
        Lista de automações do catálogo
    """
    global _CATALOG_CACHE
    
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE
    
    catalog_path = pathlib.Path("policies") / "catalog.yml"
    
    if not catalog_path.exists():
        logger.error(f"Arquivo de catálogo não encontrado: {catalog_path}")
        return []
    
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            _CATALOG_CACHE = yaml.safe_load(f) or []
        
        logger.info(f"Catálogo carregado com {len(_CATALOG_CACHE)} automações")
        return _CATALOG_CACHE
        
    except Exception as e:
        logger.error(f"Erro ao carregar catálogo: {str(e)}")
        return []


def is_automation_eligible(automation: Dict[str, Any], snapshot, text: str) -> bool:
    """
    Verifica se automação é elegível baseada nas regras de elegibilidade.
    
    Args:
        automation: Definição da automação
        snapshot: Snapshot do lead
        text: Texto da mensagem
        
    Returns:
        True se elegível, False caso contrário
    """
    # Verificar tópico/contexto
    topic = automation.get("topic", "")
    use_when = automation.get("use_when", "").lower()
    
    # Verificar se o contexto da mensagem bate com o tópico
    if topic and topic.lower() not in text:
        # Se não tem o tópico no texto, verificar use_when
        if not any(word in text for word in use_when.split()):
            return False
    
    # Compilar e avaliar regra de elegibilidade
    eligibility = automation.get("eligibility", "")
    return evaluate_eligibility_rule(eligibility, snapshot)


def evaluate_eligibility_rule(rule: str, snapshot) -> bool:
    """
    Avalia regra de elegibilidade em PT-BR contra o snapshot.
    TODO: Implementar compilador completo PT-BR → predicado.
    
    Args:
        rule: Regra em português
        snapshot: Snapshot do lead
        
    Returns:
        True se a regra é satisfeita
    """
    if not rule:
        return True  # Sem regra = sempre elegível
    
    rule_lower = rule.lower()
    
    # Compilador heurístico básico
    # TODO: Expandir para DSL completa
    
    # Regras de depósito
    if "não concordou em depositar" in rule_lower:
        can_deposit = snapshot.agreements.get("can_deposit", False)
        if can_deposit:
            return False
    
    if "concordou em depositar" in rule_lower and "não concordou" not in rule_lower:
        can_deposit = snapshot.agreements.get("can_deposit", False)
        if not can_deposit:
            return False
    
    if "não depositou" in rule_lower:
        deposit_status = snapshot.deposit.get("status", "nenhum")
        if deposit_status in ["confirmado", "pendente"]:
            return False
    
    if "já depositou" in rule_lower:
        deposit_status = snapshot.deposit.get("status", "nenhum") 
        if deposit_status not in ["confirmado", "pendente"]:
            return False
    
    if "depósito confirmado" in rule_lower:
        deposit_status = snapshot.deposit.get("status", "nenhum")
        if deposit_status != "confirmado":
            return False
    
    # Regras de conta
    if "tem conta" in rule_lower and "não tem conta" not in rule_lower:
        accounts = snapshot.accounts
        has_account = any(status not in ["desconhecido", "unknown"] for status in accounts.values())
        if not has_account:
            return False
    
    if "não tem conta" in rule_lower:
        accounts = snapshot.accounts
        has_account = any(status not in ["desconhecido", "unknown"] for status in accounts.values())
        if has_account:
            return False
    
    # Regras de flags
    if "explicado" in rule_lower:
        explained = snapshot.flags.get("explained", False)
        if "não foi explicado" in rule_lower and explained:
            return False
        if "foi explicado" in rule_lower and not explained:
            return False
    
    return True


def convert_automation_to_action(automation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte automação do catálogo para formato de ação.
    
    Args:
        automation: Automação do catálogo
        
    Returns:
        Ação formatada para o plano
    """
    output = automation.get("output", {})
    
    action = {
        "type": output.get("type", "message"),
        "text": output.get("text", ""),
    }
    
    # Adicionar botões se existirem
    buttons = output.get("buttons")
    if buttons:
        action["buttons"] = buttons
    
    # Adicionar tracking se existir
    track = output.get("track")
    if track:
        action["track"] = track
    
    return action


def reload_catalog():
    """Força recarga do catálogo (útil para desenvolvimento)."""
    global _CATALOG_CACHE
    _CATALOG_CACHE = None
    logger.info("Cache do catálogo limpo - será recarregado na próxima consulta")
