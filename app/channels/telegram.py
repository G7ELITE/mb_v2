"""
Canal de comunicação Telegram
Implementa webhook para receber atualizações do Telegram Bot API
"""
from fastapi import APIRouter, Header, Request, HTTPException
from typing import Dict, Any
import logging
import httpx

from app.settings import settings
from app.channels.adapter import normalize_inbound_event
from app.core.snapshot_builder import build_snapshot
from app.core.intake_agent import run_intake  
from app.core.orchestrator import decide_and_plan
from app.tools.apply_plan import apply_plan
from app.infra.db import SessionLocal
from app.data.repo import LeadRepository, EventRepository

router = APIRouter()
logger = logging.getLogger(__name__)


async def send_telegram_message(chat_id: str, text: str) -> bool:
    """
    Envia mensagem para o usuário via API do Telegram.
    
    Args:
        chat_id: ID do chat do Telegram
        text: Texto da mensagem a ser enviada
        
    Returns:
        True se mensagem foi enviada com sucesso, False caso contrário
    """
    try:
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
            )
            
        if response.status_code == 200:
            logger.info(f"Mensagem enviada com sucesso para chat {chat_id}")
            return True
        else:
            logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Exceção ao enviar mensagem: {str(e)}")
        return False


@router.post("/webhook")
async def webhook(request: Request, secret: str):
    """
    Webhook do Telegram para receber atualizações.
    
    Args:
        request: Request HTTP com update do Telegram
        secret: Secret para validação de webhook
        
    Returns:
        Resposta de confirmação do processamento
    """
    # Validar secret do webhook
    if secret != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning(f"Tentativa de acesso com secret inválido: {secret}")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        # Obter update do Telegram
        update = await request.json()
        logger.info(f"Recebido update do Telegram: {update.get('update_id', 'unknown')}")
        
        # 1) Normalizar update → inbound_event
        inbound = normalize_inbound_event("telegram", update)
        logger.info(f"Evento normalizado: {inbound}")
        
        # Extrair dados da mensagem
        user_id = inbound.get("user_id")
        message_text = inbound.get("message_text", "")
        
        # Obter chat_id do update original
        chat_id = None
        if "message" in update:
            chat_id = str(update["message"]["chat"]["id"])
        elif "callback_query" in update:
            chat_id = str(update["callback_query"]["message"]["chat"]["id"])
            
        if not chat_id:
            logger.error("Não foi possível obter chat_id do update")
            raise HTTPException(status_code=400, detail="Chat ID não encontrado")
        
        # 💾 PERSISTÊNCIA - Gerenciar lead no banco de dados
        db = SessionLocal()
        lead_id = None
        try:
            lead_repo = LeadRepository(db)
            event_repo = EventRepository(db)
            
            # Buscar ou criar lead
            lead = lead_repo.get_by_platform_user_id(chat_id)
            if not lead:
                # Extrair nome se disponível
                user_name = None
                if "message" in update and "from" in update["message"]:
                    user_data = update["message"]["from"]
                    user_name = user_data.get("first_name", "")
                    if user_data.get("last_name"):
                        user_name += f" {user_data['last_name']}"
                
                lead = lead_repo.create_lead(platform_user_id=chat_id, name=user_name)
                logger.info(f"Novo lead criado: ID={lead.id}, chat_id={chat_id}")
            else:
                logger.info(f"Lead existente: ID={lead.id}, chat_id={chat_id}")
            
            # Guardar ID para usar após fechar a sessão
            lead_id = lead.id
            
            # Registrar evento de mensagem recebida
            event_repo.log_event(
                lead_id=lead_id,
                event_type="message_received", 
                payload={
                    "channel": "telegram",
                    "text": message_text,
                    "update_id": update.get("update_id"),
                    "chat_id": chat_id
                }
            )
            
        except Exception as db_error:
            logger.error(f"Erro na persistência: {str(db_error)}")
        finally:
            db.close()
        
        # 🚀 PIPELINE COMPLETO DE AUTOMAÇÕES E PROCEDIMENTOS
        logger.info("🎯 Iniciando pipeline completo de processamento")
        
        try:
            # 2) Construir snapshot base
            logger.info("📊 Construindo snapshot do lead...")
            snapshot_env = await build_snapshot(inbound)
            
            # 3) Intake inteligente (pode executar até 2 tools)
            logger.info("🔍 Executando intake inteligente...")
            enriched_env = await run_intake(snapshot_env)
            
            # 4) Decisão e planejamento
            logger.info("🧠 Executando orquestrador de decisões...")
            plan = await decide_and_plan(enriched_env)
            
            # 5) Aplicar plano de ações
            logger.info(f"⚡ Aplicando plano com {len(plan.actions)} ações...")
            pipeline_result = await apply_plan({
                "decision_id": plan.decision_id,
                "actions": [action.__dict__ if hasattr(action, '__dict__') else action for action in plan.actions]
            })
            
            # Verificar se houve resposta do pipeline
            pipeline_sent_message = False
            final_response = None
            
            if pipeline_result.get("applied") and pipeline_result.get("execution_results"):
                for result in pipeline_result["execution_results"]:
                    # Aceitar tanto "send_message" quanto "message" como tipos de ação de mensagem
                    if (result.get("action_type") in ["send_message", "message"] and 
                        result.get("status") == "success"):
                        # Pipeline preparou mensagem - agora vamos enviar efetivamente
                        message_data = result.get("result", {})
                        if message_data.get("message_sent"):
                            # Extrair texto da mensagem preparada
                            adapted_payload = message_data.get("adapted_payload", {})
                            response_text = ""
                            
                            # Verificar se tem src (estrutura do catálogo)
                            if "src" in adapted_payload:
                                response_text = adapted_payload["src"].get("text", "")
                            else:
                                response_text = adapted_payload.get("text", "")
                            
                            if response_text:
                                # Enviar mensagem efetivamente via API do Telegram
                                sent = await send_telegram_message(chat_id, response_text)
                                if sent:
                                    pipeline_sent_message = True
                                    final_response = response_text
                                    logger.info(f"✅ Mensagem do pipeline enviada com sucesso: {response_text[:50]}...")
                                else:
                                    logger.error("❌ Erro ao enviar mensagem do pipeline")
                            break
            
            # Se pipeline não enviou mensagem, extrair resposta das ações
            if not pipeline_sent_message and plan.actions:
                for action in plan.actions:
                    action_dict = action.__dict__ if hasattr(action, '__dict__') else action
                    # Aceitar tanto "send_message" quanto "message" como tipos de ação
                    if action_dict.get("type") in ["send_message", "message"]:
                        response_text = action_dict.get("text", "")
                        if response_text:
                            # Enviar resposta via nosso método direto
                            sent = await send_telegram_message(chat_id, response_text)
                            pipeline_sent_message = sent
                            final_response = response_text
                            break
            
            # Fallback para garantir resposta
            if not pipeline_sent_message:
                logger.warning("⚠️ Pipeline não gerou resposta - usando fallback")
                if message_text:
                    fallback_text = f"🤖 Olá! Recebi sua mensagem: \"{message_text}\"\n\n✅ O sistema está processando sua solicitação..."
                else:
                    fallback_text = "🤖 Olá! Como posso ajudar você hoje?"
                
                sent = await send_telegram_message(chat_id, fallback_text)
                pipeline_sent_message = sent
                final_response = fallback_text
            
            # 💾 Persistir resultado do pipeline
            try:
                db2 = SessionLocal()
                try:
                    event_repo2 = EventRepository(db2)
                    lead_repo2 = LeadRepository(db2)
                    
                    # Registrar evento de pipeline executado
                    if lead_id:
                        event_repo2.log_event(
                            lead_id=lead_id,
                            event_type="pipeline_executed",
                            payload={
                                "decision_id": plan.decision_id,
                                "actions_count": len(plan.actions),
                                "response_sent": pipeline_sent_message,
                                "final_response": final_response[:200] if final_response else None
                            }
                        )
                    
                    # Atualizar perfil do lead com novos dados descobertos
                    if hasattr(enriched_env, 'snapshot') and enriched_env.snapshot:
                        snapshot = enriched_env.snapshot
                        profile_updates = {}
                        
                        # Atualizar contas se descobertas
                        if hasattr(snapshot, 'accounts') and snapshot.accounts:
                            profile_updates['accounts'] = snapshot.accounts
                        
                        # Atualizar status de depósito se descoberto
                        if hasattr(snapshot, 'deposit') and snapshot.deposit:
                            profile_updates['deposit'] = snapshot.deposit
                        
                        # Aplicar atualizações
                        if profile_updates and lead_id:
                            lead_repo2.update_profile(lead_id, **profile_updates)
                            logger.info(f"Perfil do lead {lead_id} atualizado: {profile_updates}")
                    
                finally:
                    db2.close()
                    
            except Exception as persist_error:
                logger.error(f"Erro ao persistir resultado do pipeline: {str(persist_error)}")
            
            logger.info(f"🎉 Pipeline completo executado - Decisão: {plan.decision_id}")
            return {
                "ok": True,
                "decision_id": plan.decision_id,
                "lead_id": lead_id,
                "result": {
                    "status": "processed",
                    "inbound": inbound,
                    "pipeline_executed": True,
                    "actions_count": len(plan.actions),
                    "response_sent": pipeline_sent_message,
                    "final_response": final_response[:100] + "..." if final_response and len(final_response) > 100 else final_response,
                    "pipeline_result": pipeline_result
                }
            }
            
        except Exception as pipeline_error:
            logger.error(f"❌ Erro no pipeline: {str(pipeline_error)}")
            
            # Fallback em caso de erro
            fallback_text = "🤖 Olá! Tive um pequeno problema técnico, mas estou funcionando. Como posso ajudar?"
            sent = await send_telegram_message(chat_id, fallback_text)
            
            return {
                "ok": True,
                "decision_id": "pipeline_error",
                "result": {
                    "status": "processed_with_error",
                    "inbound": inbound,
                    "pipeline_executed": False,
                    "error": str(pipeline_error),
                    "response_sent": sent,
                    "fallback_used": True
                }
            }
        
    except Exception as e:
        logger.error(f"Erro no processamento do webhook Telegram: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/info")
async def telegram_info():
    """Endpoint de informações do canal Telegram."""
    return {
        "channel": "telegram",
        "status": "active",
        "webhook_configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "env": settings.APP_ENV
    }
