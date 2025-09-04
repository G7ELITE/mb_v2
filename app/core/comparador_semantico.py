"""
Comparador semântico entre respostas geradas e automações candidatas.

Para DÚVIDA, gera resposta com snapshot+kb_context e compara com automações candidatas.
Se similaridade > limiar, prefere automação determinística.
"""
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
from openai import AsyncOpenAI

from app.data.schemas import Snapshot, KbContext
from app.settings import settings

# Importar prompt manager para usar prompt personalizado quando disponível
try:
    from app.core.rag_prompt_manager import get_current_rag_prompt
    USE_CUSTOM_PROMPT = True
except ImportError:
    USE_CUSTOM_PROMPT = False

logger = logging.getLogger(__name__)

# Limiar padrão de similaridade (configurável)
LIMIAR_SIMILARIDADE_DEFAULT = 0.8

# Timeout para geração de resposta (3s)
GERACAO_TIMEOUT = 3.0

# Template para gerar resposta baseada em snapshot + KB
TEMPLATE_GERACAO_RESPOSTA = """
Com base no contexto do lead e na pergunta, gere uma resposta curta e segura.

Contexto do Lead:
- Contas: {accounts}
- Depósitos: {deposit}
- Acordos: {agreements}
- Flags: {flags}

Contexto da KB:
{kb_context}

Pergunta do usuário: "{pergunta}"

Gere uma resposta objetiva, útil e em português brasileiro. Mantenha-a concisa (máximo 2 parágrafos).
Se não houver informação suficiente, seja honesto sobre isso.

Resposta:"""


