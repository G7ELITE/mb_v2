"""
API endpoints para gerenciamento de leads
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, and_, func
from datetime import datetime, timedelta
import math

from app.data.models import Lead, LeadProfile, JourneyEvent, ContextoLead
from app.data.repo import LeadRepository, EventRepository
from app.infra.db import get_db

router = APIRouter()


@router.delete("/leads/{lead_id}/session")
async def clear_lead_session(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Limpa a sessão/contexto de um lead específico.
    """
    try:
        from app.core.contexto_lead import get_contexto_lead_service
        
        contexto_service = get_contexto_lead_service()
        
        # Limpar contexto completo
        await contexto_service.atualizar_contexto(
            lead_id=lead_id,
            procedimento_ativo=None,
            etapa_ativa=None,
            aguardando=None,
            ultima_automacao_enviada=None,
            ultimo_topico_kb=None
        )
        
        return {"success": True, "message": f"Sessão do lead {lead_id} limpa com sucesso"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar sessão: {str(e)}")


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove um lead completamente do sistema.
    """
    try:
        lead_repo = LeadRepository(db)
        
        # Verificar se lead existe
        lead = lead_repo.get_by_id(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead não encontrado")
        
        # Deletar eventos relacionados
        event_repo = EventRepository(db)
        db.query(JourneyEvent).filter(JourneyEvent.lead_id == lead_id).delete()
        
        # Deletar perfil e contexto
        db.query(LeadProfile).filter(LeadProfile.lead_id == lead_id).delete()
        db.query(ContextoLead).filter(ContextoLead.lead_id == lead_id).delete()
        
        # Deletar lead
        db.delete(lead)
        db.commit()
        
        return {"success": True, "message": f"Lead {lead_id} removido com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao remover lead: {str(e)}")


@router.get("/leads")
async def list_leads(
    # Busca textual
    q: Optional[str] = Query(None, description="Buscar por nome ou platform_user_id"),
    
    # Filtros de data
    created_from: Optional[datetime] = Query(None, description="Data de criação inicial"),
    created_to: Optional[datetime] = Query(None, description="Data de criação final"),
    last_active_from: Optional[datetime] = Query(None, description="Última atividade inicial"),
    last_active_to: Optional[datetime] = Query(None, description="Última atividade final"),
    
    # Filtros básicos
    channel: Optional[str] = Query(None, description="Canal (telegram, whatsapp)"),
    lang: Optional[str] = Query(None, description="Idioma"),
    
    # Filtros de perfil
    deposit_status: Optional[str] = Query(None, description="Status do depósito"),
    accounts_quotex: Optional[str] = Query(None, description="Status conta Quotex"),
    accounts_nyrion: Optional[str] = Query(None, description="Status conta Nyrion"),
    agreements_can_deposit: Optional[bool] = Query(None, description="Concordou em depositar"),
    agreements_wants_test: Optional[bool] = Query(None, description="Quer testar"),
    
    # Filtros avançados
    tags: Optional[List[str]] = Query(None, description="Tags incluídas"),
    not_tags: Optional[List[str]] = Query(None, description="Tags excluídas"),
    procedure_active: Optional[str] = Query(None, description="Procedimento ativo"),
    procedure_step: Optional[str] = Query(None, description="Passo do procedimento"),
    inactive_gt_hours: Optional[int] = Query(None, description="Inativo há mais de X horas"),
    pending_ops: Optional[bool] = Query(None, description="Tem operações pendentes"),
    
    # Filtros UTM
    utm_source: Optional[str] = Query(None, description="UTM Source"),
    utm_medium: Optional[str] = Query(None, description="UTM Medium"),
    utm_campaign: Optional[str] = Query(None, description="UTM Campaign"),
    utm_content: Optional[str] = Query(None, description="UTM Content"),
    
    # Outros
    mock: Optional[bool] = Query(False, description="Dados mock para teste"),
    min_events_24h: Optional[int] = Query(None, description="Mínimo de eventos em 24h"),
    
    # Paginação e ordenação
    page: int = Query(1, ge=1, description="Página atual"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    sort_by: str = Query("created_at", description="Campo para ordenação"),
    sort_dir: str = Query("desc", regex="^(asc|desc)$", description="Direção da ordenação"),
    
    db: Session = Depends(get_db)
):
    """
    Lista leads com filtros avançados e paginação server-side.
    """
    
    # Se modo mock, retornar dados de exemplo
    if mock:
        return _get_mock_leads_data(page, page_size)
    
    # Construir query base
    query = db.query(Lead).join(LeadProfile, Lead.id == LeadProfile.lead_id, isouter=True)
    
    # Aplicar filtros
    if q:
        query = query.filter(
            or_(
                Lead.name.ilike(f"%{q}%"),
                Lead.platform_user_id.ilike(f"%{q}%")
            )
        )
    
    if created_from:
        query = query.filter(Lead.created_at >= created_from)
    if created_to:
        query = query.filter(Lead.created_at <= created_to)
    
    # Filtros de canal - inferir do platform_user_id
    if channel:
        if channel == "telegram":
            query = query.filter(Lead.platform_user_id.regexp_match(r'^\d+$'))
        elif channel == "whatsapp":
            query = query.filter(Lead.platform_user_id.regexp_match(r'^\+|^\d{10,}'))
    
    if lang:
        query = query.filter(Lead.lang == lang)
    
    # Filtros de perfil (JSON)
    if deposit_status:
        query = query.filter(LeadProfile.deposit['status'].astext == deposit_status)
    if accounts_quotex:
        if accounts_quotex == "com_conta":
            # Filtrar por qualquer valor que não seja None, null, "desconhecido" ou vazio
            query = query.filter(
                and_(
                    LeadProfile.accounts['quotex'].astext.isnot(None),
                    LeadProfile.accounts['quotex'].astext != 'null',
                    LeadProfile.accounts['quotex'].astext != 'desconhecido',
                    LeadProfile.accounts['quotex'].astext != ''
                )
            )
        elif accounts_quotex == "sem_conta":
            # Filtrar por valores que indicam ausência de conta
            query = query.filter(
                or_(
                    LeadProfile.accounts['quotex'].astext.is_(None),
                    LeadProfile.accounts['quotex'].astext == 'null',
                    LeadProfile.accounts['quotex'].astext == 'desconhecido',
                    LeadProfile.accounts['quotex'].astext == ''
                )
            )
        else:
            # Filtro exato para outros valores
            query = query.filter(LeadProfile.accounts['quotex'].astext == accounts_quotex)
    
    if accounts_nyrion:
        if accounts_nyrion == "com_conta":
            query = query.filter(
                and_(
                    LeadProfile.accounts['nyrion'].astext.isnot(None),
                    LeadProfile.accounts['nyrion'].astext != 'null',
                    LeadProfile.accounts['nyrion'].astext != 'desconhecido',
                    LeadProfile.accounts['nyrion'].astext != ''
                )
            )
        elif accounts_nyrion == "sem_conta":
            query = query.filter(
                or_(
                    LeadProfile.accounts['nyrion'].astext.is_(None),
                    LeadProfile.accounts['nyrion'].astext == 'null',
                    LeadProfile.accounts['nyrion'].astext == 'desconhecido',
                    LeadProfile.accounts['nyrion'].astext == ''
                )
            )
        else:
            query = query.filter(LeadProfile.accounts['nyrion'].astext == accounts_nyrion)
    if agreements_can_deposit is not None:
        query = query.filter(LeadProfile.agreements['can_deposit'].astext == str(agreements_can_deposit).lower())
    if agreements_wants_test is not None:
        query = query.filter(LeadProfile.agreements['wants_test'].astext == str(agreements_wants_test).lower())
    
    # Filtros de inatividade
    if inactive_gt_hours:
        cutoff_time = datetime.utcnow() - timedelta(hours=inactive_gt_hours)
        # Subquery para última atividade
        last_event_subq = db.query(
            JourneyEvent.lead_id,
            func.max(JourneyEvent.created_at).label('last_activity')
        ).group_by(JourneyEvent.lead_id).subquery()
        
        query = query.outerjoin(last_event_subq, Lead.id == last_event_subq.c.lead_id)
        query = query.filter(
            or_(
                last_event_subq.c.last_activity < cutoff_time,
                last_event_subq.c.last_activity == None
            )
        )
    
    # Contagem total antes da paginação
    total = query.count()
    
    # Aplicar ordenação
    order_field = getattr(Lead, sort_by, Lead.created_at)
    if sort_dir == "desc":
        query = query.order_by(desc(order_field))
    else:
        query = query.order_by(asc(order_field))
    
    # Aplicar paginação
    offset = (page - 1) * page_size
    leads = query.offset(offset).limit(page_size).all()
    
    # Buscar eventos recentes para cada lead
    lead_ids = [lead.id for lead in leads]
    events_count = {}
    if lead_ids:
        cutoff_24h = datetime.utcnow() - timedelta(hours=24)
        events_count_query = db.query(
            JourneyEvent.lead_id,
            func.count(JourneyEvent.id).label('count')
        ).filter(
            JourneyEvent.lead_id.in_(lead_ids),
            JourneyEvent.created_at >= cutoff_24h
        ).group_by(JourneyEvent.lead_id)
        
        for lead_id, count in events_count_query.all():
            events_count[lead_id] = count
    
    # Serializar resultados
    items = []
    for lead in leads:
        # Buscar perfil e contexto
        profile = lead.lead_profile[0] if hasattr(lead, 'lead_profile') and lead.lead_profile else None
        
        # Inferir canal do platform_user_id
        channel_inferred = "telegram" if lead.platform_user_id.isdigit() else "whatsapp"
        
        item = {
            "id": lead.id,
            "name": lead.name,
            "channel": channel_inferred,
            "platform_user_id": lead.platform_user_id,
            "lang": lead.lang,
            "created_at": lead.created_at.isoformat() if lead.created_at else None,
            "last_activity_at": None,  # TODO: calcular da JourneyEvent
            "events_24h": events_count.get(lead.id, 0),
            "accounts": profile.accounts if profile else {},
            "deposit": profile.deposit if profile else {},
            "agreements": profile.agreements if profile else {},
            "flags": profile.flags if profile else {},
            "tags": profile.flags.get("tags", []) if profile and profile.flags else [],
            "procedure": {
                "active": None,  # TODO: buscar do ContextoLead
                "step": None
            }
        }
        items.append(item)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0
    }


@router.get("/leads/{lead_id}")
async def get_lead_detail(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém detalhes completos de um lead específico.
    """
    
    # Buscar lead
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    # Buscar perfil
    lead_repo = LeadRepository(db)
    profile = lead_repo.get_profile(lead_id)
    
    # Buscar contexto
    contexto = db.query(ContextoLead).filter(ContextoLead.lead_id == lead_id).first()
    
    # Buscar eventos recentes (últimos 20)
    event_repo = EventRepository(db)
    recent_events = db.query(JourneyEvent).filter(
        JourneyEvent.lead_id == lead_id
    ).order_by(desc(JourneyEvent.created_at)).limit(20).all()
    
    # Inferir canal
    channel_inferred = "telegram" if lead.platform_user_id.isdigit() else "whatsapp"
    
    # Serializar eventos
    events = []
    for event in recent_events:
        events.append({
            "id": event.id,
            "event_type": event.type,
            "payload": event.payload,
            "created_at": event.created_at.isoformat() if event.created_at else None
        })
    
    return {
        "id": lead.id,
        "name": lead.name,
        "channel": channel_inferred,
        "platform_user_id": lead.platform_user_id,
        "lang": lead.lang,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "last_activity_at": events[0]["created_at"] if events else None,
        "snapshot": {
            "accounts": profile.accounts if profile else {},
            "deposit": profile.deposit if profile else {},
            "agreements": profile.agreements if profile else {},
            "flags": profile.flags if profile else {},
            "tags": profile.flags.get("tags", []) if profile and profile.flags else []
        },
        "procedure": {
            "active": contexto.procedimento_ativo if contexto else None,
            "step": contexto.etapa_ativa if contexto else None,
            "waiting": contexto.aguardando if contexto else None
        },
        "events_recent": events
    }


def _get_mock_leads_data(page: int, page_size: int) -> Dict[str, Any]:
    """
    Retorna dados mock para desenvolvimento/teste.
    """
    mock_leads = [
        {
            "id": 1,
            "name": "João Silva",
            "channel": "telegram",
            "platform_user_id": "123456789",
            "lang": "pt-BR",
            "created_at": "2024-12-01T10:00:00Z",
            "last_activity_at": "2024-12-15T14:30:00Z",
            "events_24h": 5,
            "accounts": {"quotex": "com_conta", "nyrion": "sem_conta"},
            "deposit": {"status": "pending"},
            "agreements": {"can_deposit": True, "wants_test": True},
            "flags": {"explained": True},
            "tags": ["vip", "ativo"],
            "procedure": {"active": "liberar_teste", "step": "Depósito confirmado"}
        },
        {
            "id": 2,
            "name": "Maria Santos",
            "channel": "telegram", 
            "platform_user_id": "987654321",
            "lang": "pt-BR",
            "created_at": "2024-12-05T15:20:00Z",
            "last_activity_at": "2024-12-14T09:15:00Z",
            "events_24h": 2,
            "accounts": {"quotex": "sem_conta", "nyrion": "desconhecido"},
            "deposit": {"status": "none"},
            "agreements": {"can_deposit": False, "wants_test": True},
            "flags": {"new_user": True},
            "tags": ["novo"],
            "procedure": {"active": "onboarding_completo", "step": "Definir corretora"}
        },
        {
            "id": 3,
            "name": None,
            "channel": "whatsapp",
            "platform_user_id": "+5511999887766",
            "lang": "pt-BR",
            "created_at": "2024-12-10T08:45:00Z",
            "last_activity_at": "2024-12-12T16:20:00Z",
            "events_24h": 0,
            "accounts": {"quotex": "desconhecido", "nyrion": "desconhecido"},
            "deposit": {"status": "none"},
            "agreements": {},
            "flags": {},
            "tags": [],
            "procedure": {"active": None, "step": None}
        }
    ]
    
    # Simular paginação
    total = len(mock_leads)
    start = (page - 1) * page_size
    end = start + page_size
    items = mock_leads[start:end]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0
    }
