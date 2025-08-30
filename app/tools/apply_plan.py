"""
Apply Plan - Aplicador de planos

Aplica planos de ação gerados pelo orchestrador.
Inclui adaptação por canal, envio de mensagens e rastreamento de eventos.
Suporte a idempotência via X-Idempotency-Key.
"""
from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Dict, Any, List, Optional
import logging
import json
from sqlalchemy.orm import Session

from app.data.schemas import Plan, Action
from app.data.repo import IdempotencyRepository, EventRepository
from app.infra.db import get_db
from app.channels.adapter import to_telegram, to_whatsapp
from app.metrics.tracking import track_action_execution
from app.infra.logging import log_structured

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/apply_plan")
async def apply_plan_endpoint(
    plan: Dict[str, Any], 
    x_idempotency_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint público para aplicar plano de ações.
    
    Args:
        plan: Plano de ações a ser executado
        x_idempotency_key: Chave de idempotência opcional
        db: Sessão do banco de dados
        
    Returns:
        Resultado da aplicação do plano
    """
    return await apply_plan(plan, x_idempotency_key, db)


async def apply_plan(
    plan: Dict[str, Any], 
    idempotency_key: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Aplica plano de ações com suporte a idempotência.
    
    Args:
        plan: Plano de ações
        idempotency_key: Chave de idempotência
        db: Sessão do banco (opcional)
        
    Returns:
        Resultado da aplicação
    """
    decision_id = plan.get("decision_id", "unknown")
    actions = plan.get("actions", [])
    
    log_structured("info", "apply_plan_start", {
        "decision_id": decision_id,
        "actions_count": len(actions),
        "has_idempotency": bool(idempotency_key)
    })
    
    # Verificar idempotência se chave fornecida
    if idempotency_key and db:
        cached_response = await check_idempotency(idempotency_key, db)
        if cached_response:
            logger.info(f"Resposta idempotente encontrada para {idempotency_key}")
            return cached_response
    
    try:
        # Executar ações do plano
        execution_results = []
        
        for i, action in enumerate(actions):
            action_result = await execute_action(action, i, decision_id, db)
            execution_results.append(action_result)
        
        # Montar resposta final
        result = {
            "applied": True,
            "decision_id": decision_id,
            "actions_executed": len(execution_results),
            "execution_results": execution_results,
            "status": "success"
        }
        
        # Salvar resposta para idempotência
        if idempotency_key and db:
            await store_idempotency_response(idempotency_key, result, db)
        
        log_structured("info", "apply_plan_success", {
            "decision_id": decision_id,
            "actions_executed": len(execution_results)
        })
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        log_structured("error", "apply_plan_error", {
            "decision_id": decision_id,
            "error": error_msg
        })
        
        error_result = {
            "applied": False,
            "decision_id": decision_id,
            "error": error_msg,
            "status": "error"
        }
        
        # Ainda salvar erro para idempotência
        if idempotency_key and db:
            await store_idempotency_response(idempotency_key, error_result, db)
        
        return error_result


async def execute_action(
    action: Dict[str, Any], 
    action_index: int, 
    decision_id: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Executa uma ação individual do plano.
    
    Args:
        action: Definição da ação
        action_index: Índice da ação no plano
        decision_id: ID da decisão
        db: Sessão do banco
        
    Returns:
        Resultado da execução da ação
    """
    action_type = action.get("type", "unknown")
    action_id = f"{decision_id}_action_{action_index}"
    
    log_structured("info", "action_execution_start", {
        "action_id": action_id,
        "action_type": action_type,
        "decision_id": decision_id
    })
    
    try:
        if action_type == "send_message":
            result = await execute_send_message(action, action_id)
        elif action_type == "send_photo":
            result = await execute_send_media(action, action_id)
        elif action_type == "set_facts":
            result = await execute_set_facts(action, action_id, db)
        elif action_type == "track_event":
            result = await execute_track_event(action, action_id, db)
        else:
            result = await execute_generic_action(action, action_id)
        
        # Rastrear execução da ação
        if db:
            await track_action_execution(action_id, action_type, result, db)
        
        log_structured("info", "action_execution_success", {
            "action_id": action_id,
            "action_type": action_type
        })
        
        return {
            "action_id": action_id,
            "action_type": action_type,
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        error_msg = str(e)
        log_structured("error", "action_execution_error", {
            "action_id": action_id,
            "action_type": action_type,
            "error": error_msg
        })
        
        return {
            "action_id": action_id,
            "action_type": action_type,
            "status": "error",
            "error": error_msg
        }


async def execute_send_message(action: Dict[str, Any], action_id: str) -> Dict[str, Any]:
    """
    Executa ação de envio de mensagem.
    TODO: Implementar envio real via canais.
    
    Args:
        action: Definição da ação
        action_id: ID da ação
        
    Returns:
        Resultado do envio
    """
    text = action.get("text", "")
    buttons = action.get("buttons", [])
    
    # TODO: Determinar canal de destino e adaptar payload
    # Por enquanto, apenas simular envio
    
    # Adaptar para Telegram (exemplo)
    telegram_payload = to_telegram(action)
    
    # TODO: Enviar via API do Telegram
    # response = await telegram_client.send_message(telegram_payload)
    
    # Simular resposta de sucesso
    return {
        "message_sent": True,
        "text_length": len(text),
        "buttons_count": len(buttons),
        "adapted_payload": telegram_payload
    }


async def execute_send_media(action: Dict[str, Any], action_id: str) -> Dict[str, Any]:
    """
    Executa ação de envio de mídia.
    TODO: Implementar envio real de fotos/vídeos.
    
    Args:
        action: Definição da ação
        action_id: ID da ação
        
    Returns:
        Resultado do envio
    """
    media = action.get("media", {})
    caption = action.get("text", "")
    
    # TODO: Implementar envio real de mídia
    
    return {
        "media_sent": True,
        "media_type": media.get("type", "unknown"),
        "caption_length": len(caption)
    }


async def execute_set_facts(
    action: Dict[str, Any], 
    action_id: str, 
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Executa ação de definição de fatos no perfil do lead.
    TODO: Implementar atualização real do perfil.
    
    Args:
        action: Definição da ação
        action_id: ID da ação  
        db: Sessão do banco
        
    Returns:
        Resultado da definição dos fatos
    """
    set_facts = action.get("set_facts", {})
    
    if not set_facts:
        return {"facts_updated": 0}
    
    # TODO: Implementar atualização real do LeadProfile
    # lead_id = extract_lead_id_from_context()
    # repo = LeadRepository(db)
    # repo.update_profile(lead_id, **set_facts)
    
    return {
        "facts_updated": len(set_facts),
        "facts": set_facts
    }


async def execute_track_event(
    action: Dict[str, Any], 
    action_id: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Executa ação de rastreamento de evento.
    
    Args:
        action: Definição da ação
        action_id: ID da ação
        db: Sessão do banco
        
    Returns:
        Resultado do rastreamento
    """
    track = action.get("track", {})
    
    if not track or not db:
        return {"event_tracked": False}
    
    # TODO: Implementar rastreamento real
    # event_repo = EventRepository(db)
    # event_repo.log_event(lead_id, track.get("event"), track)
    
    return {
        "event_tracked": True,
        "event_type": track.get("event", "unknown")
    }


async def execute_generic_action(action: Dict[str, Any], action_id: str) -> Dict[str, Any]:
    """
    Executa ação genérica não reconhecida.
    
    Args:
        action: Definição da ação
        action_id: ID da ação
        
    Returns:
        Resultado da execução
    """
    return {
        "executed": True,
        "note": "Generic action executed as placeholder"
    }


async def check_idempotency(key: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Verifica se já existe resposta para chave de idempotência.
    
    Args:
        key: Chave de idempotência
        db: Sessão do banco
        
    Returns:
        Resposta cacheada ou None
    """
    try:
        idempotency_repo = IdempotencyRepository(db)
        return idempotency_repo.get_response(key)
    except Exception as e:
        logger.warning(f"Erro ao verificar idempotência: {str(e)}")
        return None


async def store_idempotency_response(key: str, response: Dict[str, Any], db: Session):
    """
    Armazena resposta para chave de idempotência.
    
    Args:
        key: Chave de idempotência
        response: Resposta a ser armazenada
        db: Sessão do banco
    """
    try:
        idempotency_repo = IdempotencyRepository(db)
        idempotency_repo.store_response(key, response)
    except Exception as e:
        logger.warning(f"Erro ao armazenar idempotência: {str(e)}")
