"""
Serviço da fila de revisão humana para respostas geradas.

Salva respostas geradas sem automação equivalente para revisão/aprovação humana.
Nunca publica automaticamente no catálogo.
"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.data.models import FilaRevisao as FilaRevisaoDB
from app.data.schemas import FilaRevisaoItem, Snapshot
from app.infra.db import get_db

logger = logging.getLogger(__name__)


class FilaRevisaoService:
    """Serviço para gerenciar fila de revisão humana."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def adicionar_item(
        self,
        lead_id: int,
        pergunta: str,
        resposta: str,
        fontes_kb: Optional[Dict[str, Any]] = None,
        automacao_equivalente: Optional[str] = None,
        pontuacao_similaridade: Optional[float] = None,
        contexto_do_lead: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Adiciona item à fila de revisão humana.
        
        Args:
            lead_id: ID do lead
            pergunta: Pergunta do usuário
            resposta: Resposta gerada
            fontes_kb: Fontes da KB utilizadas
            automacao_equivalente: ID da automação mais similar (se houver)
            pontuacao_similaridade: Score de similaridade
            contexto_do_lead: Contexto completo do lead
            
        Returns:
            ID do item criado
        """
        item_db = FilaRevisaoDB(
            lead_id=lead_id,
            pergunta=pergunta,
            resposta=resposta,
            fontes_kb=fontes_kb,
            automacao_equivalente=automacao_equivalente,
            pontuacao_similaridade=pontuacao_similaridade,
            contexto_do_lead=contexto_do_lead,
            aprovado=False
        )
        
        self.db.add(item_db)
        self.db.commit()
        self.db.refresh(item_db)
        
        logger.info(f"Item adicionado à fila de revisão: {item_db.id} (lead: {lead_id})")
        return item_db.id
    
    async def listar_pendentes(
        self, 
        limite: int = 50,
        offset: int = 0
    ) -> List[FilaRevisaoItem]:
        """
        Lista itens pendentes de revisão.
        
        Args:
            limite: Número máximo de itens
            offset: Offset para paginação
            
        Returns:
            Lista de itens pendentes
        """
        itens_db = (
            self.db.query(FilaRevisaoDB)
            .filter(FilaRevisaoDB.aprovado == False)
            .order_by(FilaRevisaoDB.criado_em.desc())
            .limit(limite)
            .offset(offset)
            .all()
        )
        
        return [self._converter_para_schema(item) for item in itens_db]
    
    async def obter_item(self, item_id: int) -> Optional[FilaRevisaoItem]:
        """
        Obtém item específico da fila.
        
        Args:
            item_id: ID do item
            
        Returns:
            Item ou None se não encontrado
        """
        item_db = self.db.query(FilaRevisaoDB).filter(
            FilaRevisaoDB.id == item_id
        ).first()
        
        if not item_db:
            return None
        
        return self._converter_para_schema(item_db)
    
    async def aprovar_item(
        self, 
        item_id: int,
        resposta_editada: Optional[str] = None
    ) -> bool:
        """
        Aprova item da fila (com possível edição).
        
        Args:
            item_id: ID do item
            resposta_editada: Resposta editada (opcional)
            
        Returns:
            True se aprovado com sucesso
        """
        item_db = self.db.query(FilaRevisaoDB).filter(
            FilaRevisaoDB.id == item_id
        ).first()
        
        if not item_db:
            logger.warning(f"Item {item_id} não encontrado para aprovação")
            return False
        
        # Atualizar resposta se editada
        if resposta_editada:
            item_db.resposta = resposta_editada
        
        item_db.aprovado = True
        self.db.commit()
        
        logger.info(f"Item {item_id} aprovado" + 
                   (" (editado)" if resposta_editada else ""))
        return True
    
    async def rejeitar_item(self, item_id: int) -> bool:
        """
        Remove item da fila (rejeita).
        
        Args:
            item_id: ID do item
            
        Returns:
            True se removido com sucesso
        """
        item_db = self.db.query(FilaRevisaoDB).filter(
            FilaRevisaoDB.id == item_id
        ).first()
        
        if not item_db:
            logger.warning(f"Item {item_id} não encontrado para rejeição")
            return False
        
        self.db.delete(item_db)
        self.db.commit()
        
        logger.info(f"Item {item_id} rejeitado e removido")
        return True
    
    async def obter_estatisticas(self) -> Dict[str, int]:
        """
        Obtém estatísticas da fila de revisão.
        
        Returns:
            Dicionário com estatísticas
        """
        total_pendentes = self.db.query(FilaRevisaoDB).filter(
            FilaRevisaoDB.aprovado == False
        ).count()
        
        total_aprovados = self.db.query(FilaRevisaoDB).filter(
            FilaRevisaoDB.aprovado == True
        ).count()
        
        total_geral = self.db.query(FilaRevisaoDB).count()
        
        return {
            "pendentes": total_pendentes,
            "aprovados": total_aprovados,
            "total": total_geral
        }
    
    def _converter_para_schema(self, item_db: FilaRevisaoDB) -> FilaRevisaoItem:
        """
        Converte modelo DB para schema.
        
        Args:
            item_db: Item do banco
            
        Returns:
            Schema do item
        """
        return FilaRevisaoItem(
            id=item_db.id,
            lead_id=item_db.lead_id,
            pergunta=item_db.pergunta,
            resposta=item_db.resposta,
            fontes_kb=item_db.fontes_kb,
            automacao_equivalente=item_db.automacao_equivalente,
            pontuacao_similaridade=item_db.pontuacao_similaridade,
            contexto_do_lead=item_db.contexto_do_lead,
            aprovado=item_db.aprovado
        )


def get_fila_revisao_service(db: Session = next(get_db())) -> FilaRevisaoService:
    """Factory para criar instância do serviço."""
    return FilaRevisaoService(db)
