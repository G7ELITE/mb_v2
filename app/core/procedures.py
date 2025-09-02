"""
Procedures - Executor de procedimentos (funil de passos)

Executa funil flexível de procedimentos por passos sem "verificação ativa".
Para no primeiro passo não satisfeito e dispara 1 automação.
"""
import yaml
import pathlib
import logging
from typing import Dict, Any, List, Optional

from app.data.schemas import Env
from app.core.selector import evaluate_eligibility_rule, convert_automation_to_action, load_catalog

logger = logging.getLogger(__name__)

# Cache dos procedimentos carregados
_PROCEDURES_CACHE: Optional[List[Dict[str, Any]]] = None


async def run_procedure(proc_id: str, env: Env) -> Dict[str, Any]:
    """
    Executa procedimento específico contra o snapshot do lead.
    
    Args:
        proc_id: ID do procedimento a ser executado
        env: Ambiente com snapshot do lead
        
    Returns:
        Plano com ações a serem executadas
    """
    logger.info(f"Executando procedimento: {proc_id}")
    
    proc = find_procedure(proc_id)
    if not proc:
        logger.error(f"Procedimento não encontrado: {proc_id}")
        return {"decision_id": "proc_error", "actions": []}
    
    snapshot = env.snapshot
    actions = []
    
    # Avaliar cada passo em ordem
    for i, step in enumerate(proc.get("steps", [])):
        step_name = step.get("name", f"Step {i+1}")
        condition = step.get("condition", "")
        
        logger.info(f"Avaliando passo: {step_name}")
        
        # Verificar se o passo está satisfeito
        if is_step_satisfied(condition, snapshot):
            logger.info(f"Passo satisfeito: {step_name}")
            continue
        
        # Passo não satisfeito - executar ação e parar
        logger.info(f"Passo não satisfeito: {step_name} - executando ação")
        
        step_action = await execute_step_action(step, env)
        if step_action:
            actions.append(step_action)
        
        # Parar no primeiro passo não satisfeito
        break
    
    # Se todos os passos foram satisfeitos, executar ação final
    if not actions and proc.get("steps"):
        final_step = proc["steps"][-1]
        final_action = final_step.get("do")
        
        if final_action:
            logger.info("Todos os passos satisfeitos - executando ação final")
            action = await execute_automation(final_action, env)
            if action:
                # action já contém automation_id via convert_automation_to_action
                actions.append(action)
        else:
            # Procedimento completo sem ação final
            logger.info("Procedimento completo")
            actions.append({
                "type": "send_message",
                "text": "Procedimento concluído com sucesso! ✅"
            })
    
    return {
        "decision_id": f"proc_{proc_id}_{len(actions)}",
        "actions": actions
    }


def find_procedure(proc_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca procedimento por ID.
    
    Args:
        proc_id: ID do procedimento
        
    Returns:
        Definição do procedimento ou None
    """
    procedures = load_procedures()
    
    for proc in procedures:
        if proc.get("id") == proc_id:
            return proc
    
    return None


def load_procedures() -> List[Dict[str, Any]]:
    """
    Carrega procedimentos do arquivo YAML.
    
    Returns:
        Lista de procedimentos
    """
    global _PROCEDURES_CACHE
    
    if _PROCEDURES_CACHE is not None:
        return _PROCEDURES_CACHE
    
    procedures_path = pathlib.Path("policies") / "procedures.yml"
    
    if not procedures_path.exists():
        logger.error(f"Arquivo de procedimentos não encontrado: {procedures_path}")
        return []
    
    try:
        with open(procedures_path, "r", encoding="utf-8") as f:
            _PROCEDURES_CACHE = yaml.safe_load(f) or []
        
        logger.info(f"Procedimentos carregados: {len(_PROCEDURES_CACHE)}")
        return _PROCEDURES_CACHE
        
    except Exception as e:
        logger.error(f"Erro ao carregar procedimentos: {str(e)}")
        return []


def is_step_satisfied(condition: str, snapshot) -> bool:
    """
    Verifica se condição do passo está satisfeita.
    Reutiliza lógica do selector para avaliar regras em PT-BR.
    
    Args:
        condition: Condição em português
        snapshot: Snapshot do lead
        
    Returns:
        True se condição está satisfeita
    """
    if not condition:
        return True  # Sem condição = sempre satisfeito
    
    # Reutilizar avaliador de elegibilidade
    return evaluate_eligibility_rule(condition, snapshot)


async def execute_step_action(step: Dict[str, Any], env: Env) -> Optional[Dict[str, Any]]:
    """
    Executa ação de um passo não satisfeito.
    
    Args:
        step: Definição do passo
        env: Ambiente atual
        
    Returns:
        Ação a ser executada ou None
    """
    if_missing = step.get("if_missing")
    
    if not if_missing:
        return None
    
    # Executar automação especificada
    return await execute_automation(if_missing, env)


async def execute_automation(automation_spec: Dict[str, Any], env: Env) -> Optional[Dict[str, Any]]:
    """
    Executa automação especificada.
    
    Args:
        automation_spec: Especificação da automação
        env: Ambiente atual
        
    Returns:
        Ação resultante ou None
    """
    automation_id = automation_spec.get("automation")
    
    if not automation_id:
        logger.warning("Especificação de automação sem ID")
        return None
    
    # Buscar automação no catálogo
    automation = find_automation_by_id(automation_id)
    
    if automation:
        logger.info(f"Executando automação: {automation_id}")
        return convert_automation_to_action(automation)
    else:
        logger.warning(f"Automação não encontrada no catálogo: {automation_id}")
        return {
            "type": "send_message",
            "text": f"Ação do passo: {automation_id}"
        }


def find_automation_by_id(automation_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca automação no catálogo por ID.
    
    Args:
        automation_id: ID da automação
        
    Returns:
        Automação do catálogo ou None
    """
    catalog = load_catalog()
    
    for automation in catalog:
        if automation.get("id") == automation_id:
            return automation
    
    return None


def reload_procedures():
    """Força recarga dos procedimentos (útil para desenvolvimento)."""
    global _PROCEDURES_CACHE
    _PROCEDURES_CACHE = None
    logger.info("Cache dos procedimentos limpo - será recarregado na próxima consulta")


def get_procedure_status(proc_id: str, snapshot) -> Dict[str, Any]:
    """
    Obtém status de progresso de um procedimento.
    
    Args:
        proc_id: ID do procedimento
        snapshot: Snapshot do lead
        
    Returns:
        Status do procedimento com progresso dos passos
    """
    proc = find_procedure(proc_id)
    
    if not proc:
        return {"error": "Procedimento não encontrado"}
    
    steps_status = []
    completed_steps = 0
    
    for i, step in enumerate(proc.get("steps", [])):
        step_name = step.get("name", f"Step {i+1}")
        condition = step.get("condition", "")
        satisfied = is_step_satisfied(condition, snapshot)
        
        steps_status.append({
            "name": step_name,
            "condition": condition,
            "satisfied": satisfied
        })
        
        if satisfied:
            completed_steps += 1
        else:
            # Parar no primeiro não satisfeito
            break
    
    total_steps = len(proc.get("steps", []))
    progress = completed_steps / total_steps if total_steps > 0 else 0.0
    
    return {
        "procedure_id": proc_id,
        "title": proc.get("title", ""),
        "progress": progress,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "steps_status": steps_status,
        "is_complete": completed_steps == total_steps
    }
