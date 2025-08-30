"""
Snapshot Builder - Construtor determinístico de snapshot do lead

Normaliza evento de entrada, extrai evidências simples (regex/âncoras), 
funde com estado do lead do banco, e NÃO decide. Pode enfileirar jobs para workers.
"""
import re
import logging
from typing import Dict, Any, List, Optional

from app.data.schemas import Env, Lead, Snapshot, Message

logger = logging.getLogger(__name__)

# Regex patterns para extração de evidências
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?[\d\s\-\(\)]{10,}")

# Patterns de ID de corretoras (conforme policy_intake.yml)
NYRION_ID_RE = re.compile(r"\b[0-9]{6,12}\b")
QUOTEX_ID_RE = re.compile(r"\b[a-zA-Z0-9]{6,16}\b")


async def build_snapshot(inbound: Dict[str, Any]) -> Env:
    """
    Constrói snapshot determinístico do estado do lead.
    
    Args:
        inbound: Evento normalizado de entrada
        
    Returns:
        Env: Ambiente completo com lead, snapshot e contexto
    """
    logger.info(f"Construindo snapshot para plataforma: {inbound.get('platform', 'unknown')}")
    
    # Extrair texto da mensagem
    text = inbound.get("message_text", "")
    user_id = inbound.get("user_id", "")
    
    # Extrair candidatos/evidências do texto
    candidates = extract_candidates(text)
    
    # TODO: Buscar lead e perfil do banco de dados
    # Por enquanto, usar dados mock
    lead_data = await get_lead_from_db(user_id, inbound.get("platform", ""))
    
    # Construir janela de mensagens (por ora, apenas a atual)
    messages_window = [
        Message(id=f"msg_{inbound.get('type', 'unknown')}", text=text)
    ]
    
    # Construir snapshot com dados do banco + candidatos
    snapshot = build_lead_snapshot(lead_data, candidates)
    
    # Montar ambiente completo
    env = Env(
        lead=lead_data,
        snapshot=snapshot,
        candidates=candidates,
        messages_window=messages_window,
        apply=True
    )
    
    logger.info(f"Snapshot construído com {len(candidates)} candidatos")
    return env


def extract_candidates(text: str) -> Dict[str, Any]:
    """
    Extrai candidatos/evidências do texto usando regex e âncoras.
    
    Args:
        text: Texto da mensagem para análise
        
    Returns:
        Dicionário com candidatos extraídos
    """
    candidates = {}
    
    if not text:
        return candidates
    
    text_lower = text.lower()
    
    # Extrair emails
    emails = EMAIL_RE.findall(text)
    if emails:
        candidates["email"] = emails[-1]  # Último email encontrado
    
    # Extrair telefones
    phones = PHONE_RE.findall(text)
    if phones:
        candidates["phone"] = phones[-1]
    
    # Detectar possíveis IDs de corretoras
    nyrion_ids = NYRION_ID_RE.findall(text)
    if nyrion_ids:
        candidates["nyrion_id"] = nyrion_ids[-1]
    
    quotex_ids = QUOTEX_ID_RE.findall(text)
    if quotex_ids:
        candidates["quotex_id"] = quotex_ids[-1]
    
    # Detectar intenções simples baseadas em âncoras
    if any(word in text_lower for word in ["quero", "teste", "liberar"]):
        candidates["intent"] = "teste"
    elif any(word in text_lower for word in ["deposito", "depósito", "valor"]):
        candidates["intent"] = "deposito"
    elif any(word in text_lower for word in ["ajuda", "como", "dúvida"]):
        candidates["intent"] = "duvida"
    
    return candidates


async def get_lead_from_db(user_id: str, platform: str) -> Lead:
    """
    Busca dados do lead no banco de dados.
    TODO: Implementar consulta real ao banco.
    
    Args:
        user_id: ID do usuário na plataforma
        platform: Nome da plataforma
        
    Returns:
        Lead: Dados básicos do lead
    """
    # TODO: Implementar consulta real
    # db = get_db()
    # repo = LeadRepository(db)
    # lead = repo.get_by_platform_user_id(f"{platform}:{user_id}")
    
    # Por enquanto, retornar dados mock
    return Lead(
        id=None,
        nome=None,
        lang="pt-BR"
    )


def build_lead_snapshot(lead: Lead, candidates: Dict[str, Any]) -> Snapshot:
    """
    Constrói snapshot do estado atual do lead.
    TODO: Mesclar com dados reais do banco.
    
    Args:
        lead: Dados básicos do lead
        candidates: Candidatos extraídos da mensagem
        
    Returns:
        Snapshot: Estado atual do lead
    """
    # TODO: Buscar dados reais do LeadProfile
    snapshot = Snapshot(
        accounts={
            "quotex": "desconhecido", 
            "nyrion": "desconhecido"
        },
        deposit={
            "status": "nenhum",
            "amount": None,
            "confirmed": False
        },
        agreements={
            "can_deposit": False,
            "wants_test": False
        },
        flags={
            "explained": False,
            "onboarded": False
        },
        history_summary=""
    )
    
    # Enriquecer com candidatos se houver evidências fortes
    if "nyrion_id" in candidates:
        snapshot.accounts["nyrion"] = "candidato"
    if "quotex_id" in candidates:
        snapshot.accounts["quotex"] = "candidato"
    
    if candidates.get("intent") == "teste":
        snapshot.agreements["wants_test"] = True
    
    return snapshot


def coalesce_message_window(lead_id: Optional[int], current_message: str) -> List[Message]:
    """
    Monta janela de mensagens recentes do lead.
    TODO: Implementar busca no histórico.
    
    Args:
        lead_id: ID do lead no banco
        current_message: Mensagem atual
        
    Returns:
        Lista de mensagens na janela de contexto
    """
    # TODO: Buscar mensagens recentes do banco
    # Por enquanto, apenas a mensagem atual
    return [Message(id="current", text=current_message)]
