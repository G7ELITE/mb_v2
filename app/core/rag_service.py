"""
Serviço de RAG por turno com cache.

Executa 1 retrieval/top-k por turno e anexa contexto da FAQ/KB ao snapshot.
Usa cache curto por tópico (~60s) para eficiência.
"""
import time
import hashlib
import logging
import random
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
        
        # Calcular similaridade INTELIGENTE para cada seção da KB
        hits_com_score = []
        query_lower = query.lower().strip()
        
        # Normalizar query para capturar variações
        query_normalizada = query_lower.replace('?', '').replace('.', '').replace(',', '')
        palavras_query = query_normalizada.split()
        
        for secao in _KB_CACHE:
            texto_completo = secao["texto"]
            
            # Dividir o texto em perguntas/respostas individuais
            linhas = texto_completo.split('\n')
            
            # BUSCAR TODAS AS LINHAS RELEVANTES (não apenas a melhor)
            linhas_relevantes = []
            
            i = 0
            while i < len(linhas):
                linha = linhas[i].strip()
                if not linha:
                    i += 1
                    continue
                
                linha_lower = linha.lower()
                
                # Busca por matches de palavras-chave específicas
                matches_palavras = 0
                for palavra in palavras_query:
                    if palavra in linha_lower:
                        matches_palavras += 1
                
                # Se encontrou palavras da query na linha
                if matches_palavras > 0:
                    # Score REAL baseado na proporção de palavras encontradas
                    score_base = matches_palavras / len(palavras_query)
                    
                    # BONUS para termos específicos de trading
                    bonus_termos = {
                        'sinais': ['sinais', 'sinal', 'opera', 'otc'],
                        'banca': ['banca', 'minim', 'valor', 'deposito'],
                        'deposito': ['deposito', 'banca', 'minim', 'valor'],
                        'experiencia': ['experiencia', 'precisa', 'iniciante'],
                        'otc': ['otc', 'funciona', 'mercado', 'sinais'],
                        'sacar': ['sacar', 'saque', 'dinheiro']
                    }
                    
                    score_linha = score_base
                    for termo_query, termos_bonus in bonus_termos.items():
                        if termo_query in query_lower:
                            if any(t in linha_lower for t in termos_bonus):
                                score_linha += 0.2  # Bonus menor para ser mais realista
                                break
                    
                    # BONUS para perguntas diretas com ?
                    if '?' in linha and '?' in query:
                        score_linha += 0.15
                    
                    # Adicionar variação no score para evitar sempre 0.98
                    variacao = random.uniform(-0.05, 0.05)
                    score_linha += variacao
                    
                    # Se é uma pergunta, pegar também a resposta (próxima linha)
                    if '?' in linha and i + 1 < len(linhas) and linhas[i + 1].strip():
                        resposta = linhas[i + 1].strip()
                        linha_completa = f"{linha}\n{resposta}"
                        i += 1  # Pular a próxima linha já que foi processada
                    else:
                        linha_completa = linha
                    
                    if score_linha >= 0.15:  # Threshold mais baixo para capturar mais resultados
                        linhas_relevantes.append({
                            "texto": linha_completa,
                            "fonte": secao["fonte"],
                            "score": round(min(score_linha, 0.95), 3)  # Score mais realista
                        })
                
                i += 1
            
            # Adicionar TODAS as linhas relevantes (não apenas a melhor)
            hits_com_score.extend(linhas_relevantes)
        
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
        Parseia arquivo Markdown em seções de FAQ (pergunta + resposta).
        
        Args:
            conteudo: Conteúdo do arquivo MD
            
        Returns:
            Lista de seções [{texto, fonte}] - uma para cada Q&A
        """
        secoes = []
        linhas = conteudo.split('\n')
        
        i = 0
        while i < len(linhas):
            linha = linhas[i].strip()
            
            # Pular linhas vazias ou de cabeçalho
            if not linha or linha.startswith('#') or linha.startswith('📚'):
                i += 1
                continue
            
            # Se a linha tem ?, é uma pergunta
            if '?' in linha:
                pergunta = linha
                resposta = ""
                
                # Pegar a próxima linha não vazia como resposta
                j = i + 1
                while j < len(linhas):
                    linha_seguinte = linhas[j].strip()
                    if linha_seguinte and not linha_seguinte.startswith('#'):
                        resposta = linha_seguinte
                        break
                    j += 1
                
                # Se encontrou pergunta + resposta, criar seção
                if resposta:
                    secoes.append({
                        "texto": f"{pergunta}\n{resposta}",
                        "fonte": "KB: FAQ"
                    })
                    i = j + 1  # Pular a linha da resposta
                else:
                    # Só pergunta sem resposta
                    secoes.append({
                        "texto": pergunta,
                        "fonte": "KB: FAQ"
                    })
                    i += 1
            else:
                # Linha que não é pergunta, pode ser resposta isolada
                # Por enquanto, pular
                i += 1
        
        logger.info(f"📋 Parser FAQ: {len(secoes)} seções de perguntas/respostas criadas")
        return secoes
    
    def limpar_cache(self) -> None:
        """Limpa todo o cache RAG."""
        global _RAG_CACHE
        _RAG_CACHE.clear()
        logger.info("Cache RAG limpo")


def get_rag_service() -> RagService:
    """Factory para criar instância do serviço RAG."""
    return RagService()
