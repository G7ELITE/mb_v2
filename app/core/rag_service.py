"""
Serviço de RAG por turno com cache.

Executa 1 retrieval/top-k por turno e anexa contexto da FAQ/KB ao snapshot.
Usa cache curto por tópico (~60s) para eficiência.
"""
import time
import hashlib
import logging
from typing import Optional, List, Dict, Any, Tuple
from difflib import SequenceMatcher
import pathlib

from app.data.schemas import KbContext

logger = logging.getLogger(__name__)

# Cache de resultados RAG (tópico -> {resultado, timestamp})
_RAG_CACHE: Dict[str, Dict[str, Any]] = {}

# TTL do cache (60 segundos)
CACHE_TTL = 60

# Cache do conteúdo da KB
_KB_CACHE: Optional[List[Dict[str, str]]] = None

# Arquivo da base de conhecimento
KB_FILE = pathlib.Path(__file__).parent.parent.parent / "policies" / "kb.md"


class RagService:
    """Serviço de RAG com cache por tópico."""
    
    def __init__(self):
        self._carregar_kb()
    
    async def buscar_contexto_kb(
        self, 
        query: str, 
        top_k: int = 3
    ) -> Optional[KbContext]:
        """
        Busca contexto da KB para a query, usando cache quando possível.
        
        Args:
            query: Texto da consulta
            top_k: Número máximo de resultados
            
        Returns:
            Contexto da KB com hits ranqueados
        """
        # Gerar tópico/chave do cache baseado na query
        topico = self._extrair_topico(query)
        
        # Verificar cache
        if self._cache_valido(topico):
            logger.info(f"Cache hit para tópico: {topico}")
            cached_result = _RAG_CACHE[topico]["resultado"]
            return KbContext(**cached_result)
        
        # Cache miss, executar busca
        logger.info(f"Cache miss para tópico: {topico}, executando busca")
        hits = self._buscar_hits(query, top_k)
        
        if not hits:
            return None
        
        contexto = KbContext(hits=hits, topico=topico)
        
        # Salvar no cache
        _RAG_CACHE[topico] = {
            "resultado": contexto.dict(),
            "timestamp": time.time()
        }
        
        logger.info(f"Cached resultado para tópico: {topico}")
        return contexto
    
    def _extrair_topico(self, query: str) -> str:
        """
        Extrai tópico principal da query para usar como chave de cache.
        
        Args:
            query: Texto da consulta
            
        Returns:
            Tópico normalizado
        """
        # Converter para minúsculas e remover acentos/pontuação
        query_limpa = query.lower().strip()
        
        # Palavras-chave principais para tópicos
        topicos_map = {
            "depósito": ["deposito", "depositar", "dinheiro", "valor", "pagar"],
            "conta": ["conta", "cadastro", "registrar", "signup", "criar"],
            "teste": ["teste", "testar", "demo", "trial", "gratuito"],
            "saque": ["saque", "sacar", "retirar", "withdrawl"],
            "quotex": ["quotex"],
            "nyrion": ["nyrion"],
            "otc": ["otc", "opções", "opcoes", "binarias"],
            "suporte": ["ajuda", "suporte", "problema", "erro", "duvida"]
        }
        
        # Encontrar tópico mais relevante
        for topico, palavras in topicos_map.items():
            if any(palavra in query_limpa for palavra in palavras):
                return topico
        
        # Se não encontrou tópico específico, usar hash da query
        return hashlib.md5(query_limpa.encode()).hexdigest()[:8]
    
    def _cache_valido(self, topico: str) -> bool:
        """
        Verifica se o cache para o tópico ainda é válido.
        
        Args:
            topico: Tópico a verificar
            
        Returns:
            True se cache é válido
        """
        if topico not in _RAG_CACHE:
            return False
        
        timestamp = _RAG_CACHE[topico]["timestamp"]
        return (time.time() - timestamp) < CACHE_TTL
    
    def _buscar_hits(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Busca hits na KB usando similaridade textual.
        
        Args:
            query: Texto da consulta
            top_k: Número máximo de resultados
            
        Returns:
            Lista de hits [{texto, fonte, score}]
        """
        if not _KB_CACHE:
            self._carregar_kb()
        
        if not _KB_CACHE:
            logger.warning("KB vazia, não é possível buscar")
            return []
        
        # Calcular similaridade para cada seção da KB
        hits_com_score = []
        query_lower = query.lower()
        
        for secao in _KB_CACHE:
            # Busca por palavra-chave
            texto_lower = secao["texto"].lower()
            palavras_query = set(query_lower.split())
            palavras_texto = set(texto_lower.split())
            
            # Score baseado em palavras em comum + similaridade sequencial
            palavras_comuns = len(palavras_query.intersection(palavras_texto))
            similaridade_seq = SequenceMatcher(None, query_lower, texto_lower).ratio()
            
            # Score combinado (mais peso para palavras em comum)
            score = (palavras_comuns * 0.7) + (similaridade_seq * 0.3)
            
            if score > 0.05:  # Threshold mínimo reduzido
                hits_com_score.append({
                    "texto": secao["texto"],
                    "fonte": secao["fonte"],
                    "score": score
                })
        
        # Ordenar por score e retornar top-k
        hits_ordenados = sorted(hits_com_score, key=lambda x: x["score"], reverse=True)
        return hits_ordenados[:top_k]
    
    def _carregar_kb(self) -> None:
        """Carrega a base de conhecimento do arquivo MD."""
        global _KB_CACHE
        
        if not KB_FILE.exists():
            logger.warning(f"Arquivo KB não encontrado: {KB_FILE}")
            _KB_CACHE = []
            return
        
        try:
            conteudo = KB_FILE.read_text(encoding="utf-8")
            _KB_CACHE = self._parsear_md(conteudo)
            logger.info(f"KB carregada: {len(_KB_CACHE)} seções")
        except Exception as e:
            logger.error(f"Erro ao carregar KB: {e}")
            _KB_CACHE = []
    
    def _parsear_md(self, conteudo: str) -> List[Dict[str, str]]:
        """
        Parseia arquivo Markdown em seções.
        
        Args:
            conteudo: Conteúdo do arquivo MD
            
        Returns:
            Lista de seções [{texto, fonte}]
        """
        secoes = []
        linhas = conteudo.split('\n')
        
        secao_atual = ""
        titulo_atual = "Introdução"
        
        for linha in linhas:
            linha = linha.strip()
            
            # Nova seção (cabeçalho)
            if linha.startswith('#'):
                # Salvar seção anterior se não vazia
                if secao_atual.strip():
                    secoes.append({
                        "texto": secao_atual.strip(),
                        "fonte": f"KB: {titulo_atual}"
                    })
                
                # Iniciar nova seção
                titulo_atual = linha.lstrip('# ').strip()
                secao_atual = ""
            else:
                # Adicionar linha à seção atual
                if linha:  # Ignorar linhas vazias
                    secao_atual += linha + " "
        
        # Adicionar última seção
        if secao_atual.strip():
            secoes.append({
                "texto": secao_atual.strip(),
                "fonte": f"KB: {titulo_atual}"
            })
        
        return secoes
    
    def limpar_cache(self) -> None:
        """Limpa todo o cache RAG."""
        global _RAG_CACHE
        _RAG_CACHE.clear()
        logger.info("Cache RAG limpo")


def get_rag_service() -> RagService:
    """Factory para criar instância do serviço RAG."""
    return RagService()
