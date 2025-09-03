"""
Orchestrator - Orquestrador central de decisões

Recebe snapshot enriquecido e decide entre DÚVIDA ou PROCEDIMENTO.
NÃO chama APIs externas, decide apenas pelos fatos do Lead Snapshot.
"""
from fastapi import APIRouter
from typing import Dict, Any, Optional
import logging
import uuid

from app.data.schemas import Env, Plan, Action
from app.core.selector import select_automation
from app.core.procedures import run_procedure
from app.core.fallback_kb import query_knowledge_base
from app.core.resposta_curta import get_resposta_curta_service
from app.core.contexto_lead import get_contexto_lead_service
from app.core.comparador_semantico import get_comparador_semantico
from app.core.fila_revisao import get_fila_revisao_service

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
    Inclui verificação de resposta curta e contexto persistente.
    
    Args:
        env: Ambiente com lead, snapshot e contexto
        
    Returns:
        Plan: Plano com decision_id e lista de ações
    """
    decision_id = generate_decision_id()
    logger.info(f"Iniciando decisão {decision_id}")
    
    # Obter contexto persistente do lead
    contexto_service = get_contexto_lead_service()
    contexto_lead = None
    if env.lead.id:
        contexto_lead = await contexto_service.obter_contexto(env.lead.id)
    
    # Verificar se é resposta curta para confirmação pendente
    resposta_curta_service = get_resposta_curta_service()
    mensagem_atual = env.messages_window[-1].text if env.messages_window else ""
    
    posicao_resposta = await resposta_curta_service.interpretar_resposta(
        mensagem_atual, contexto_lead, env.snapshot, env.messages_window
    )
    
    if posicao_resposta:
        # É uma resposta curta (sim/não), processar confirmação
        plan = await handle_confirmacao_curta(env, contexto_lead, posicao_resposta, decision_id)
        logger.info(f"Decisão {decision_id}: CONFIRMAÇÃO_CURTA processada ({posicao_resposta})")
        return plan
    
    # Classificar tipo de interação normal
    interaction_type = classify_interaction(env)
    
    plan = Plan(decision_id=decision_id, actions=[])
    
    try:
        if interaction_type == "PROCEDIMENTO":
            # Fluxo de procedimento (funil de passos)
            procedure_plan = await handle_procedure_flow(env, contexto_lead)
            plan.actions = procedure_plan.get("actions", [])
            logger.info(f"Decisão {decision_id}: PROCEDIMENTO executado")
            
        elif interaction_type == "DÚVIDA":
            # Fluxo de dúvida (catálogo + KB + comparador semântico)
            doubt_plan = await handle_doubt_flow(env, contexto_lead)
            plan.actions = doubt_plan.get("actions", [])
            logger.info(f"Decisão {decision_id}: DÚVIDA processada")
            
        else:
            # Fallback genérico
            fallback_plan = await handle_fallback_flow(env, contexto_lead)
            plan.actions = fallback_plan.get("actions", [])
            logger.info(f"Decisão {decision_id}: FALLBACK ativado")
    
    except Exception as e:
        logger.error(f"Erro na decisão {decision_id}: {str(e)}")
        plan.actions = [create_error_action()]
    
    plan.metadata = {
        "interaction_type": interaction_type,
        "snapshot_summary": summarize_snapshot(env.snapshot),
        "contexto_lead": contexto_lead.dict() if contexto_lead else None,
        "decision_type": determine_decision_type(interaction_type, plan.actions)
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
        "como", "onde", "quando", "que", "qual", "quanto", "dúvida", "ajuda",
        "não entendi", "explicar", "?", "funciona", "faz", "valor", "preciso",
        "posso", "consegue", "saber", "informação"
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


async def handle_procedure_flow(env: Env, contexto_lead=None) -> Dict[str, Any]:
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
        procedure_result = await run_procedure(procedure_id, env)
        
        # BUGFIX: Se procedimento falhou (não encontrado), fazer fallback para DÚVIDA
        if (procedure_result.get("decision_id") == "proc_error" or 
            len(procedure_result.get("actions", [])) == 0):
            logger.warning(f"Procedimento {procedure_id} falhou, fazendo fallback para DÚVIDA")
            return await handle_doubt_flow(env, contexto_lead)
        
        return procedure_result
    else:
        # Nenhum procedimento ativo, usar seletor
        logger.info("Nenhum procedimento ativo, usando seletor")
        return await handle_doubt_flow(env, contexto_lead)


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


async def handle_doubt_flow(env: Env, contexto_lead=None) -> Dict[str, Any]:
    """
    FASE 4: Lida com fluxo de dúvida (catálogo + sinais LLM + KB).
    
    Args:
        env: Ambiente atual
        
    Returns:
        Plano de ações para dúvida
    """
    # Primeiro, tentar seletor de automações do catálogo
    automation = await select_automation(env)
    
    if automation:
        logger.info("Automação selecionada pelo catálogo")
        # Log estruturado para observabilidade
        from app.infra.logging import log_structured
        log_structured("info", "orchestrator_select", {
            "eligible_count": 1, 
            "chosen": automation.get('automation_id', 'unknown'), 
            "used_llm_proposal": False, 
            "reason": "catalog_match"
        })
        return {
            "actions": [Action(**automation)]
        }
    
    # FASE 4 - Se catálogo não encontrou, considerar sinais do Intake LLM
    from app.settings import settings
    if settings.ORCH_ACCEPT_LLM_PROPOSAL and env.snapshot.llm_signals:
        llm_proposal = await try_llm_proposal(env)
        if llm_proposal:
            logger.info(f"Proposta LLM aceita: {llm_proposal.get('automation_id')}")
            # Log estruturado para observabilidade
            from app.infra.logging import log_structured
            log_structured("info", "orchestrator_select", {
                "eligible_count": 0, 
                "chosen": llm_proposal.get('automation_id'), 
                "used_llm_proposal": True, 
                "reason": "llm_proposal_accepted"
            })
            return {
                "actions": [Action(**llm_proposal)]
            }
    
    # Se não encontrou no catálogo e não há proposta LLM válida, usar KB
    logger.info("Buscando resposta na base de conhecimento")
    kb_response = await query_knowledge_base(env)
    
    if kb_response:
        # Log estruturado para observabilidade
        from app.infra.logging import log_structured
        log_structured("info", "orchestrator_select", {
            "eligible_count": 0, 
            "chosen": "kb_response", 
            "used_llm_proposal": False, 
            "reason": "kb_fallback"
        })
        return {
            "actions": [Action(type="send_message", text=kb_response)]
        }
    
    # Fallback final
    from app.infra.logging import log_structured
    log_structured("info", "orchestrator_select", {
        "eligible_count": 0, 
        "chosen": "none", 
        "used_llm_proposal": False, 
        "reason": "final_fallback"
    })
    return await handle_fallback_flow(env, contexto_lead)


async def handle_fallback_flow(env: Env, contexto_lead=None) -> Dict[str, Any]:
    """
    Fluxo de fallback quando não consegue classificar ou responder.
    NOVA LÓGICA: Tenta usar KB antes de fallback genérico.
    
    Args:
        env: Ambiente atual
        contexto_lead: Contexto do lead (opcional)
        
    Returns:
        Plano de ação de fallback
    """
    from app.infra.logging import log_structured
    from app.core.selector import load_catalog
    from app.core.procedures import load_procedures
    
    # Get current message for context
    current_message = ""
    if env.messages_window:
        current_message = env.messages_window[-1].text.lower()
    
    # Check if catalogs are empty
    catalog = load_catalog()
    procedures = load_procedures()
    catalog_empty = len(catalog) == 0
    procedures_empty = len(procedures) == 0
    
    # Check for simple confirmations when no waiting state
    is_simple_confirmation = any(word in current_message for word in [
        "sim", "yes", "não", "no", "ok", "certo", "correto", "exato"
    ])
    
    # NOVA LÓGICA: Se catálogo/procedimentos vazios, tentar KB primeiro
    if catalog_empty and procedures_empty and not is_simple_confirmation and len(current_message.strip()) >= 3:
        logger.info("Catálogo/procedimentos vazios, tentando fallback para KB")
        kb_response = await query_knowledge_base(env)
        if kb_response:
            log_structured("info", "orchestrator_fallback", {
                "reason": "kb_used",
                "catalog_empty": catalog_empty,
                "procedures_empty": procedures_empty,
                "message_length": len(current_message),
                "lead_id": env.lead.id if env.lead else None
            })
            return {
                "actions": [Action(type="send_message", text=kb_response)]
            }
    
    # Handle different fallback scenarios
    message = None
    fallback_reason = "generic"
    
    if catalog_empty and procedures_empty:
        # System has no automations/procedures configured
        message = "🤖 Sistema em configuração inicial. As automações estão sendo preparadas. Tente novamente em breve."
        fallback_reason = "empty_catalog"
        
    elif is_simple_confirmation:
        # User sent a confirmation but there's no active waiting state
        message = "Entendi sua confirmação! Porém, no momento não tenho uma pergunta ativa para você. Como posso te ajudar?"
        fallback_reason = "orphaned_confirmation"
        
    elif current_message and len(current_message.strip()) < 3:
        # Very short message
        message = "Pode me dar um pouco mais de detalhes? Assim posso te ajudar melhor! 😊"
        fallback_reason = "too_short"
        
    else:
        # Generic fallback
        fallback_messages = [
            "Não entendi bem sua mensagem. Pode me explicar melhor?",
            "Como posso te ajudar hoje?",
            "Precisa de alguma coisa específica?",
        ]
        message = fallback_messages[0]
        fallback_reason = "generic"
    
    # Log structured fallback event
    log_structured("info", "orchestrator_fallback", {
        "reason": fallback_reason,
        "catalog_empty": catalog_empty,
        "procedures_empty": procedures_empty,
        "is_simple_confirmation": is_simple_confirmation,
        "message_length": len(current_message),
        "lead_id": env.lead.id if env.lead else None
    })
    
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


async def handle_confirmacao_curta(env: Env, contexto_lead, posicao: str, decision_id: str) -> Plan:
    """
    Processa confirmação curta (sim/não).
    
    Args:
        env: Ambiente atual
        contexto_lead: Contexto persistente do lead
        posicao: 'afirmacao' ou 'negacao'
        decision_id: ID da decisão
        
    Returns:
        Plan: Plano com resposta adequada
    """
    if not contexto_lead or not contexto_lead.aguardando:
        return Plan(decision_id=decision_id, actions=[create_error_action()])
    
    aguardando = contexto_lead.aguardando
    fato = aguardando.get("fato")
    
    # Aplicar confirmação
    if posicao == "afirmacao":
        # TODO: Aplicar set_facts com o fato confirmado
        texto_resposta = "Perfeito! Vamos continuar então."
    else:
        # TODO: Aplicar set_facts com o fato negado
        texto_resposta = "Entendi. Vamos ver outras opções."
    
    # Limpar estado aguardando
    contexto_service = get_contexto_lead_service()
    if env.lead.id:
        await contexto_service.limpar_aguardando(env.lead.id)
    
    return Plan(
        decision_id=decision_id,
        actions=[Action(type="send_message", text=texto_resposta)]
    )


async def try_llm_proposal(env: Env) -> Dict[str, Any]:
    """
    FASE 4: Tenta aceitar uma proposta do Intake LLM com guardrails.
    
    Args:
        env: Ambiente atual
        
    Returns:
        Automação proposta ou None se não válida
    """
    try:
        signals = env.snapshot.llm_signals
        propose_automations = signals.get('propose_automations', [])
        
        if not propose_automations:
            return None
        
        # Aceitar no máximo 1 proposta válida
        for automation_id in propose_automations[:1]:  # Só primeira proposta
            # Validar proposta com guardrails
            if await is_proposal_valid(automation_id, env):
                # Carregar configuração da automação do catálogo
                automation_config = await load_automation_from_catalog(automation_id)
                if automation_config:
                    # Converter para formato de ação
                    return convert_automation_config_to_action(automation_config)
        
        # Se chegou aqui, nenhuma proposta válida
        logger.info(f"{{'event':'orchestrator_select', 'eligible_count':0, 'chosen':'none', 'used_llm_proposal':False, 'reason':'proposal_rejected', 'proposals':{propose_automations}}}")
        return None
        
    except Exception as e:
        logger.warning(f"Erro ao processar proposta LLM: {e}")
        return None


async def is_proposal_valid(automation_id: str, env: Env) -> bool:
    """
    FASE 4: Valida se uma proposta LLM é aceitável com guardrails.
    
    Args:
        automation_id: ID da automação proposta
        env: Ambiente atual
        
    Returns:
        True se a proposta é válida
    """
    try:
        # Verificar se existe no catálogo
        automation_config = await load_automation_from_catalog(automation_id)
        if not automation_config:
            logger.info(f"Proposta rejeitada - não existe no catálogo: {automation_id}")
            return False
        
        # Verificar eligibilidade com fatos duros (reutilizar lógica do selector)
        from app.core.selector import is_automation_applicable
        if not await is_automation_applicable(automation_config, env):
            logger.info(f"Proposta rejeitada - não aplicável: {automation_id}")
            return False
        
        # Verificar cooldown
        if not await check_automation_cooldown(automation_id, env.lead.id):
            logger.info(f"Proposta rejeitada - cooldown ativo: {automation_id}")
            return False
        
        logger.info(f"Proposta aceita - guardrails OK: {automation_id}")
        return True
        
    except Exception as e:
        logger.warning(f"Erro ao validar proposta {automation_id}: {e}")
        return False


async def load_automation_from_catalog(automation_id: str) -> Optional[Dict[str, Any]]:
    """
    FASE 4: Carrega configuração de automação do catálogo YAML.
    
    Args:
        automation_id: ID da automação
        
    Returns:
        Configuração da automação ou None
    """
    try:
        import yaml
        import os
        
        catalog_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "policies", "catalog.yml"
        )
        
        if os.path.exists(catalog_path):
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog_list = yaml.safe_load(f) or []
                
            # Buscar automação por ID
            for automation in catalog_list:
                if automation.get("id") == automation_id:
                    return automation
                    
        return None
        
    except Exception as e:
        logger.error(f"Erro ao carregar automação do catálogo: {e}")
        return None


def convert_automation_config_to_action(automation_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    FASE 4: Converte configuração YAML para formato de ação.
    
    Args:
        automation_config: Configuração da automação
        
    Returns:
        Ação formatada
    """
    # Reutilizar lógica do selector
    from app.core.selector import convert_automation_to_action
    return convert_automation_to_action(automation_config)


