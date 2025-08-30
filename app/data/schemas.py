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
