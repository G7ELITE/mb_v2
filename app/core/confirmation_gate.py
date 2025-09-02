"""
Confirmation Gate - Gate de confirmação LLM-first com guardrails

Implementa confirmação inteligente usando LLM com fallback determinístico.
Integra no pipeline antes do orchestrator para interceptar confirmações.
"""
import time
import logging
import yaml
import os
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI

from app.data.schemas import Env, Action, Plan
from app.core.contexto_lead import get_contexto_lead_service
from app.settings import settings

logger = logging.getLogger(__name__)

# Carregamento do store de targets será implementado
_confirm_targets_cache = None
_confirm_targets_whitelist = set()


class ConfirmationResult:
    """Resultado de uma tentativa de confirmação."""
    
    def __init__(self, handled: bool = False, actions: List[Action] = None,
                 target: Optional[str] = None, polarity: Optional[str] = None,
                 confidence: float = 0.0, source: str = "none", reason: str = ""):
        self.handled = handled
        self.actions = actions or []  # Lista de ações a serem executadas
        self.target = target
        self.polarity = polarity  # 'yes' | 'no' | 'unknown'
        self.confidence = confidence
        self.source = source  # 'llm' | 'fallback' | 'none'
        self.reason = reason


class ConfirmationGate:
    """
    Gate de confirmação LLM-first que intercepta mensagens antes do orchestrator.
    """
    
    def __init__(self):
        self.contexto_service = get_contexto_lead_service()
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def process_message(self, env: Env) -> ConfirmationResult:
        """
        Processa mensagem verificando se é uma confirmação.
        
        Args:
            env: Ambiente com mensagem e contexto
            
        Returns:
            ConfirmationResult: Resultado do processamento
        """
        start_time = time.time()
        
        # Verificar se tem contexto de aguardando
        contexto_lead = None
        if env.lead.id:
            contexto_lead = await self.contexto_service.obter_contexto(env.lead.id)
        
        pending_confirmations = await self._get_pending_confirmations(contexto_lead, env)
        
        if not pending_confirmations:
            return ConfirmationResult(handled=False, reason="no_pending_confirmations")
        
        # Extrair mensagem atual
        current_message = ""
        if env.messages_window:
            current_message = env.messages_window[-1].text
        
        if not current_message:
            return ConfirmationResult(handled=False, reason="empty_message")
        
        # Tentar LLM primeiro se habilitado
        if settings.CONFIRM_AGENT_MODE in ["llm_first", "hybrid"] and self.openai_client:
            try:
                llm_result = await self._try_llm_confirmation(
                    current_message, env.messages_window, pending_confirmations, env.snapshot
                )
                
                if llm_result.handled:
                    # Aplicar outcome se confiança suficiente
                    if llm_result.confidence >= settings.CONFIRM_AGENT_THRESHOLD:
                        actions = await self._create_confirmation_actions(llm_result, env.lead.id)
                        llm_result.actions = actions
                        
                        # Log telemetria
                        latency_ms = int((time.time() - start_time) * 1000)
                        await self._log_confirmation_telemetry(
                            env.lead.id, llm_result, latency_ms, "applied"
                        )
                        
                        return llm_result
                    else:
                        # Confiança baixa - não aplicar
                        logger.info(f"LLM confidence too low: {llm_result.confidence} < {settings.CONFIRM_AGENT_THRESHOLD}")
                        return ConfirmationResult(handled=False, reason="low_confidence")
                        
            except Exception as e:
                logger.warning(f"LLM confirmation failed: {str(e)}")
                # Continuar para fallback determinístico
        
        # Fallback determinístico
        if settings.CONFIRM_AGENT_MODE in ["llm_first", "hybrid", "det_only"]:
            fallback_result = await self._try_deterministic_confirmation(
                current_message, pending_confirmations
            )
            
            if fallback_result.handled:
                actions = await self._create_confirmation_actions(fallback_result, env.lead.id)
                fallback_result.actions = actions
                
                # Log telemetria
                latency_ms = int((time.time() - start_time) * 1000)
                await self._log_confirmation_telemetry(
                    env.lead.id, fallback_result, latency_ms, "applied"
                )
                
                return fallback_result
        
        return ConfirmationResult(handled=False, reason="no_match")
    
    async def _get_pending_confirmations(self, contexto_lead, env: Env) -> List[Dict[str, Any]]:
        """
        Obtém lista de confirmações pendentes baseada no contexto.
        
        Args:
            contexto_lead: Contexto persistente do lead
            env: Ambiente atual
            
        Returns:
            Lista de confirmações pendentes
        """
        pending = []
        
        # Verificar aguardando no contexto
        if contexto_lead and contexto_lead.aguardando:
            aguardando = contexto_lead.aguardando
            if aguardando.get("tipo") == "confirmacao":
                target = aguardando.get("fato")
                if target and self._is_target_valid(target):
                    # Verificar TTL
                    ttl = aguardando.get("ttl", 0)
                    if int(time.time()) <= ttl:
                        pending.append({
                            "target": target,
                            "source": "context",
                            "timestamp": ttl - 1800  # Assuming 30min TTL
                        })
        
        # TODO: Verificar última automação se for de pergunta e recente
        # if contexto_lead and contexto_lead.ultima_automacao_enviada:
        #     automation = await self._get_automation_by_id(contexto_lead.ultima_automacao_enviada)
        #     if automation and automation.get("expects_reply"):
        #         ...
        
        return pending
    
    async def _try_llm_confirmation(
        self, 
        message: str, 
        history: List, 
        pending_confirmations: List[Dict[str, Any]], 
        snapshot
    ) -> ConfirmationResult:
        """
        Tenta interpretar confirmação usando LLM.
        
        Args:
            message: Mensagem atual
            history: Histórico limitado de mensagens
            pending_confirmations: Confirmações pendentes
            snapshot: Snapshot do lead
            
        Returns:
            ConfirmationResult
        """
        if not self.openai_client:
            return ConfirmationResult(handled=False, reason="no_openai_client")
        
        # Preparar contexto para LLM
        context = self._build_llm_context(message, history, pending_confirmations, snapshot)
        
        try:
            # Usar function calling para estruturar resposta
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": """Você é um especialista em interpretar respostas de confirmação em português brasileiro.
                        
