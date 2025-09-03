"""
Repository helpers para persistência.
Implementará operações CRUD e queries específicas conforme necessário.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.data.models import Lead, LeadProfile, JourneyEvent, IdempotencyKey


class LeadRepository:
    """Repository para operações relacionadas ao Lead."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_platform_user_id(self, platform_user_id: str) -> Optional[Lead]:
        """Busca lead por platform_user_id."""
        return self.db.query(Lead).filter(Lead.platform_user_id == platform_user_id).first()
    
    def get_by_id(self, lead_id: int) -> Optional[Lead]:
        """Busca lead por ID."""
        return self.db.query(Lead).filter(Lead.id == lead_id).first()
    
    def create_lead(self, platform_user_id: str, name: Optional[str] = None, lang: str = "pt-BR") -> Lead:
        """Cria um novo lead."""
        lead = Lead(platform_user_id=platform_user_id, name=name, lang=lang)
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead
    
    def get_profile(self, lead_id: int) -> Optional[LeadProfile]:
        """Busca perfil do lead."""
        return self.db.query(LeadProfile).filter(LeadProfile.lead_id == lead_id).first()
    
    def update_profile(self, lead_id: int, **kwargs) -> None:
        """Atualiza perfil do lead."""
        profile = self.get_profile(lead_id)
        if not profile:
            # Criar perfil se não existir
            profile = LeadProfile(
                lead_id=lead_id,
                accounts={},
                deposit={},
                agreements={},
                flags={}
            )
            self.db.add(profile)
        
        # Atualizar campos fornecidos
        for field, value in kwargs.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        self.db.commit()


class IdempotencyRepository:
    """Repository para chaves de idempotência."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_response(self, key: str) -> Optional[Dict[str, Any]]:
        """Busca resposta cacheada por chave de idempotência."""
        record = self.db.query(IdempotencyKey).filter(IdempotencyKey.key == key).first()
        return record.response if record else None
    
    def store_response(self, key: str, response: Dict[str, Any]) -> None:
        """Armazena resposta para chave de idempotência."""
        record = IdempotencyKey(key=key, response=response)
        self.db.add(record)
        self.db.commit()


class EventRepository:
    """Repository para eventos da jornada."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(self, lead_id: int, event_type: str, payload: Dict[str, Any]) -> None:
        """Registra evento na jornada do lead."""
        event = JourneyEvent(lead_id=lead_id, type=event_type, payload=payload)
        self.db.add(event)
        self.db.commit()
