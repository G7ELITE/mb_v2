"""
Fallback Knowledge Base - Base de conhecimento de fallback

RAG-lite seguro: busca trechos em policies/kb.md + template.
Sistema simples de busca por palavras-chave e similaridade.
"""
import pathlib
import logging
import re
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher

from app.data.schemas import Env

logger = logging.getLogger(__name__)

# Cache do conteúdo da KB
_KB_CACHE: Optional[List[Dict[str, str]]] = None


async def query_knowledge_base(env: Env) -> Optional[str]:
    """
    Consulta a base de conhecimento para responder dúvidas.
    
    Args:
        env: Ambiente com snapshot e mensagem
        
    Returns:
        Resposta da KB ou None se não encontrou
    """
    if not env.messages_window:
        return None
    
    query = env.messages_window[-1].text
    logger.info(f"Consultando KB para: '{query[:50]}...'")
    
    # Carregar e buscar na KB
    kb_entries = load_knowledge_base()
    
    if not kb_entries:
        logger.warning("KB vazia ou não carregada")
        return None
    
    # Buscar entrada mais relevante
    best_match = find_best_match(query, kb_entries)
    
    if best_match:
        response = best_match["content"]
        logger.info(f"Resposta encontrada na KB (score: {best_match.get('score', 0):.2f})")
        return response
    
    logger.info("Nenhuma resposta relevante encontrada na KB")
    return None


def load_knowledge_base() -> List[Dict[str, str]]:
    """
    Carrega base de conhecimento do arquivo markdown.
    
    Returns:
        Lista de entradas da KB com título e conteúdo
    """
    global _KB_CACHE
    
    if _KB_CACHE is not None:
        return _KB_CACHE
    
    kb_path = pathlib.Path("policies") / "kb.md"
    
    if not kb_path.exists():
        logger.error(f"Arquivo de KB não encontrado: {kb_path}")
        return []
    
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parsear markdown em seções
        _KB_CACHE = parse_markdown_sections(content)
        
        logger.info(f"KB carregada com {len(_KB_CACHE)} entradas")
        return _KB_CACHE
        
    except Exception as e:
        logger.error(f"Erro ao carregar KB: {str(e)}")
        return []


def parse_markdown_sections(content: str) -> List[Dict[str, str]]:
    """
    Parseia markdown em seções baseadas em cabeçalhos.
    
    Args:
        content: Conteúdo markdown
        
    Returns:
        Lista de seções com título e conteúdo
    """
    sections = []
    current_section = {"title": "", "content": ""}
    
    lines = content.split("\n")
    
    for line in lines:
        # Detectar cabeçalho
        if line.startswith("#"):
            # Salvar seção anterior se não vazia
            if current_section["content"].strip():
                sections.append(current_section.copy())
            
            # Iniciar nova seção
            current_section = {
                "title": line.strip("# ").strip(),
                "content": ""
            }
        else:
            # Adicionar linha ao conteúdo da seção atual
            current_section["content"] += line + "\n"
    
    # Adicionar última seção
    if current_section["content"].strip():
        sections.append(current_section)
    
    # Limpar conteúdos
    for section in sections:
        section["content"] = section["content"].strip()
    
    return sections


def find_best_match(query: str, kb_entries: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """
    Encontra a melhor correspondência na KB para a query.
    
    Args:
        query: Pergunta do usuário
        kb_entries: Entradas da base de conhecimento
        
    Returns:
        Melhor correspondência com score ou None
    """
    query_lower = query.lower()
    
    # Extrair palavras-chave da query
    keywords = extract_keywords(query_lower)
    
    if not keywords:
        return None
    
    best_match = None
    best_score = 0.0
    
    for entry in kb_entries:
        score = calculate_relevance_score(keywords, query_lower, entry)
        
        if score > best_score and score > 0.3:  # Threshold mínimo
            best_score = score
            best_match = {
                **entry,
                "score": score
            }
    
    return best_match


def extract_keywords(text: str) -> List[str]:
    """
    Extrai palavras-chave relevantes do texto.
    
    Args:
        text: Texto para análise
        
    Returns:
        Lista de palavras-chave
    """
    # Remover pontuação e dividir em palavras
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filtrar stopwords básicas
    stopwords = {
        "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
        "e", "ou", "mas", "para", "por", "com", "em", "no", "na", "nos", "nas",
        "que", "como", "onde", "quando", "por", "porque", "qual", "quais",
        "é", "são", "foi", "foram", "tem", "ter", "pode", "posso", "consegue",
        "me", "te", "se", "nos", "vocês", "eles", "elas", "isso", "isso",
        "esse", "essa", "este", "esta", "aquele", "aquela"
    }
    
    keywords = [word for word in words if len(word) > 2 and word not in stopwords]
    
    return keywords


def calculate_relevance_score(keywords: List[str], query: str, entry: Dict[str, str]) -> float:
    """
    Calcula score de relevância entre query e entrada da KB.
    
    Args:
        keywords: Palavras-chave extraídas
        query: Query original
        entry: Entrada da KB
        
    Returns:
        Score de relevância (0.0 a 1.0)
    """
    title = entry["title"].lower()
    content = entry["content"].lower()
    combined_text = f"{title} {content}"
    
    score = 0.0
    
    # Score baseado em keywords
    keyword_matches = 0
    for keyword in keywords:
        if keyword in combined_text:
            keyword_matches += 1
            # Peso maior se estiver no título
            if keyword in title:
                score += 0.3
            else:
                score += 0.1
    
    # Bonus por densidade de matches
    if keywords:
        density = keyword_matches / len(keywords)
        score += density * 0.3
    
    # Score baseado em similaridade de sequência
    sequence_similarity = SequenceMatcher(None, query, combined_text).ratio()
    score += sequence_similarity * 0.2
    
    # Normalizar score
    return min(score, 1.0)


def get_kb_sections() -> List[str]:
    """
    Retorna lista de seções disponíveis na KB.
    
    Returns:
        Lista de títulos das seções
    """
    kb_entries = load_knowledge_base()
    return [entry["title"] for entry in kb_entries if entry["title"]]


def search_kb_by_section(section_title: str) -> Optional[str]:
    """
    Busca conteúdo de seção específica da KB.
    
    Args:
        section_title: Título da seção
        
    Returns:
        Conteúdo da seção ou None
    """
    kb_entries = load_knowledge_base()
    
    for entry in kb_entries:
        if entry["title"].lower() == section_title.lower():
            return entry["content"]
    
    return None


def reload_knowledge_base():
    """Força recarga da KB (útil para desenvolvimento)."""
    global _KB_CACHE
    _KB_CACHE = None
    logger.info("Cache da KB limpo - será recarregado na próxima consulta")