class ComparadorSemantico:
    """Comparador para determinar equivalência entre resposta gerada e automações."""
    
    def __init__(self, limiar_similaridade: float = LIMIAR_SIMILARIDADE_DEFAULT):
        self.limiar_similaridade = limiar_similaridade
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def comparar_resposta_vs_automacoes(
        self,
        pergunta: str,
        snapshot: Snapshot,
        automacoes_candidatas: List[Dict[str, Any]]
    ) -> Tuple[Optional[str], Optional[str], float]:
        """
        Compara resposta gerada com automações candidatas.
        
        Args:
            pergunta: Pergunta do usuário
            snapshot: Snapshot com contexto
            automacoes_candidatas: Lista de automações elegíveis
            
        Returns:
            Tupla: (resposta_gerada, automacao_escolhida, score_similaridade)
            - Se score >= limiar: automacao_escolhida preenchido
            - Se score < limiar: resposta_gerada preenchido
        """
        # Gerar resposta baseada no contexto
        resposta_gerada = await self._gerar_resposta(pergunta, snapshot)
        
        if not resposta_gerada:
            logger.warning("Falha ao gerar resposta, sem comparação possível")
            return None, None, 0.0
        
        if not automacoes_candidatas:
            logger.info("Nenhuma automação candidata, usando resposta gerada")
            return resposta_gerada, None, 0.0
        
        # Encontrar automação mais similar
        melhor_automacao, melhor_score = self._encontrar_melhor_automacao(
            resposta_gerada, automacoes_candidatas
        )
        
        logger.info(f"Melhor similaridade: {melhor_score:.3f} (limiar: {self.limiar_similaridade})")
        
        if melhor_score >= self.limiar_similaridade:
            logger.info(f"Automação escolhida: {melhor_automacao['id']} (score: {melhor_score:.3f})")
            return None, melhor_automacao["id"], melhor_score
        else:
            logger.info(f"Resposta gerada escolhida (score: {melhor_score:.3f} < {self.limiar_similaridade})")
            return resposta_gerada, None, melhor_score
    
    async def _gerar_resposta(self, pergunta: str, snapshot: Snapshot) -> Optional[str]:
        """
        Gera resposta usando LLM baseado no contexto.
        
        Args:
            pergunta: Pergunta do usuário
            snapshot: Snapshot com contexto
            
        Returns:
            Resposta gerada ou None se erro
        """
        if not self.client:
            logger.warning("Cliente OpenAI não configurado")
            return None
        
        try:
            # Preparar contexto da KB
            kb_text = ""
            if snapshot.kb_context:
                hits = snapshot.kb_context.get("hits", [])
                kb_text = "\n".join([
                    f"- {hit.get('texto', '')[:200]}... (fonte: {hit.get('fonte', 'desconhecida')})"
                    for hit in hits[:3]
                ])
            
            if not kb_text:
                kb_text = "Nenhum contexto da KB disponível."
            
            # Usar prompt personalizado se disponível, senão usar padrão
            if USE_CUSTOM_PROMPT:
                template = get_current_rag_prompt()
            else:
                template = TEMPLATE_GERACAO_RESPOSTA
                
            # Adaptação para novo formato do prompt
            try:
                # Tentar formato novo (histórico + mensagem atual)
                historico_fake = f"Lead: '{pergunta}'"  # Simular histórico básico
                prompt = template.format(
                    historico_mensagens=historico_fake,
                    kb_context=kb_text,
                    mensagem_atual=pergunta
                )
            except KeyError:
                # Fallback para formato antigo (compatibilidade)
                try:
                    prompt = template.format(
                        accounts=json.dumps(snapshot.accounts, ensure_ascii=False),
                        deposit=json.dumps(snapshot.deposit, ensure_ascii=False),
                        agreements=json.dumps(snapshot.agreements, ensure_ascii=False),
                        flags=json.dumps(snapshot.flags, ensure_ascii=False),
                        kb_context=kb_text,
                        pergunta=pergunta
                    )
                except KeyError as e:
                    logger.error(f"Erro na formatação do prompt: {e}")
                    # Fallback simples
                    prompt = f"Baseado na KB: {kb_text}\n\nPergunta: {pergunta}\n\nResponda de forma objetiva:"
            
            # Chamar LLM com timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.3
                ),
                timeout=GERACAO_TIMEOUT
            )
            
            resposta = response.choices[0].message.content.strip()
            logger.info(f"Resposta gerada: {resposta[:100]}...")
            return resposta
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout na geração de resposta após {GERACAO_TIMEOUT}s")
            return None
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return None
    
    def _encontrar_melhor_automacao(
        self,
        resposta_gerada: str,
        automacoes: List[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Encontra a automação mais similar à resposta gerada.
        
        Args:
            resposta_gerada: Texto da resposta gerada
            automacoes: Lista de automações candidatas
            
        Returns:
            Tupla: (melhor_automacao, score)
        """
        melhor_score = 0.0
        melhor_automacao = None
        
        resposta_normalizada = self._normalizar_texto(resposta_gerada)
        
        for automacao in automacoes:
            # Extrair texto da automação
            output = automacao.get("output", {})
            texto_automacao = output.get("text", "")
            
            if not texto_automacao:
                continue
            
            texto_normalizado = self._normalizar_texto(texto_automacao)
            
            # Calcular similaridade semântica
            score = self._calcular_similaridade(resposta_normalizada, texto_normalizado)
            
            logger.debug(f"Automação {automacao.get('id')}: similaridade {score:.3f}")
            
            if score > melhor_score:
                melhor_score = score
                melhor_automacao = automacao
        
        return melhor_automacao, melhor_score
    
    def _normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto para comparação.
        
        Args:
            texto: Texto original
            
        Returns:
            Texto normalizado
        """
        # Converter para minúsculas e remover pontuação extra
        texto_limpo = texto.lower().strip()
        
        # Remover emojis e caracteres especiais (simplificado)
        import re
        texto_limpo = re.sub(r'[^\w\s]', ' ', texto_limpo)
        
        # Normalizar espaços
        texto_limpo = ' '.join(texto_limpo.split())
        
        return texto_limpo
    
    def _calcular_similaridade(self, texto1: str, texto2: str) -> float:
        """
        Calcula similaridade semântica entre dois textos.
        
        Args:
            texto1: Primeiro texto
            texto2: Segundo texto
            
        Returns:
            Score de similaridade (0.0 a 1.0)
        """
        # Similaridade baseada em sequência
        similaridade_seq = SequenceMatcher(None, texto1, texto2).ratio()
        
        # Similaridade baseada em palavras em comum
        palavras1 = set(texto1.split())
        palavras2 = set(texto2.split())
        
        if not palavras1 or not palavras2:
            return similaridade_seq
        
        intersecao = len(palavras1.intersection(palavras2))
        uniao = len(palavras1.union(palavras2))
        similaridade_palavras = intersecao / uniao if uniao > 0 else 0.0
        
        # Score combinado (mais peso para palavras em comum)
        score_final = (similaridade_palavras * 0.6) + (similaridade_seq * 0.4)
        
        return score_final


def get_comparador_semantico(limiar: float = LIMIAR_SIMILARIDADE_DEFAULT) -> ComparadorSemantico:
    """Factory para criar instância do comparador."""
    return ComparadorSemantico(limiar)
