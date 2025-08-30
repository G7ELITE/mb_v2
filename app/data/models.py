from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String, JSON, DateTime, func


Base = declarative_base()


class Lead(Base):
    """Modelo para armazenar informações básicas do lead."""
    __tablename__ = "lead"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_user_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    lang: Mapped[str] = mapped_column(String, default="pt-BR")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LeadProfile(Base):
    """Perfil detalhado do lead com contas, depósitos e acordos."""
    __tablename__ = "lead_profile"
    
    lead_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    accounts: Mapped[dict] = mapped_column(JSON)        # {quotex, nyrion}
    deposit: Mapped[dict] = mapped_column(JSON)         # {status}
    agreements: Mapped[dict] = mapped_column(JSON)      # {can_deposit, ...}
    flags: Mapped[dict] = mapped_column(JSON)           # {explained, ...}


class AutomationRun(Base):
    """Registro de execução de automações do catálogo."""
    __tablename__ = "automation_run"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, index=True)
    automation_id: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcedureRun(Base):
    """Registro de execução de procedimentos (funil de passos)."""
    __tablename__ = "procedure_run"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, index=True)
    procedure_id: Mapped[str] = mapped_column(String)
    step: Mapped[str] = mapped_column(String)
    outcome: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JourneyEvent(Base):
    """Eventos da jornada do lead (ledger de ações)."""
    __tablename__ = "journey_event"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, index=True)
    type: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LeadTouchpoint(Base):
    """Pontos de contato do lead para rastreamento UTM."""
    __tablename__ = "lead_touchpoint"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, index=True)
    utm_id: Mapped[str] = mapped_column(String, nullable=True)
    event: Mapped[str] = mapped_column(String)
    ts: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IdempotencyKey(Base):
    """Chaves de idempotência para apply_plan."""
    __tablename__ = "idempotency_key"
    
    key: Mapped[str] = mapped_column(String, primary_key=True)
    response: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
