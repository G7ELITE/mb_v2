"""
Canal de comunicação Telegram
Implementa webhook para receber atualizações do Telegram Bot API
"""
from fastapi import APIRouter, Header, Request, HTTPException
from typing import Dict, Any
import logging

from app.settings import settings
from app.channels.adapter import normalize_inbound_event
# from app.core.snapshot_builder import build_snapshot
# from app.core.intake_agent import run_intake  
# from app.core.orchestrator import decide_and_plan
# from app.tools.apply_plan import apply_plan

router = APIRouter()
logger = logging.getLogger(__name__)


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
        
        # TODO: Implementar pipeline completo quando os módulos estiverem prontos
        # 2) snapshot base
        # snapshot_env = await build_snapshot(inbound)
        
        # 3) intake (pode executar até 2 tools)
        # enriched_env = await run_intake(snapshot_env)
        
        # 4) decisão e plano
        # plan = await decide_and_plan(enriched_env)
        
        # 5) aplicar
        # result = await apply_plan(plan)
        
        # Por enquanto, retornar resposta stub
        logger.info("Pipeline de processamento concluído (stub)")
        return {
            "ok": True, 
            "decision_id": "stub_decision",
            "result": {"status": "processed", "inbound": inbound}
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
