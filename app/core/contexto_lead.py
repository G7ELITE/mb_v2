"""
Serviço para gerenciar contexto persistente do lead entre turnos.

Mantém estado mínimo da sessão com TTL para estados voláteis.
"""
import time
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.data.models import ContextoLead
from app.data.schemas import ContextoLead as ContextoLeadSchema, AguardandoConfirmacao
from app.infra.db import get_db

logger = logging.getLogger(__name__)

# TTL padrão para estados voláteis (30 minutos)
TTL_AGUARDANDO = 30 * 60


class ContextoLeadService:
    """Serviço para gerenciar contexto persistente do lead."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def obter_contexto(self, lead_id: int) -> Optional[ContextoLeadSchema]:
        """
        Obtém o contexto atual do lead, limpando estados expirados.
        
        Args:
            lead_id: ID do lead
            
        Returns:
            Contexto do lead ou None se não existir
        """
        contexto_db = self.db.query(ContextoLead).filter(
            ContextoLead.lead_id == lead_id
        ).first()
        
        if not contexto_db:
            return None
        
        # Verificar se estado 'aguardando' expirou
        aguardando = contexto_db.aguardando
        if aguardando and self._aguardando_expirou(aguardando):
            logger.info(f"Estado 'aguardando' expirado para lead {lead_id}")
            contexto_db.aguardando = None
            self.db.commit()
            aguardando = None
        
        return ContextoLeadSchema(
            lead_id=contexto_db.lead_id,
            procedimento_ativo=contexto_db.procedimento_ativo,
            etapa_ativa=contexto_db.etapa_ativa,
            aguardando=aguardando,
            ultima_automacao_enviada=contexto_db.ultima_automacao_enviada,
            ultimo_topico_kb=contexto_db.ultimo_topico_kb
        )
    
    async def atualizar_contexto(
        self, 
        lead_id: int,
        procedimento_ativo: Optional[str] = None,
        etapa_ativa: Optional[str] = None,
        aguardando: Optional[Dict[str, Any]] = None,
        ultima_automacao_enviada: Optional[str] = None,
        ultimo_topico_kb: Optional[str] = None
    ) -> None:
        """
        Atualiza o contexto do lead.
        
        Args:
            lead_id: ID do lead
            **kwargs: Campos para atualizar (None = manter atual)
        """
        contexto_db = self.db.query(ContextoLead).filter(
            ContextoLead.lead_id == lead_id
        ).first()
        
        if not contexto_db:
            contexto_db = ContextoLead(lead_id=lead_id)
            self.db.add(contexto_db)
        
        # Atualizar apenas campos não-None
        if procedimento_ativo is not None:
            contexto_db.procedimento_ativo = procedimento_ativo
        if etapa_ativa is not None:
            contexto_db.etapa_ativa = etapa_ativa
        if aguardando is not None:
            contexto_db.aguardando = aguardando
        if ultima_automacao_enviada is not None:
            contexto_db.ultima_automacao_enviada = ultima_automacao_enviada
        if ultimo_topico_kb is not None:
            contexto_db.ultimo_topico_kb = ultimo_topico_kb
        
        contexto_db.atualizado_em = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Contexto atualizado para lead {lead_id}")
    
    async def limpar_aguardando(self, lead_id: int) -> None:
        """
        Limpa o estado 'aguardando' do lead.
        
        Args:
            lead_id: ID do lead
        """
        await self.atualizar_contexto(lead_id, aguardando=None)
    
    async def definir_aguardando_confirmacao(
        self, 
        lead_id: int,
        fato: str,
        origem: str,
        ttl_segundos: int = TTL_AGUARDANDO
    ) -> None:
        """
        Define um estado de aguardando confirmação.
        
        Args:
            lead_id: ID do lead
            fato: Qual fato está sendo confirmado
            origem: Última pergunta feita
            ttl_segundos: TTL em segundos
        """
        aguardando = {
            "tipo": "confirmacao",
            "fato": fato,
            "origem": origem,
            "ttl": int(time.time()) + ttl_segundos
        }
        
        await self.atualizar_contexto(lead_id, aguardando=aguardando)
        logger.info(f"Aguardando confirmação definido para lead {lead_id}: {fato}")
    
    def _aguardando_expirou(self, aguardando: Dict[str, Any]) -> bool:
        """
        Verifica se o estado 'aguardando' expirou.
        
        Args:
            aguardando: Dados do estado aguardando
            
        Returns:
            True se expirou
        """
        if not aguardando or "ttl" not in aguardando:
            return False
        
        return int(time.time()) > aguardando["ttl"]
    
    async def adicionar_timeline_expects_reply(self, lead_id: int, entry: Dict[str, Any]) -> None:
        """
        FASE 3: Adiciona entrada no timeline de expects_reply.
        
        Args:
            lead_id: ID do lead
            entry: Entrada do timeline
        """
        contexto_db = self.db.query(ContextoLead).filter(
            ContextoLead.lead_id == lead_id
        ).first()
        
        if not contexto_db:
            contexto_db = ContextoLead(lead_id=lead_id)
            self.db.add(contexto_db)
        
        # Obter timeline atual ou criar novo
        timeline_atual = contexto_db.timeline_expects_reply or []
        
        # Adicionar nova entrada
        timeline_atual.append(entry)
        
        # Manter apenas últimas 10 entradas para não crescer indefinidamente
        if len(timeline_atual) > 10:
            timeline_atual = timeline_atual[-10:]
        
        contexto_db.timeline_expects_reply = timeline_atual
        contexto_db.atualizado_em = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Timeline expects_reply atualizado para lead {lead_id}: {len(timeline_atual)} entradas")
    
    async def obter_timeline_expects_reply(self, lead_id: int) -> Optional[list]:
        """
        FASE 3: Obtém timeline de expects_reply do lead.
        
        Args:
            lead_id: ID do lead
            
        Returns:
            Lista de entradas do timeline ou None
        """
        contexto_db = self.db.query(ContextoLead).filter(
            ContextoLead.lead_id == lead_id
        ).first()
        
        if not contexto_db:
            return None
        
        return contexto_db.timeline_expects_reply or []


def get_contexto_lead_service(db: Session = next(get_db())) -> ContextoLeadService:
    """Factory para criar instância do serviço de contexto."""
    return ContextoLeadService(db)