Analise se a mensagem do usuário é uma resposta de confirmação (sim/não) para alguma pergunta pendente.

Contexto: Sistema de automação para leads interessados em robô de trading.

Regras:
- Só confirme se a mensagem for claramente uma resposta sim/não 
- "sim", "consigo", "posso", "quero", "aceito" = YES
- "não", "não consigo", "não posso", "não quero" = NO
- Frases ambíguas ou perguntas = UNKNOWN
- Considere apenas confirmações para perguntas recentes (últimos 30min)""",
                    },
                    {
                        "role": "user", 
                        "content": context
                    }
                ],
                functions=[
                    {
                        "name": "analyze_confirmation",
                        "description": "Analisa se uma mensagem é uma confirmação",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "matches": {
                                    "type": "boolean",
                                    "description": "Se a mensagem é uma confirmação clara"
                                },
                                "target": {
                                    "type": "string", 
                                    "description": "Target da confirmação (se aplicável)"
                                },
                                "polarity": {
                                    "type": "string",
                                    "enum": ["yes", "no", "unknown"],
                                    "description": "Polaridade da resposta"
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                    "description": "Confiança na análise (0-1)"
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "Justificativa da análise"
                                }
                            },
                            "required": ["matches", "polarity", "confidence", "reason"]
                        }
                    }
                ],
                function_call={"name": "analyze_confirmation"},
                timeout=settings.CONFIRM_AGENT_TIMEOUT_MS / 1000.0
            )
            
            # Extrair resposta estruturada
            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "analyze_confirmation":
                import json
                args = json.loads(function_call.arguments)
                
                if args.get("matches") and pending_confirmations:
                    target = args.get("target") or pending_confirmations[0]["target"]
                    return ConfirmationResult(
                        handled=True,
                        target=target,
                        polarity=args.get("polarity", "unknown"),
                        confidence=args.get("confidence", 0.0),
                        source="llm",
                        reason=args.get("reason", "LLM confirmation")
                    )
            
            return ConfirmationResult(handled=False, reason="llm_no_match", source="llm")
            
        except Exception as e:
            logger.error(f"LLM confirmation error: {str(e)}")
            return ConfirmationResult(handled=False, reason=f"llm_error: {str(e)}", source="llm")
    
    async def _try_deterministic_confirmation(
        self, 
        message: str, 
        pending_confirmations: List[Dict[str, Any]]
    ) -> ConfirmationResult:
        """
        Tenta interpretar confirmação usando regras determinísticas.
        
        Args:
            message: Mensagem atual
            pending_confirmations: Confirmações pendentes
            
        Returns:
            ConfirmationResult
        """
        if not pending_confirmations:
            return ConfirmationResult(handled=False, reason="no_pending")
        
        # Normalizar mensagem
        msg_lower = message.lower().strip()
        
        # Padrões de confirmação
        yes_patterns = [
            "sim", "consigo", "posso", "quero", "aceito", "pode", "vamos", 
            "claro", "certeza", "ok", "beleza", "perfeito", "vou"
        ]
        
        no_patterns = [
            "não", "nao", "não consigo", "não posso", "não quero", 
            "impossível", "não dá", "não da", "negativo"
        ]
        
        # Verificar padrões
        polarity = None
        confidence = 0.0
        
        for pattern in yes_patterns:
            if pattern in msg_lower:
                polarity = "yes"
                confidence = 0.85 if pattern in ["sim", "consigo", "posso"] else 0.75
                break
        
        if not polarity:
            for pattern in no_patterns:
                if pattern in msg_lower:
                    polarity = "no"
                    confidence = 0.85 if pattern in ["não", "nao"] else 0.75
                    break
        
        if polarity and confidence >= 0.70:  # Limiar mais baixo para determinístico
            return ConfirmationResult(
                handled=True,
                target=pending_confirmations[0]["target"],
                polarity=polarity,
                confidence=confidence,
                source="fallback",
                reason=f"deterministic_match: {polarity}"
            )
        
        return ConfirmationResult(handled=False, reason="deterministic_no_match", source="fallback")
    
    def _build_llm_context(
        self, 
        message: str, 
        history: List, 
        pending_confirmations: List[Dict[str, Any]], 
        snapshot
    ) -> str:
        """
        Constrói contexto para LLM.
        """
        context_parts = []
        
        # Mensagem atual
        context_parts.append(f"MENSAGEM ATUAL: '{message}'")
        
        # Confirmações pendentes
        if pending_confirmations:
            targets = [p["target"] for p in pending_confirmations]
            context_parts.append(f"AGUARDANDO CONFIRMAÇÃO PARA: {', '.join(targets)}")
        
        # Histórico limitado (últimas N mensagens)
        if history and len(history) > 1:
            recent_history = history[-min(settings.CONFIRM_AGENT_MAX_HISTORY, len(history)):]
            history_text = " | ".join([msg.text for msg in recent_history[-3:]])
            context_parts.append(f"CONTEXTO RECENTE: {history_text}")
        
        # Snapshot relevante
        if hasattr(snapshot, 'agreements') and snapshot.agreements:
            relevant_agreements = {k: v for k, v in snapshot.agreements.items() if v}
            if relevant_agreements:
                context_parts.append(f"ACORDOS: {relevant_agreements}")
        
        return "\n\n".join(context_parts)
    
    async def _create_confirmation_actions(self, result: ConfirmationResult, lead_id: Optional[int]) -> List[Action]:
        """
        Cria ações baseadas no resultado da confirmação.
        
        Args:
            result: Resultado da confirmação
            lead_id: ID do lead
            
        Returns:
            Lista de ações a serem executadas
        """
        actions = []
        
        if not result.handled or not result.target or not lead_id:
            return actions
        
        # Carregar configuração do target
        target_config = await self._get_target_config(result.target)
        if not target_config:
            logger.warning(f"Target config not found: {result.target}")
            return actions
        
        # Criar ações baseado na polaridade
        if result.polarity == "yes" and "on_yes" in target_config:
            facts = target_config["on_yes"].get("facts", {})
            if facts:
                actions.append(Action(
                    type="set_facts",
                    set_facts=facts
                ))
            
            # Adicionar mensagem de confirmação para o usuário
            actions.append(Action(
                type="send_message",
                text="✅ Perfeito! Entendi que você consegue fazer o depósito. Vou liberar seu acesso ao teste!"
            ))
        
        elif result.polarity == "no" and "on_no" in target_config:
            facts = target_config["on_no"].get("facts", {})
            automation = target_config["on_no"].get("automation")
            
            if facts:
                actions.append(Action(
                    type="set_facts",
                    set_facts=facts
                ))
            
            if automation:
                actions.append(Action(
                    type="send_message",
                    text=f"Automação de ajuda disparada: {automation}"
                ))
            else:
                # Mensagem padrão para 'não'
                actions.append(Action(
                    type="send_message",
                    text="Entendi que você não consegue fazer o depósito agora. Posso te ajudar com outras opções!"
                ))
        
        # Sempre limpar estado aguardando
        actions.append(Action(
            type="clear_waiting",
            text="Estado de aguardando limpo"
        ))
        
        return actions
    
    async def _get_target_config(self, target: str) -> Optional[Dict[str, Any]]:
        """
        Obtém configuração de um target do YAML.
        
        Args:
            target: Nome do target
            
        Returns:
            Configuração do target ou None
        """
        global _confirm_targets_cache
        
        if _confirm_targets_cache is None:
            try:
                # Carregar confirm_targets.yml
                targets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                           "policies", "confirm_targets.yml")
                
                if os.path.exists(targets_path):
                    with open(targets_path, 'r', encoding='utf-8') as f:
                        _confirm_targets_cache = yaml.safe_load(f) or {}
                        logger.info(f"Loaded {len(_confirm_targets_cache)} confirmation targets from YAML")
                else:
                    logger.warning(f"Confirm targets YAML not found: {targets_path}")
                    _confirm_targets_cache = {}
                    
            except Exception as e:
                logger.error(f"Error loading confirm targets YAML: {str(e)}")
                _confirm_targets_cache = {}
        
        return _confirm_targets_cache.get(target)
    
    def _is_target_valid(self, target: str) -> bool:
        """
        Verifica se target está na whitelist.
        
        Args:
            target: Nome do target
            
        Returns:
            True se válido
        """
        global _confirm_targets_whitelist, _confirm_targets_cache
        
        if not _confirm_targets_whitelist:
            # Carregar whitelist das chaves do YAML
            if _confirm_targets_cache is None:
                # Carregar cache primeiro
                import asyncio
                asyncio.create_task(self._get_target_config("dummy"))
            
            if _confirm_targets_cache:
                _confirm_targets_whitelist = set(_confirm_targets_cache.keys())
            else:
                _confirm_targets_whitelist = {"confirm_can_deposit", "confirm_created_account"}
        
        return target in _confirm_targets_whitelist
    
    async def _log_confirmation_telemetry(
        self, 
        lead_id: Optional[int], 
        result: ConfirmationResult, 
        latency_ms: int, 
        outcome: str
    ) -> None:
        """
        Registra telemetria da confirmação.
        
        Args:
            lead_id: ID do lead
            result: Resultado da confirmação
            latency_ms: Latência em ms
            outcome: 'applied' | 'skip'
        """
        from app.infra.logging import log_structured
        
        log_structured("info", "confirmation_processed", {
            "lead_id": lead_id,
            "target": result.target,
            "polarity": result.polarity,
            "confidence": result.confidence,
            "source": result.source,
            "latency_ms": latency_ms,
            "outcome": outcome,
            "reason": result.reason
        })


# Instância global do gate
_confirmation_gate = None

def get_confirmation_gate() -> ConfirmationGate:
    """Obtém instância singleton do gate de confirmação."""
    global _confirmation_gate
    if _confirmation_gate is None:
        _confirmation_gate = ConfirmationGate()
    return _confirmation_gate
