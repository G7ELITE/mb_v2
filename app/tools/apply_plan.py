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
from app.core.config_melhorias import normalizar_action_type, IDEMPOTENCY_HEADER
from app.core.automation_hook import get_automation_hook

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/apply_plan")
async def apply_plan_endpoint(
    plan: Dict[str, Any], 
    x_idempotency_key: Optional[str] = Header(None, alias=IDEMPOTENCY_HEADER),
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
    metadata = plan.get("metadata", {})
    
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
            action_result = await execute_action(action, i, decision_id, db, metadata)
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
    db: Optional[Session] = None,
    metadata: Optional[Dict[str, Any]] = None
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
    action_type_raw = action.get("type", "unknown")
    action_type = normalizar_action_type(action_type_raw)
    action_id = f"{decision_id}_action_{action_index}"
    
    log_structured("info", "action_execution_start", {
        "action_id": action_id,
        "action_type": action_type,
        "action_type_raw": action_type_raw,
        "decision_id": decision_id
    })
    
    try:
        if action_type == "send_message":
            result = await execute_send_message(action, action_id)
        elif action_type == "send_photo":
            result = await execute_send_media(action, action_id)
        elif action_type == "set_facts":
            result = await execute_set_facts(action, action_id, db, metadata)
        elif action_type == "track_event":
            result = await execute_track_event(action, action_id, db)
        elif action_type == "clear_waiting":
            result = await execute_clear_waiting(action, action_id, metadata)
        else:
            result = await execute_generic_action(action, action_id)
        
        # Rastrear execução da ação
        if db:
            await track_action_execution(action_id, action_type, result, db)
        
        # Hook para expects_reply (se for send_message com sucesso)
        if action_type == "send_message" and result.get("message_sent"):
            try:
                automation_hook = get_automation_hook()
                automation_id = action.get("automation_id")
                # Extrair lead_id do metadata do plan
                lead_id = (metadata or {}).get("lead_id")
                logger.info(f"🔧 [ApplyPlan] Calling automation hook: automation_id={automation_id}, lead_id={lead_id}, success={result.get('message_sent')}")
                if automation_id and lead_id:
                    await automation_hook.on_automation_sent(automation_id, lead_id, True)
                else:
                    logger.warning(f"🔧 [ApplyPlan] Missing automation_id ({automation_id}) or lead_id ({lead_id}) for hook")
            except Exception as hook_error:
                logger.warning(f"Automation hook error: {str(hook_error)}")
        
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
    Executa ação de envio de mensagem com blindagem contra nulos.
    Nota: Esta implementação apenas prepara o payload - o envio real é feito no webhook.
    
    Args:
        action: Definição da ação
        action_id: ID da ação
        
    Returns:
        Resultado do envio
    """
    # Blindagem contra nulos - normalizar dados
    action_normalizada = normalizar_action_para_envio(action)
    
    text = action_normalizada.get("text", "")
    buttons = action_normalizada.get("buttons", [])
    media = action_normalizada.get("media", [])
    
    # Adaptar para Telegram
    try:
        telegram_payload = to_telegram(action_normalizada)
    except Exception as e:
        logger.warning(f"Erro ao adaptar payload para Telegram: {str(e)}")
        telegram_payload = {"text": text}
    
    # O envio real será feito pelo webhook que chamou este pipeline
    # Aqui apenas preparamos e validamos o payload
    
    return {
        "message_sent": True,  # Marca como "enviado" para o pipeline
        "text_length": len(text),
        "buttons_count": len(buttons),
        "adapted_payload": telegram_payload,
        "note": "Message prepared for webhook delivery"
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
    db: Optional[Session] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executa ação de definição de fatos no perfil do lead.
    
    Args:
        action: Definição da ação
        action_id: ID da ação  
        db: Sessão do banco
        metadata: Metadata do plano (para obter lead_id)
        
    Returns:
        Resultado da definição dos fatos
    """
    set_facts = action.get("set_facts", {})
    
    if not set_facts:
        return {"facts_updated": 0}
    
    try:
        # Extrair lead_id do metadata
        lead_id = (metadata or {}).get("lead_id")
        if not lead_id or not db:
            logger.warning(f"Missing lead_id ({lead_id}) or db for set_facts")
            return {
                "facts_updated": 0,
                "facts": set_facts,
                "status": "skipped",
                "reason": "missing_lead_id_or_db"
            }
        
        from app.data.repo import LeadRepository
        repo = LeadRepository(db)
        
        # Atualizar perfil com os fatos
        # set_facts pode ter formato "agreements.can_deposit": true
        # então precisamos converter para nested dict
        profile_updates = {}
        for key, value in set_facts.items():
            if "." in key:
                # Converter "agreements.can_deposit" para {"agreements": {"can_deposit": true}}
                parts = key.split(".")
                current = profile_updates
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                profile_updates[key] = value
        
        # Atualizar perfil
        repo.update_profile_facts(lead_id, profile_updates)
        
        logger.info(f"📝 [SetFacts] Updated facts for lead {lead_id}: {set_facts}")
        
        return {
            "facts_updated": len(set_facts),
            "facts": set_facts,
            "status": "success",
            "lead_id": lead_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error setting facts: {error_msg}")
        return {
            "facts_updated": 0,
            "facts": set_facts,
            "status": "error",
            "error": error_msg
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


async def execute_clear_waiting(
    action: Dict[str, Any], 
    action_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Executa ação de limpar estado de aguardando confirmação.
    
    Args:
        action: Definição da ação
        action_id: ID da ação
        metadata: Metadata do plano (para obter lead_id)
        
    Returns:
        Resultado da execução
    """
    try:
        from app.core.contexto_lead import get_contexto_lead_service
        
        lead_id = (metadata or {}).get("lead_id")
        if not lead_id:
            return {
                "status": "error",
                "error": "lead_id not found in metadata"
            }
        
        contexto_service = get_contexto_lead_service()
        await contexto_service.limpar_aguardando(lead_id)
        
        logger.info(f"🧹 [ClearWaiting] Cleared waiting state for lead {lead_id}")
        
        return {
            "status": "success",
            "cleared": True,
            "lead_id": lead_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error clearing waiting state: {error_msg}")
        return {
            "status": "error",
            "error": error_msg
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


def normalizar_action_para_envio(action: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza action para blindar envio contra nulos e botões inválidos.
    
    Args:
        action: Action original
        
    Returns:
        Action normalizada e segura
    """
    # Criar cópia da action
    action_normalizada = action.copy()
    
    # Normalizar campos básicos
    action_normalizada["text"] = action.get("text") or ""
    action_normalizada["buttons"] = action.get("buttons") or []
    action_normalizada["media"] = action.get("media") or []
    
    # Validar e filtrar botões
    buttons_validados = []
    for botao in action_normalizada["buttons"]:
        if not isinstance(botao, dict):
            logger.warning(f"Botão inválido ignorado: {botao}")
            continue
        
        # Validar campos obrigatórios
        if not botao.get("label"):
            logger.warning(f"Botão sem label ignorado: {botao}")
            continue
        
        tipo = botao.get("kind", "callback")
        if tipo not in ["callback", "url", "quick_reply"]:
            logger.warning(f"Tipo de botão inválido '{tipo}', usando 'callback'")
            tipo = "callback"
        
        # Validar URL se necessário
        if tipo == "url" and not botao.get("url"):
            logger.warning(f"Botão URL sem URL ignorado: {botao}")
            continue
        
        # Botão válido
        botao_validado = {
            "id": botao.get("id", f"btn_{len(buttons_validados)}"),
            "label": botao["label"],
            "kind": tipo
        }
        
        # Adicionar campos opcionais se presentes
        if "url" in botao:
            botao_validado["url"] = botao["url"]
        if "set_facts" in botao:
            botao_validado["set_facts"] = botao["set_facts"]
        if "track" in botao:
            botao_validado["track"] = botao["track"]
        
        buttons_validados.append(botao_validado)
    
    action_normalizada["buttons"] = buttons_validados
    
    # Normalizar mídia
    media_validada = []
    for item_media in action_normalizada["media"]:
        if not isinstance(item_media, dict):
            logger.warning(f"Item de mídia inválido ignorado: {item_media}")
            continue
        
        kind = item_media.get("kind")
        url = item_media.get("url")
        
        if not kind or kind not in ["photo", "video", "document"]:
            logger.warning(f"Tipo de mídia inválido ignorado: {kind}")
            continue
        
        if not url:
            logger.warning(f"Item de mídia sem URL ignorado: {item_media}")
            continue
        
        media_validada.append({
            "kind": kind,
            "url": url,
            "caption": item_media.get("caption", "")
        })
    
    action_normalizada["media"] = media_validada
    
    logger.debug(f"Action normalizada: {len(buttons_validados)} botões, {len(media_validada)} mídias")
    return action_normalizada