async def check_automation_cooldown(automation_id: str, lead_id: int) -> bool:
    """
    FASE 4: Verifica se automação não está em cooldown.
    
    Args:
        automation_id: ID da automação
        lead_id: ID do lead
        
    Returns:
        True se pode executar (não em cooldown)
    """
    try:
        # Reutilizar lógica do selector se existir
        from app.core.selector import check_cooldown
        return await check_cooldown(automation_id, lead_id)
        
    except ImportError:
        # Se não existe, assumir que pode executar
        logger.info(f"Cooldown check não implementado - assumindo OK para {automation_id}")
        return True
    except Exception as e:
        logger.warning(f"Erro ao verificar cooldown: {e}")
        return True


def determine_decision_type(interaction_type: str, actions: list) -> str:
    """
    Determina o tipo de decisão baseado no fluxo seguido.
    
    Args:
        interaction_type: Tipo de interação
        actions: Lista de ações executadas
        
    Returns:
        Tipo de decisão para telemetria
    """
    if interaction_type == "PROCEDIMENTO":
        return "PROCEDIMENTO"
    elif interaction_type == "DÚVIDA":
        # Verificar se usou automação ou resposta gerada
        for action in actions:
            if action.type == "send_message":
                # TODO: Melhorar detecção baseada em metadata da action
                return "CATALOGO"  # Por enquanto, assumir catálogo
        return "RAG"
    else:
        return "KB_FALLBACK"
