"""
Orchestrator - Orquestrador central de decisões

Recebe snapshot enriquecido e decide entre DÚVIDA ou PROCEDIMENTO.
NÃO chama APIs externas, decide apenas pelos fatos do Lead Snapshot.
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging
import uuid

from app.data.schemas import Env, Plan, Action
from app.core.selector import select_automation
from app.core.procedures import run_procedure
from app.core.fallback_kb import query_knowledge_base

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/decide")
async def decide_endpoint(env: Env) -> Plan:
    """
    Endpoint público para decisão do orchestrador.
    
    Args:
        env: Ambiente enriquecido com snapshot do lead
        
    Returns:
        Plan: Plano de ações a serem executadas
    """
    return await decide_and_plan(env)


async def decide_and_plan(env: Env) -> Plan:
    """
    Decisão principal: analisa ambiente e gera plano de resposta.
    
    Args:
        env: Ambiente com lead, snapshot e contexto
        
    Returns:
        Plan: Plano com decision_id e lista de ações
    """
    decision_id = generate_decision_id()
    logger.info(f"Iniciando decisão {decision_id}")
    
    # Classificar tipo de interação
    interaction_type = classify_interaction(env)
    
    plan = Plan(decision_id=decision_id, actions=[])
    
    try:
        if interaction_type == "PROCEDIMENTO":
            # Fluxo de procedimento (funil de passos)
            procedure_plan = await handle_procedure_flow(env)
            plan.actions = procedure_plan.get("actions", [])
            logger.info(f"Decisão {decision_id}: PROCEDIMENTO executado")
            
        elif interaction_type == "DÚVIDA":
            # Fluxo de dúvida (catálogo + KB)
            doubt_plan = await handle_doubt_flow(env)
            plan.actions = doubt_plan.get("actions", [])
            logger.info(f"Decisão {decision_id}: DÚVIDA processada")
            
        else:
            # Fallback genérico
            fallback_plan = await handle_fallback_flow(env)
            plan.actions = fallback_plan.get("actions", [])
            logger.info(f"Decisão {decision_id}: FALLBACK ativado")
    
    except Exception as e:
        logger.error(f"Erro na decisão {decision_id}: {str(e)}")
        plan.actions = [create_error_action()]
    
    plan.metadata = {
        "interaction_type": interaction_type,
        "snapshot_summary": summarize_snapshot(env.snapshot)
    }
    
    logger.info(f"Decisão {decision_id} concluída com {len(plan.actions)} ações")
    return plan


def classify_interaction(env: Env) -> str:
    """
    Classifica o tipo de interação baseado no contexto.
    
    Args:
        env: Ambiente atual
        
    Returns:
        Tipo de interação: PROCEDIMENTO, DÚVIDA ou FALLBACK
    """
    # Analisar mensagem mais recente
    text = ""
    if env.messages_window:
        text = env.messages_window[-1].text.lower()
    
    # Detectar sinais de procedimento ativo
    procedure_signals = [
        "quero", "teste", "liberar", "testar", "começar", 
        "sim", "consigo", "pode", "vamos"
    ]
    
    doubt_signals = [
        "como", "onde", "quando", "que", "dúvida", "ajuda",
        "não entendi", "explicar", "?", "funciona", "faz"
    ]
    
    # Verificar contexto de procedimento ativo
    wants_test = env.snapshot.agreements.get("wants_test", False)
    has_active_agreement = any(env.snapshot.agreements.values())
    
    # Priorizar procedimento se há contexto ativo
    if wants_test or has_active_agreement:
        return "PROCEDIMENTO"
    
    # Verificar sinais na mensagem
    if any(signal in text for signal in procedure_signals):
        return "PROCEDIMENTO"
    
    if any(signal in text for signal in doubt_signals):
        return "DÚVIDA"
    
    # Fallback se não conseguir classificar
    return "FALLBACK"


async def handle_procedure_flow(env: Env) -> Dict[str, Any]:
    """
    Lida com fluxo de procedimento (funil de passos).
    
    Args:
        env: Ambiente atual
        
    Returns:
        Plano de ações do procedimento
    """
    # Determinar qual procedimento executar
    procedure_id = determine_active_procedure(env)
    
    if procedure_id:
        logger.info(f"Executando procedimento: {procedure_id}")
        return await run_procedure(procedure_id, env)
    else:
        # Nenhum procedimento ativo, usar seletor
        logger.info("Nenhum procedimento ativo, usando seletor")
        return await handle_doubt_flow(env)


def determine_active_procedure(env: Env) -> str:
    """
    Determina qual procedimento deve ser executado.
    
    Args:
        env: Ambiente atual
        
    Returns:
        ID do procedimento ou string vazia
    """
    # Verificar se quer teste
    if env.snapshot.agreements.get("wants_test", False):
        return "liberar_teste"
    
    # Verificar outros contextos (futuro)
    # if env.snapshot.agreements.get("wants_deposit_help"):
    #     return "ajuda_deposito"
    
    return ""


async def handle_doubt_flow(env: Env) -> Dict[str, Any]:
    """
    Lida com fluxo de dúvida (catálogo + KB).
    
    Args:
        env: Ambiente atual
        
    Returns:
        Plano de ações para dúvida
    """
    # Primeiro, tentar seletor de automações
    automation = await select_automation(env)
    
    if automation:
        logger.info("Automação selecionada pelo catálogo")
        return {
            "actions": [Action(**automation)]
        }
    
    # Se não encontrou no catálogo, usar KB
    logger.info("Buscando resposta na base de conhecimento")
    kb_response = await query_knowledge_base(env)
    
    if kb_response:
        return {
            "actions": [Action(type="send_message", text=kb_response)]
        }
    
    # Fallback final
    return await handle_fallback_flow(env)


async def handle_fallback_flow(env: Env) -> Dict[str, Any]:
    """
    Fluxo de fallback quando não consegue classificar ou responder.
    
    Args:
        env: Ambiente atual
        
    Returns:
        Plano de ação de fallback
    """
    fallback_messages = [
        "Não entendi bem sua mensagem. Pode me explicar melhor?",
        "Como posso te ajudar hoje?",
        "Precisa de alguma coisa específica?",
    ]
    
    # Escolher mensagem baseada no contexto
    message = fallback_messages[0]
    
    return {
        "actions": [
            Action(
                type="send_message", 
                text=message
            )
        ]
    }


def create_error_action() -> Action:
    """Cria ação de erro padrão."""
    return Action(
        type="send_message",
        text="Ops, tive um problema interno. Tente novamente em alguns instantes."
    )


def generate_decision_id() -> str:
    """Gera ID único para a decisão."""
    return f"dec_{uuid.uuid4().hex[:12]}"


def summarize_snapshot(snapshot) -> Dict[str, Any]:
    """
    Cria resumo do snapshot para metadados.
    
    Args:
        snapshot: Snapshot do lead
        
    Returns:
        Resumo estruturado
    """
    return {
        "accounts_status": dict(snapshot.accounts),
        "deposit_status": snapshot.deposit.get("status", "unknown"),
        "agreements_count": len([k for k, v in snapshot.agreements.items() if v]),
        "flags_count": len([k for k, v in snapshot.flags.items() if v])
    }
