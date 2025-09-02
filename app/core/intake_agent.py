"""
Intake Agent - Agente de recepção inteligente

Interpreta mensagem crua e se a confiança for alta, chama até 2 tools 
(verify/check) em paralelo quando útil, devolvendo fatos prontos no snapshot.
1 chamada LLM (abstraída) + heurísticas de decisão.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio

from app.data.schemas import Env

logger = logging.getLogger(__name__)

# Configurações do intake conforme policy_intake.yml
INTAKE_CONFIG = {
    "llm_budget": 1,
    "tool_budget": 2,
    "max_latency_ms": 3000,
    "thresholds": {
        "direct": 0.80,
        "parallel": 0.60
    },
    "anchors": {
        "email": ["email", "e-mail", "mail"],
        "id": ["id", "conta", "login", "número da conta"]
    },
    "broker_priority": [
        "by_active_procedure",
        "by_profile_known", 
        "fallback_parallel"
    ]
}

# Configuração para intake sempre-LLM
INTAKE_LLM_CONFIG = {
    "mode": "always_llm",  # always_llm | hybrid | passthrough
    "samples": 2,  # Número de amostras para majority vote
    "short_msg_tokens": 4,  # Mensagens com ≤ tokens pular RAG
    "use_reranker": True,
    "self_consistency": True
}


async def run_intake(env: Env) -> Env:
    """
    Executa intake inteligente da mensagem.
    
    Args:
        env: Ambiente com snapshot inicial
        
    Returns:
        Env: Ambiente enriquecido com dados dos tools
    """
    logger.info("Iniciando intake agent")
    
    # Verificar se deve usar intake sempre-LLM
    if INTAKE_LLM_CONFIG["mode"] == "always_llm":
        return await run_intake_always_llm(env)
    
    # Analisar confiança e decidir estratégia
    analysis = analyze_message_confidence(env)
    
    # Executar estratégia baseada na confiança
    if analysis["strategy"] == "direct":
        enriched_env = await execute_direct_strategy(env, analysis)
    elif analysis["strategy"] == "parallel":
        enriched_env = await execute_parallel_strategy(env, analysis)
    else:
        # Estratégia passthrough - sem tools
        enriched_env = env
        logger.info("Estratégia passthrough - sem execução de tools")
    
    logger.info(f"Intake concluído com estratégia: {analysis['strategy']}")
    return enriched_env


async def run_intake_always_llm(env: Env) -> Env:
    """
    Executa intake sempre-LLM com output estruturado.
    
    Args:
        env: Ambiente com snapshot inicial
        
    Returns:
        Env: Ambiente enriquecido com sinais do LLM
    """
    logger.info("Iniciando intake sempre-LLM")
    
    # Extrair mensagem atual
    current_message = ""
    if env.messages_window:
        current_message = env.messages_window[-1].text
    
    if not current_message:
        logger.info("Mensagem vazia - retornando env original")
        return env
    
    # Verificar se mensagem é curta (pular RAG)
    tokens_estimate = len(current_message.split())
    use_rag = tokens_estimate > INTAKE_LLM_CONFIG["short_msg_tokens"]
    
    # Executar análise LLM
    llm_result = await _analyze_message_with_llm(current_message, env, use_rag)
    
    # Aplicar sinais do LLM ao snapshot (sem modificar fatos duros)
    enriched_env = _apply_llm_signals_to_env(env, llm_result)
    
    # Log estruturado para observabilidade
    logger.info(f"{{'event':'intake_llm', 'intents':{len(llm_result.get('intents', []))}, 'polarity':'{llm_result.get('polarity', 'unknown')}', 'targets':{len(llm_result.get('targets', {}))}, 'facts_count':{len(llm_result.get('facts', []))}, 'propose_automations_count':{len(llm_result.get('propose_automations', []))}, 'used_samples':{INTAKE_LLM_CONFIG['samples']}, 'agreement_score':{llm_result.get('agreement_score', 'N/A')}, 'error':{llm_result.get('error', None)}}}")
    
    logger.info(f"Intake sempre-LLM concluído: polarity={llm_result.get('polarity')}, intents={llm_result.get('intents')}")
    return enriched_env


def analyze_message_confidence(env: Env) -> Dict[str, Any]:
    """
    Analisa mensagem e determina estratégia de intake.
    
    Args:
        env: Ambiente atual
        
    Returns:
        Análise com estratégia e confiança
    """
    message_text = ""
    if env.messages_window:
        message_text = env.messages_window[-1].text.lower()
    
    candidates = env.candidates
    analysis = {
        "strategy": "passthrough",
        "confidence": 0.0,
        "triggers": [],
        "tools_to_call": []
    }
    
    # Calcular confiança baseada em candidatos e âncoras
    confidence_score = 0.0
    triggers = []
    
    # Verificar se há email ou ID forte nos candidatos
    if "email" in candidates:
        confidence_score += 0.4
        triggers.append("email_detected")
    
    if "nyrion_id" in candidates or "quotex_id" in candidates:
        confidence_score += 0.5
        triggers.append("broker_id_detected")
    
    # Verificar âncoras no texto
    for anchor_type, anchor_words in INTAKE_CONFIG["anchors"].items():
        for word in anchor_words:
            if word in message_text:
                confidence_score += 0.3
                triggers.append(f"{anchor_type}_anchor")
                break
    
    # Determinar estratégia baseada na confiança
    if confidence_score >= INTAKE_CONFIG["thresholds"]["direct"]:
        analysis["strategy"] = "direct"
        analysis["confidence"] = confidence_score
        analysis["triggers"] = triggers
        analysis["tools_to_call"] = ["verify_signup", "check_broker_status"]
    elif confidence_score >= INTAKE_CONFIG["thresholds"]["parallel"]:
        analysis["strategy"] = "parallel"
        analysis["confidence"] = confidence_score
        analysis["triggers"] = triggers
        analysis["tools_to_call"] = ["verify_signup"]
    else:
        analysis["strategy"] = "passthrough"
        analysis["confidence"] = confidence_score
        analysis["triggers"] = triggers
    
    return analysis


async def _analyze_message_with_llm(message: str, env: Env, use_rag: bool) -> Dict[str, Any]:
    """
    Analisa mensagem usando LLM com output estruturado.
    
    Args:
        message: Mensagem a ser analisada
        env: Ambiente atual
        use_rag: Se deve usar RAG para contexto
        
    Returns:
        Resultado estruturado da análise
    """
    try:
        from app.settings import settings
        import openai
        
        if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key não configurada - retornando resultado vazio")
            return _get_empty_llm_result()
        
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Preparar contexto
        context = _build_intake_context(message, env, use_rag)
        
        # Executar análise com self-consistency se habilitado
        if INTAKE_LLM_CONFIG["self_consistency"]:
            results = []
            for i in range(INTAKE_LLM_CONFIG["samples"]):
                result = await _call_intake_llm(client, context, i)
                results.append(result)
            
            # Majority vote para campos críticos
            final_result = _merge_llm_results(results)
        else:
            final_result = await _call_intake_llm(client, context, 0)
        
        return final_result
        
    except Exception as e:
        logger.error(f"Erro na análise LLM: {str(e)}")
        return _get_empty_llm_result()


def _build_intake_context(message: str, env: Env, use_rag: bool) -> str:
    """
    Constrói contexto para análise LLM.
    
    Args:
        message: Mensagem atual
        env: Ambiente
        use_rag: Se deve incluir contexto RAG
        
    Returns:
        Contexto formatado
    """
    context_parts = [
        f"Mensagem do usuário: {message}",
        f"Lead ID: {env.lead.id if env.lead else 'N/A'}",
        f"Plataforma: {env.lead.platform if env.lead else 'N/A'}"
    ]
    
    # Adicionar snapshot se disponível
    if hasattr(env, 'snapshot') and env.snapshot:
        snapshot = env.snapshot
        context_parts.append(f"Contas: {getattr(snapshot, 'accounts', {})}")
        context_parts.append(f"Depósito: {getattr(snapshot, 'deposit', {})}")
        context_parts.append(f"Acordos: {getattr(snapshot, 'agreements', {})}")
    
    # Adicionar histórico recente
    if env.messages_window and len(env.messages_window) > 1:
        recent_messages = env.messages_window[-3:]  # Últimas 3 mensagens
        context_parts.append("Histórico recente:")
        for msg in recent_messages:
            context_parts.append(f"- {msg.sender}: {msg.text}")
    
    # TODO: Adicionar contexto RAG se use_rag=True
    
    return "\n".join(context_parts)


async def _call_intake_llm(client, context: str, sample_id: int) -> Dict[str, Any]:
    """
    Chama LLM para análise de intake.
    
    Args:
        client: Cliente OpenAI
        context: Contexto formatado
        sample_id: ID da amostra (para self-consistency)
        
    Returns:
        Resultado da análise
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1 if sample_id == 0 else 0.3,  # Primeira amostra mais determinística
            messages=[
                {
                    "role": "system",
                    "content": """Você é um especialista em análise de mensagens de leads para sistema de trading.

Analise a mensagem do usuário e extraia informações estruturadas:

1. INTENTS: Intenções principais (ex: "quero testar", "preciso de ajuda", "criar conta")
2. POLARITY: Polaridade da resposta (yes/no/other/sarcastic)
3. TARGETS: Confirmações para targets específicos (ex: {"confirm_can_deposit": "yes"})
4. FACTS: Fatos extraídos da mensagem (ex: [{"path": "agreements.can_deposit", "value": true, "confidence": 0.9}])
5. PROPOSE_AUTOMATIONS: Automações sugeridas (ex: ["ask_deposit_for_test", "signup_link"])
6. NEEDS_CLARIFYING: Se precisa de esclarecimento
7. SLOTS_PATCH: Campos opcionais para atualizar

Contexto: Sistema ManyBlack V2 para robô de trading."""
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
                            functions=[
                    {
                        "name": "analyze_intake",
                        "description": "Analisa mensagem de intake",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "intents": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Intenções principais"
                                },
                                "polarity": {
                                    "type": "string",
                                    "enum": ["yes", "no", "other", "sarcastic"],
                                    "description": "Polaridade da resposta"
                                },
                                "targets": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "type": "string",
                                        "enum": ["yes", "no", "n/a"]
                                    },
                                    "description": "Confirmações para targets específicos"
                                },
                                "facts": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "path": {"type": "string"},
                                            "value": {
                                                "oneOf": [
                                                    {"type": "string"},
                                                    {"type": "number"},
                                                    {"type": "boolean"},
                                                    {"type": "null"}
                                                ]
                                            },
                                            "confidence": {"type": "number"}
                                        },
                                        "required": ["path", "value"],
                                        "additionalProperties": False
                                    },
                                    "description": "Fatos extraídos"
                                },
                                "propose_automations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Automações sugeridas"
                                },
                                "needs_clarifying": {
                                    "type": "boolean",
                                    "description": "Se precisa de esclarecimento"
                                },
                                "slots_patch": {
                                    "type": "object",
                                    "additionalProperties": {
                                        "oneOf": [
                                            {"type": "string"},
                                            {"type": "number"},
                                            {"type": "boolean"}
                                        ]
                                    },
                                    "description": "Campos opcionais para atualizar"
                                }
                            },
                            "required": ["intents", "polarity", "targets", "facts", "propose_automations", "needs_clarifying"],
                            "additionalProperties": False
                        }
                    }
                ],
            function_call={"name": "analyze_intake"}
        )
        
        # Extrair resultado da function call
        if response.choices and response.choices[0].message.function_call:
            import json
            result = json.loads(response.choices[0].message.function_call.arguments)
            return result
        
        return _get_empty_llm_result()
        
    except Exception as e:
        logger.error(f"Erro na chamada LLM: {str(e)}")
        return _get_empty_llm_result()


