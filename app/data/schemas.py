from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class Message(BaseModel):
    """Schema para mensagens na janela de contexto."""
    id: str
    text: str


class Snapshot(BaseModel):
    """Schema para snapshot do estado do lead."""
    accounts: Dict[str, str] = Field(default_factory=dict)
    deposit: Dict[str, Any] = Field(default_factory=dict)
    agreements: Dict[str, Any] = Field(default_factory=dict)
    flags: Dict[str, Any] = Field(default_factory=dict)
    history_summary: str = ""
    kb_context: Optional[Dict[str, Any]] = None  # {hits: [{texto, fonte, score}], topico}
    llm_signals: Dict[str, Any] = Field(default_factory=dict)  # Sinais do LLM para Fase 4


class Lead(BaseModel):
    """Schema para informações básicas do lead."""
    id: Optional[int] = None
    nome: Optional[str] = None
    lang: str = "pt-BR"


class Env(BaseModel):
    """Schema para o ambiente completo passado ao orchestrador."""
    lead: Lead
    snapshot: Snapshot
    candidates: Dict[str, Any] = Field(default_factory=dict)
    messages_window: List[Message]
    apply: bool = True


class Action(BaseModel):
    """Schema para ações no plano de resposta."""
    type: str
    text: Optional[str] = None
    buttons: Optional[list] = None
    url: Optional[str] = None
    media: Optional[Dict[str, Any]] = None
    track: Optional[Dict[str, Any]] = None
    set_facts: Optional[Dict[str, Any]] = None
    automation_id: Optional[str] = None  # FASE 4: ID da automação que gerou a ação


class Plan(BaseModel):
    """Schema para o plano de resposta do orchestrador."""
    decision_id: str
    actions: List[Action] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class TelegramUpdate(BaseModel):
    """Schema básico para updates do Telegram."""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None


class ContextoLead(BaseModel):
    """Schema para contexto persistente do lead."""
    lead_id: int
    procedimento_ativo: Optional[str] = None
    etapa_ativa: Optional[str] = None
    aguardando: Optional[Dict[str, Any]] = None
    ultima_automacao_enviada: Optional[str] = None
    ultimo_topico_kb: Optional[str] = None


class AguardandoConfirmacao(BaseModel):
    """Schema para estado de aguardando confirmação."""
    tipo: str  # 'confirmacao'
    fato: str  # qual fato está sendo confirmado
    origem: str  # última pergunta feita
    ttl: int  # timestamp de expiração


class KbContext(BaseModel):
    """Schema para contexto da KB anexado ao snapshot."""
    hits: List[Dict[str, Any]]  # [{texto, fonte, score}]
    topico: str
    
    def build_context_string(self) -> str:
        """
        Constrói string de contexto a partir dos hits.
        
        Returns:
            String formatada com o contexto dos hits encontrados
        """
        if not self.hits:
            return "Nenhuma informação relevante encontrada na base de conhecimento."
        
        context_parts = []
        for i, hit in enumerate(self.hits, 1):
            texto = hit.get("texto", "")
            fonte = hit.get("fonte", "Desconhecida")
            score = hit.get("score", 0.0)
            
            # Formatação mais limpa para o contexto com índice e score
            context_parts.append(f"**{i}. {fonte} (Score: {score:.3f})**: {texto}")
        
        context_string = "\n\n".join(context_parts)
        
        # Log para debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🎯 CONTEXTO CONSTRUÍDO: {len(self.hits)} hits incluídos no contexto")
        for i, hit in enumerate(self.hits, 1):
            logger.info(f"   Hit {i}: Score {hit.get('score', 0):.3f} - {hit.get('texto', '')[:100]}...")
        
        return context_string


class FilaRevisaoItem(BaseModel):
    """Schema para item na fila de revisão humana."""
    id: Optional[int] = None
    lead_id: int
    pergunta: str
    resposta: str
    fontes_kb: Optional[Dict[str, Any]] = None
    automacao_equivalente: Optional[str] = None
    pontuacao_similaridade: Optional[float] = None
    contexto_do_lead: Optional[Dict[str, Any]] = None
    aprovado: bool = False


class ConfirmacaoCurta(BaseModel):
    """Schema para resposta de LLM sobre confirmação curta."""
    posicao: str  # 'afirmacao' | 'negacao' | 'incerto'
    justificativa: str
