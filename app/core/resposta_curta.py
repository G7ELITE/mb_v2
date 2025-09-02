"""
Serviço para entender respostas curtas ('sim/não') via regex e LLM fallback.

Interpreta confirmações por texto usando padrões regex e LLM como fallback
quando a mensagem é ambígua.
"""
import re
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI

from app.data.schemas import ContextoLead, Snapshot, Message, ConfirmacaoCurta
from app.settings import settings

logger = logging.getLogger(__name__)

# Patterns regex para detecção de confirmações
PADRAO_AFIRMACAO = re.compile(r'^\s*(sim|s|ok|claro|consigo|bora|vamos|aceito|concordo|pode|perfeito)\s*$', re.IGNORECASE)
PADRAO_NEGACAO = re.compile(r'^\s*(não|nao|n|agora não|ainda não|nunca|jamais|negativo)\s*$', re.IGNORECASE)

# Timeout para LLM (1.5s)
LLM_TIMEOUT = 1.5

# Template para LLM de confirmação curta
TEMPLATE_CONFIRMACAO_LLM = """
Você recebe uma mensagem curta do usuário e precisa dizer se é AFIRMAÇÃO, NEGAÇÃO ou INCERTO
em relação à pergunta pendente (confirmação). Use o contexto fornecido.
Responda estritamente em JSON.

Contexto:
- Pergunta pendente: {pergunta_pendente}
- Mensagem do usuário: "{mensagem_usuario}"
- Estado da sessão: {estado_sessao}
- Fatos relevantes: {fatos_relevantes}
- Contexto KB: {kb_context}

Se não houver pergunta pendente ou não conseguir determinar, retorne posicao='incerto'.

Responda apenas com JSON no formato:
{{"posicao": "afirmacao|negacao|incerto", "justificativa": "explicação em até 20 palavras"}}
"""


class RespostaCurtaService:
    """Serviço para interpretar respostas curtas."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def interpretar_resposta(
        self,
        mensagem: str,
        contexto_lead: Optional[ContextoLead],
        snapshot: Snapshot,
        messages_window: list[Message]
    ) -> Optional[str]:
        """
        Interpreta uma resposta curta do usuário.
        
        Args:
            mensagem: Texto da mensagem do usuário
            contexto_lead: Contexto persistente do lead
            snapshot: Snapshot atual
            messages_window: Janela de mensagens
            
        Returns:
            'afirmacao', 'negacao' ou None se não for resposta curta/confirmação
        """
        # Verificar se existe estado de aguardando confirmação
        if not contexto_lead or not contexto_lead.aguardando:
            return None
        
        aguardando = contexto_lead.aguardando
        if aguardando.get("tipo") != "confirmacao":
            return None
        
        # Primeiro, tentar regex
        posicao_regex = self._detectar_por_regex(mensagem)
        if posicao_regex:
            logger.info(f"Resposta curta detectada por regex: {posicao_regex}")
            return posicao_regex
        
        # Se não deu match por regex e mensagem é curta/ambígua, usar LLM
        if self._eh_mensagem_curta_ambigua(mensagem):
            logger.info("Mensagem curta ambígua, tentando LLM fallback")
            posicao_llm = await self._interpretar_com_llm(
                mensagem, aguardando, snapshot, messages_window
            )
            return posicao_llm
        
        return None
    
    def _detectar_por_regex(self, mensagem: str) -> Optional[str]:
        """
        Detecta confirmação usando padrões regex.
        
        Args:
            mensagem: Texto da mensagem
            
        Returns:
            'afirmacao', 'negacao' ou None
        """
        mensagem_limpa = mensagem.strip()
        
        if PADRAO_AFIRMACAO.match(mensagem_limpa):
            return "afirmacao"
        elif PADRAO_NEGACAO.match(mensagem_limpa):
            return "negacao"
        
        return None
    
    def _eh_mensagem_curta_ambigua(self, mensagem: str) -> bool:
        """
        Verifica se a mensagem é curta e potencialmente ambígua.
        
        Args:
            mensagem: Texto da mensagem
            
        Returns:
            True se for curta e ambígua
        """
        palavras = mensagem.strip().split()
        return len(palavras) <= 3 and len(mensagem.strip()) <= 20
    
    async def _interpretar_com_llm(
        self,
        mensagem: str,
        aguardando: Dict[str, Any],
        snapshot: Snapshot,
        messages_window: list[Message]
    ) -> Optional[str]:
        """
        Interpreta mensagem usando LLM como fallback.
        
        Args:
            mensagem: Texto da mensagem
            aguardando: Estado de aguardando confirmação
            snapshot: Snapshot atual
            messages_window: Janela de mensagens
            
        Returns:
            'afirmacao', 'negacao' ou None se timeout/erro
        """
        if not self.client:
            logger.warning("Cliente OpenAI não configurado")
            return None
        
        try:
            # Preparar contexto para o LLM
            pergunta_pendente = aguardando.get("origem", "pergunta não especificada")
            estado_sessao = {
                "procedimento_ativo": aguardando.get("procedimento_ativo"),
                "etapa_ativa": aguardando.get("etapa_ativa"),
                "fato_esperado": aguardando.get("fato")
            }
            fatos_relevantes = {
                "agreements": snapshot.agreements,
                "accounts": snapshot.accounts,
                "deposit": snapshot.deposit
            }
            kb_context = snapshot.kb_context or {}
            
            prompt = TEMPLATE_CONFIRMACAO_LLM.format(
                pergunta_pendente=pergunta_pendente,
                mensagem_usuario=mensagem,
                estado_sessao=json.dumps(estado_sessao, ensure_ascii=False),
                fatos_relevantes=json.dumps(fatos_relevantes, ensure_ascii=False),
                kb_context=json.dumps(kb_context, ensure_ascii=False)
            )
            
            # Chamar LLM com timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.1
                ),
                timeout=LLM_TIMEOUT
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Resposta LLM: {content}")
            
            # Parse da resposta JSON
            try:
                result = json.loads(content)
                posicao = result.get("posicao")
                justificativa = result.get("justificativa", "")
                
                if posicao in ["afirmacao", "negacao"]:
                    logger.info(f"LLM detectou: {posicao} - {justificativa}")
                    return posicao
                else:
                    logger.info(f"LLM retornou 'incerto': {justificativa}")
                    return None
                    
            except json.JSONDecodeError:
                logger.warning(f"Resposta LLM não é JSON válido: {content}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout do LLM após {LLM_TIMEOUT}s")
            return None
        except Exception as e:
            logger.error(f"Erro ao chamar LLM: {e}")
            return None


def get_resposta_curta_service() -> RespostaCurtaService:
    """Factory para criar instância do serviço."""
    return RespostaCurtaService()
