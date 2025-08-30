"""
Tracking - Sistema de rastreamento de métricas

Rastreia execução de ações, eventos de jornada e métricas de performance.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.data.repo import EventRepository
from app.infra.logging import log_structured

logger = logging.getLogger(__name__)


async def track_action_execution(
    action_id: str, 
    action_type: str, 
    result: Dict[str, Any],
    db: Optional[Session] = None
) -> None:
    """
    Rastreia execução de uma ação.
    
    Args:
        action_id: ID da ação executada
        action_type: Tipo da ação
        result: Resultado da execução
        db: Sessão do banco
    """
    log_structured("info", "action_tracked", {
        "action_id": action_id,
        "action_type": action_type,
        "success": result.get("status") == "success",
        "timestamp": datetime.now().isoformat()
    })
    
    # TODO: Persistir no banco se DB disponível
    if db:
        # event_repo = EventRepository(db)
        # event_repo.log_event(lead_id, "action_executed", {
        #     "action_id": action_id,
        #     "action_type": action_type,
        #     "result": result
        # })
        pass


async def track_decision_made(
    decision_id: str,
    interaction_type: str,
    lead_id: Optional[int] = None,
    db: Optional[Session] = None
) -> None:
    """
    Rastreia decisão tomada pelo orchestrador.
    
    Args:
        decision_id: ID da decisão
        interaction_type: Tipo de interação (DÚVIDA/PROCEDIMENTO)
        lead_id: ID do lead
        db: Sessão do banco
    """
    log_structured("info", "decision_tracked", {
        "decision_id": decision_id,
        "interaction_type": interaction_type,
        "lead_id": lead_id,
        "timestamp": datetime.now().isoformat()
    })


async def track_user_interaction(
    platform: str,
    user_id: str,
    interaction_type: str,
    metadata: Dict[str, Any],
    db: Optional[Session] = None
) -> None:
    """
    Rastreia interação do usuário.
    
    Args:
        platform: Plataforma (telegram, whatsapp)
        user_id: ID do usuário na plataforma
        interaction_type: Tipo de interação
        metadata: Metadados adicionais
        db: Sessão do banco
    """
    log_structured("info", "user_interaction", {
        "platform": platform,
        "user_id": mask_user_id(user_id),
        "interaction_type": interaction_type,
        "metadata": metadata,
        "timestamp": datetime.now().isoformat()
    })


def mask_user_id(user_id: str) -> str:
    """
    Mascara ID do usuário para proteção de PII.
    
    Args:
        user_id: ID original
        
    Returns:
        ID mascarado
    """
    if len(user_id) <= 4:
        return "***"
    
    return f"{user_id[:2]}***{user_id[-2:]}"


def mask_email(email: str) -> str:
    """
    Mascara email para proteção de PII.
    
    Args:
        email: Email original
        
    Returns:
        Email mascarado
    """
    if "@" not in email:
        return "***"
    
    local, domain = email.split("@", 1)
    
    if len(local) <= 2:
        masked_local = "***"
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    
    return f"{masked_local}@{domain}"