def _get_empty_llm_result() -> Dict[str, Any]:
    """Retorna resultado vazio para LLM."""
    return {
        "intents": [],
        "polarity": "other",
        "targets": {},
        "facts": [],
        "propose_automations": [],
        "needs_clarifying": False,
        "slots_patch": {}
    }


def _merge_llm_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Faz majority vote para mesclar resultados de self-consistency.
    
    Args:
        results: Lista de resultados do LLM
        
    Returns:
        Resultado mesclado
    """
    if not results:
        return _get_empty_llm_result()
    
    if len(results) == 1:
        return results[0]
    
    # Majority vote para polarity
    polarities = [r.get("polarity", "other") for r in results]
    from collections import Counter
    polarity_counter = Counter(polarities)
    final_polarity = polarity_counter.most_common(1)[0][0]
    
    # Unir intents únicos
    all_intents = set()
    for r in results:
        all_intents.update(r.get("intents", []))
    
    # Unir targets (maioria vence)
    all_targets = {}
    for r in results:
        for target, value in r.get("targets", {}).items():
            if target not in all_targets:
                all_targets[target] = []
            all_targets[target].append(value)
    
    final_targets = {}
    for target, values in all_targets.items():
        value_counter = Counter(values)
        final_targets[target] = value_counter.most_common(1)[0][0]
    
    # Unir facts (maioria vence)
    all_facts = {}
    for r in results:
        for fact in r.get("facts", []):
            path = fact.get("path")
            if path not in all_facts:
                all_facts[path] = []
            all_facts[path].append(fact)
    
    final_facts = []
    for path, facts in all_facts.items():
        if len(facts) > len(results) / 2:  # Maioria
            final_facts.append(facts[0])  # Pegar primeiro
    
    # Unir automações sugeridas
    all_automations = set()
    for r in results:
        all_automations.update(r.get("propose_automations", []))
    
    # Calcular agreement score
    agreement_score = None
    if len(results) > 1:
        # Calcular concordância baseada na polarity
        polarity_agreement = sum(1 for r in results if r.get("polarity") == final_polarity) / len(results)
        agreement_score = round(polarity_agreement, 2)
    
    return {
        "intents": list(all_intents),
        "polarity": final_polarity,
        "targets": final_targets,
        "facts": final_facts,
        "propose_automations": list(all_automations),
        "needs_clarifying": any(r.get("needs_clarifying", False) for r in results),
        "slots_patch": results[0].get("slots_patch", {}),  # Usar primeiro
        "agreement_score": agreement_score,
        "error": None
    }


def _apply_llm_signals_to_env(env: Env, llm_result: Dict[str, Any]) -> Env:
    """
    Aplica sinais do LLM ao ambiente (sem modificar fatos duros).
    
    Args:
        env: Ambiente original
        llm_result: Resultado do LLM
        
    Returns:
        Env enriquecido
    """
    # Adicionar sinais do LLM ao snapshot
    if hasattr(env, 'snapshot') and env.snapshot:
        # Adicionar campo para sinais do LLM
        if not hasattr(env.snapshot, 'llm_signals'):
            env.snapshot.llm_signals = {}
        
        env.snapshot.llm_signals.update({
            "intents": llm_result.get("intents", []),
            "polarity": llm_result.get("polarity", "other"),
            "targets": llm_result.get("targets", {}),
            "facts": llm_result.get("facts", []),
            "propose_automations": llm_result.get("propose_automations", []),
            "needs_clarifying": llm_result.get("needs_clarifying", False),
            "slots_patch": llm_result.get("slots_patch", {}),
            "used_samples": INTAKE_LLM_CONFIG['samples'],
            "agreement_score": llm_result.get("agreement_score"),
            "error": llm_result.get("error")
        })
    
    return env


def analyze_message_confidence(env: Env) -> Dict[str, Any]:
    """
    Analisa mensagem e determina estratégia de intake.
    
    Args:
        env: Ambiente atual
        
    Returns:
        Análise com estratégia e confiança
    """
    message_text = ""
    if env.messages_window:
        message_text = env.messages_window[-1].text.lower()
    
    candidates = env.candidates
    analysis = {
        "strategy": "passthrough",
        "confidence": 0.0,
        "triggers": [],
        "tools_to_call": []
    }
    
    # Calcular confiança baseada em candidatos e âncoras
    confidence_score = 0.0
    triggers = []
    
    # Verificar se há email ou ID forte nos candidatos
    if "email" in candidates:
        confidence_score += 0.4
        triggers.append("email_detected")
    
    if "nyrion_id" in candidates or "quotex_id" in candidates:
        confidence_score += 0.5
        triggers.append("broker_id_detected")
    
    # Verificar âncoras no texto
    for anchor_type, anchor_words in INTAKE_CONFIG["anchors"].items():
        for word in anchor_words:
            if word in message_text:
                confidence_score += 0.3
                triggers.append(f"{anchor_type}_anchor")
                break
    
    # Determinar estratégia baseada na confiança
    if confidence_score >= INTAKE_CONFIG["thresholds"]["direct"]:
        analysis["strategy"] = "direct"
        analysis["confidence"] = confidence_score
        analysis["triggers"] = triggers
        analysis["tools_to_call"] = ["verify_signup", "check_broker_status"]
    elif confidence_score >= INTAKE_CONFIG["thresholds"]["parallel"]:
        analysis["strategy"] = "parallel"
        analysis["confidence"] = confidence_score
        analysis["triggers"] = triggers
        analysis["tools_to_call"] = ["verify_signup"]
    else:
        analysis["strategy"] = "passthrough"
        analysis["confidence"] = confidence_score
        analysis["triggers"] = triggers
    
    return analysis


def determine_direct_tools(env: Env, candidates: Dict[str, Any]) -> List[str]:
    """Determina tools para estratégia direta (alta confiança)."""
    tools = []
    
    # Se há email ou ID, verificar cadastro
    if "email" in candidates or "nyrion_id" in candidates or "quotex_id" in candidates:
        tools.append("verify_signup")
    
    # Se há contexto de depósito, verificar
    if candidates.get("intent") == "deposito" or env.snapshot.agreements.get("can_deposit"):
        tools.append("check_deposit")
    
    return tools[:INTAKE_CONFIG["tool_budget"]]


def determine_parallel_tools(env: Env, candidates: Dict[str, Any]) -> List[str]:
    """Determina tools para estratégia paralela (confiança média)."""
    tools = []
    
    # Estratégia paralela: verificar ambos se há evidências
    if candidates:
        tools.extend(["verify_signup", "check_deposit"])
    
    return tools[:INTAKE_CONFIG["tool_budget"]]


async def execute_direct_strategy(env: Env, analysis: Dict[str, Any]) -> Env:
    """
    Executa estratégia direta - tools em sequência otimizada.
    
    Args:
        env: Ambiente atual
        analysis: Análise do intake
        
    Returns:
        Ambiente enriquecido
    """
    tools_to_call = analysis["tools_to_call"]
    
    for tool_name in tools_to_call:
        try:
            # TODO: Implementar chamadas reais dos tools
            result = await call_tool_stub(tool_name, env)
            env = merge_tool_result(env, tool_name, result)
            logger.info(f"Tool {tool_name} executado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao executar tool {tool_name}: {str(e)}")
    
    return env


async def execute_parallel_strategy(env: Env, analysis: Dict[str, Any]) -> Env:
    """
    Executa estratégia paralela - tools em paralelo quando útil.
    
    Args:
        env: Ambiente atual  
        analysis: Análise do intake
        
    Returns:
        Ambiente enriquecido
    """
    tools_to_call = analysis["tools_to_call"]
    
    if len(tools_to_call) <= 1:
        # Não vale a pena paralelizar
        return await execute_direct_strategy(env, analysis)
    
    # Executar tools em paralelo
    tasks = []
    for tool_name in tools_to_call:
        task = call_tool_stub(tool_name, env)
        tasks.append((tool_name, task))
    
    # Aguardar resultados com timeout
    try:
        timeout_seconds = INTAKE_CONFIG["max_latency_ms"] / 1000
        results = await asyncio.wait_for(
            asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
            timeout=timeout_seconds
        )
        
        # Processar resultados
        for i, (tool_name, _) in enumerate(tasks):
            result = results[i]
            if not isinstance(result, Exception):
                env = merge_tool_result(env, tool_name, result)
                logger.info(f"Tool {tool_name} executado em paralelo")
            else:
                logger.error(f"Erro no tool {tool_name}: {str(result)}")
                
    except asyncio.TimeoutError:
        logger.warning("Timeout na execução paralela de tools")
    
    return env


async def call_tool_stub(tool_name: str, env: Env) -> Dict[str, Any]:
    """
    Stub para chamada de tools. 
    TODO: Implementar chamadas reais aos tools verify_signup e check_deposit.
    
    Args:
        tool_name: Nome do tool a ser chamado
        env: Ambiente atual
        
    Returns:
        Resultado do tool
    """
    # Simular latência realista
    await asyncio.sleep(0.1)
    
    if tool_name == "verify_signup":
        return {
            "verified": False,
            "accounts_found": [],
            "confidence": 0.5
        }
    elif tool_name == "check_deposit":
        return {
            "deposits_found": [],
            "total_amount": 0,
            "status": "none"
        }
    else:
        return {"status": "unknown_tool"}


def merge_tool_result(env: Env, tool_name: str, result: Dict[str, Any]) -> Env:
    """
    Mescla resultado do tool no ambiente.
    
    Args:
        env: Ambiente atual
        tool_name: Nome do tool executado  
        result: Resultado do tool
        
    Returns:
        Ambiente atualizado
    """
    # TODO: Implementar merge real dos resultados
    
    if tool_name == "verify_signup" and result.get("verified"):
        # Atualizar contas verificadas
        accounts_found = result.get("accounts_found", [])
        for account in accounts_found:
            broker = account.get("broker", "")
            if broker in env.snapshot.accounts:
                env.snapshot.accounts[broker] = "verificado"
    
    elif tool_name == "check_deposit":
        # Atualizar status de depósito
        deposits = result.get("deposits_found", [])
        if deposits:
            env.snapshot.deposit["status"] = "confirmado"
            env.snapshot.deposit["amount"] = result.get("total_amount", 0)
    
    return env
