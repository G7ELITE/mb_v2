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


async def run_intake(env: Env) -> Env:
    """
    Executa intake inteligente da mensagem.
    
    Args:
        env: Ambiente com snapshot inicial
        
    Returns:
        Env: Ambiente enriquecido com dados dos tools
    """
    logger.info("Iniciando intake agent")
    
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
    for anchor_type, words in INTAKE_CONFIG["anchors"].items():
        if any(word in message_text for word in words):
            confidence_score += 0.2
            triggers.append(f"anchor_{anchor_type}")
    
    # Verificar contexto de procedimento ativo
    if env.snapshot.agreements.get("wants_test", False):
        confidence_score += 0.3
        triggers.append("active_procedure")
    
    analysis["confidence"] = min(confidence_score, 1.0)
    analysis["triggers"] = triggers
    
    # Decidir estratégia baseada na confiança
    if analysis["confidence"] >= INTAKE_CONFIG["thresholds"]["direct"]:
        analysis["strategy"] = "direct"
        analysis["tools_to_call"] = determine_direct_tools(env, candidates)
    elif analysis["confidence"] >= INTAKE_CONFIG["thresholds"]["parallel"]:
        analysis["strategy"] = "parallel"
        analysis["tools_to_call"] = determine_parallel_tools(env, candidates)
    
    logger.info(f"Análise: confiança={analysis['confidence']:.2f}, estratégia={analysis['strategy']}")
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
