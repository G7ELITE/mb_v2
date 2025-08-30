"""
Canal de comunicação WhatsApp Business API
Placeholder para implementação futura
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def webhook():
    """
    Webhook do WhatsApp Business API.
    Placeholder para implementação futura.
    """
    logger.info("Webhook WhatsApp chamado (placeholder)")
    return {"status": "placeholder", "message": "WhatsApp integration not implemented yet"}


@router.get("/info")
async def whatsapp_info():
    """Endpoint de informações do canal WhatsApp."""
    return {
        "channel": "whatsapp",
        "status": "placeholder",
        "implemented": False,
        "note": "Será implementado em versão futura"
    }
