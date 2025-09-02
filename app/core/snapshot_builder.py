"""
Snapshot Builder - Construtor determinístico de snapshot do lead

Normaliza evento de entrada, extrai evidências simples (regex/âncoras), 
funde com estado do lead do banco, e NÃO decide. Pode enfileirar jobs para workers.
Implementa merge não-regressivo e RAG por turno.
"""
import re
import logging
from typing import Dict, Any, List, Optional

from app.data.schemas import Env, Lead, Snapshot, Message
from app.core.rag_service import get_rag_service
from app.core.contexto_lead import get_contexto_lead_service

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
    Inclui RAG por turno e merge não-regressivo.
    
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
    
    # Buscar lead e perfil do banco de dados
    lead_data = await get_lead_from_db(user_id, inbound.get("platform", ""))
    
    # Construir janela de mensagens (por ora, apenas a atual)
    messages_window = [
        Message(id=f"msg_{inbound.get('type', 'unknown')}", text=text)
    ]
    
    # Construir snapshot com dados do banco + candidatos (merge não-regressivo)
    snapshot = build_lead_snapshot(lead_data, candidates)
    
    # Executar RAG por turno
    rag_service = get_rag_service()
    kb_context = await rag_service.buscar_contexto_kb(text, top_k=3)
    
    if kb_context:
        snapshot.kb_context = kb_context.dict()
        logger.info(f"RAG: encontrado contexto para tópico '{kb_context.topico}'")
    else:
        logger.info("RAG: nenhum contexto encontrado")
    
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
    Constrói snapshot do estado atual do lead com merge não-regressivo.
    
    Args:
        lead: Dados básicos do lead
        candidates: Candidatos extraídos da mensagem
        
    Returns:
        Snapshot: Estado atual do lead
    """
    # TODO: Buscar dados reais do LeadProfile do banco
    # Por enquanto, usar dados base
    snapshot_existente = Snapshot(
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
    
    # Aplicar merge não-regressivo com candidatos
    snapshot_atualizado = merge_nao_regressivo(snapshot_existente, candidates)
    
    return snapshot_atualizado


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


def merge_nao_regressivo(snapshot_existente: Snapshot, candidates: Dict[str, Any]) -> Snapshot:
    """
    Merge não-regressivo: não rebaixa fatos informativos sem evidência melhor.
    
    Args:
        snapshot_existente: Snapshot atual do lead
        candidates: Novos candidatos/evidências
        
    Returns:
        Snapshot atualizado sem regressão
    """
    # Criar cópia do snapshot existente
    snapshot = Snapshot(
        accounts=snapshot_existente.accounts.copy(),
        deposit=snapshot_existente.deposit.copy(),
        agreements=snapshot_existente.agreements.copy(),
        flags=snapshot_existente.flags.copy(),
        history_summary=snapshot_existente.history_summary,
        kb_context=snapshot_existente.kb_context
    )
    
    # Hierarquia de evidência (mais forte -> mais fraco)
    HIERARQUIA_ACCOUNTS = ["com_conta", "verificado", "candidato", "desconhecido"]
    HIERARQUIA_DEPOSIT = ["confirmado", "pendente", "nenhum"]
    
    # Atualizar contas apenas se evidência for igual ou melhor
    if "nyrion_id" in candidates:
        valor_atual = snapshot.accounts.get("nyrion", "desconhecido")
        novo_valor = "candidato"
        if _evidencia_melhor_ou_igual(novo_valor, valor_atual, HIERARQUIA_ACCOUNTS):
            snapshot.accounts["nyrion"] = novo_valor
    
    if "quotex_id" in candidates:
        valor_atual = snapshot.accounts.get("quotex", "desconhecido")
        novo_valor = "candidato"
        if _evidencia_melhor_ou_igual(novo_valor, valor_atual, HIERARQUIA_ACCOUNTS):
            snapshot.accounts["quotex"] = novo_valor
    
    # Atualizar agreements apenas se evidência positiva
    if candidates.get("intent") == "teste":
        snapshot.agreements["wants_test"] = True  # Sempre atualizar para True se detectado
    
    # Não rebaixar deposit status sem evidência melhor
    if "deposit_evidence" in candidates:
        valor_atual = snapshot.deposit.get("status", "nenhum")
        novo_valor = candidates["deposit_evidence"]
        if _evidencia_melhor_ou_igual(novo_valor, valor_atual, HIERARQUIA_DEPOSIT):
            snapshot.deposit["status"] = novo_valor
    
    return snapshot


def _evidencia_melhor_ou_igual(novo_valor: str, valor_atual: str, hierarquia: List[str]) -> bool:
    """
    Verifica se nova evidência é melhor ou igual à atual.
    
    Args:
        novo_valor: Novo valor proposto
        valor_atual: Valor atual
        hierarquia: Lista ordenada (melhor -> pior)
        
    Returns:
        True se nova evidência é melhor ou igual
    """
    try:
        pos_novo = hierarquia.index(novo_valor)
        pos_atual = hierarquia.index(valor_atual)
        return pos_novo <= pos_atual  # Menor índice = melhor evidência
    except ValueError:
        # Se valor não está na hierarquia, considerar como evidência fraca
        return False
