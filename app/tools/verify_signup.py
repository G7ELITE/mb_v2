"""
Verify Signup - Verificador de cadastro

Contrato de verificação de cadastro (NYRION/QUOTEX).
Executado por worker/service para validar contas de corretoras.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
import httpx

from app.data.schemas import Env
from app.infra.logging import log_structured

logger = logging.getLogger(__name__)


class SignupVerifier:
    """Verificador de cadastros em corretoras."""
    
    def __init__(self):
        self.timeout = 10.0
        self.max_retries = 2
    
    async def verify_lead_signup(self, env: Env) -> Dict[str, Any]:
        """
        Verifica cadastro do lead nas corretoras suportadas.
        
        Args:
            env: Ambiente com dados do lead
            
        Returns:
            Resultado da verificação
        """
        candidates = env.candidates
        snapshot = env.snapshot
        
        results = {
            "verified": False,
            "accounts_found": [],
            "confidence": 0.0,
            "errors": []
        }
        
        # Determinar estratégia de verificação baseada em candidatos
        verification_tasks = []
        
        # Verificar Nyrion se há candidato
        if "nyrion_id" in candidates:
            task = self._verify_nyrion_signup(candidates["nyrion_id"])
            verification_tasks.append(("nyrion", task))
        
        # Verificar Quotex se há candidato  
        if "quotex_id" in candidates:
            task = self._verify_quotex_signup(candidates["quotex_id"])
            verification_tasks.append(("quotex", task))
        
        # Verificar por email se disponível
        if "email" in candidates:
            email_tasks = [
                ("nyrion", self._verify_nyrion_by_email(candidates["email"])),
                ("quotex", self._verify_quotex_by_email(candidates["email"]))
            ]
            verification_tasks.extend(email_tasks)
        
        # Executar verificações em paralelo
        if verification_tasks:
            verification_results = await self._execute_parallel_verifications(verification_tasks)
            results.update(self._consolidate_verification_results(verification_results))
        
        log_structured("info", "signup_verification_completed", {
            "verified": results["verified"],
            "accounts_found": len(results["accounts_found"]),
            "confidence": results["confidence"]
        })
        
        return results
    
    async def _execute_parallel_verifications(self, tasks: List[tuple]) -> Dict[str, Any]:
        """Executa verificações em paralelo com timeout."""
        results = {}
        
        try:
            # Executar com timeout global
            async_tasks = {broker: task for broker, task in tasks}
            completed = await asyncio.wait_for(
                asyncio.gather(*async_tasks.values(), return_exceptions=True),
                timeout=self.timeout
            )
            
            # Processar resultados
            for i, (broker, _) in enumerate(tasks):
                result = completed[i]
                if isinstance(result, Exception):
                    results[broker] = {"error": str(result)}
                else:
                    results[broker] = result
                    
        except asyncio.TimeoutError:
            logger.warning("Timeout nas verificações de cadastro")
            for broker, _ in tasks:
                results[broker] = {"error": "timeout"}
        
        return results
    
    def _consolidate_verification_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Consolida resultados das verificações."""
        consolidated = {
            "verified": False,
            "accounts_found": [],
            "confidence": 0.0,
            "errors": []
        }
        
        confidence_scores = []
        
        for broker, result in results.items():
            if "error" in result:
                consolidated["errors"].append(f"{broker}: {result['error']}")
                continue
            
            if result.get("verified", False):
                account_info = {
                    "broker": broker,
                    "account_id": result.get("account_id"),
                    "status": result.get("status", "active"),
                    "confidence": result.get("confidence", 0.5)
                }
                consolidated["accounts_found"].append(account_info)
                confidence_scores.append(result.get("confidence", 0.5))
        
        # Calcular confiança geral
        if confidence_scores:
            consolidated["verified"] = True
            consolidated["confidence"] = max(confidence_scores)
        
        return consolidated
    
    async def _verify_nyrion_signup(self, nyrion_id: str) -> Dict[str, Any]:
        """
        Verifica cadastro no Nyrion por ID.
        TODO: Implementar integração real com API do Nyrion.
        """
        await asyncio.sleep(0.1)  # Simular latência
        
        # Stub: validação básica do formato
        if len(nyrion_id) >= 6 and nyrion_id.isdigit():
            return {
                "verified": True,
                "account_id": nyrion_id,
                "status": "active",
                "confidence": 0.8
            }
        
        return {"verified": False, "confidence": 0.0}
    
    async def _verify_quotex_signup(self, quotex_id: str) -> Dict[str, Any]:
        """
        Verifica cadastro no Quotex por ID.
        TODO: Implementar integração real com API do Quotex.
        """
        await asyncio.sleep(0.1)  # Simular latência
        
        # Stub: validação básica do formato
        if len(quotex_id) >= 6 and quotex_id.replace("_", "").isalnum():
            return {
                "verified": True,
                "account_id": quotex_id,
                "status": "active", 
                "confidence": 0.8
            }
        
        return {"verified": False, "confidence": 0.0}
    
    async def _verify_nyrion_by_email(self, email: str) -> Dict[str, Any]:
        """
        Verifica cadastro no Nyrion por email.
        TODO: Implementar integração real.
        """
        await asyncio.sleep(0.15)  # Simular latência maior
        
        # Stub: sempre retorna não encontrado por email
        return {"verified": False, "confidence": 0.0}
    
    async def _verify_quotex_by_email(self, email: str) -> Dict[str, Any]:
        """
        Verifica cadastro no Quotex por email.
        TODO: Implementar integração real.
        """
        await asyncio.sleep(0.15)  # Simular latência maior
        
        # Stub: sempre retorna não encontrado por email
        return {"verified": False, "confidence": 0.0}


# Instância global do verificador
signup_verifier = SignupVerifier()


async def verify_signup_tool(env: Env) -> Dict[str, Any]:
    """
    Tool function para verificação de cadastro.
    Interface padrão chamada pelo intake agent.
    
    Args:
        env: Ambiente com dados do lead
        
    Returns:
        Resultado da verificação
    """
    return await signup_verifier.verify_lead_signup(env)


# Função de conveniência para verificação direta
async def verify_account_by_id(broker: str, account_id: str) -> Dict[str, Any]:
    """
    Verifica conta específica por broker e ID.
    
    Args:
        broker: Nome da corretora (nyrion, quotex)
        account_id: ID da conta
        
    Returns:
        Resultado da verificação
    """
    verifier = SignupVerifier()
    
    if broker.lower() == "nyrion":
        return await verifier._verify_nyrion_signup(account_id)
    elif broker.lower() == "quotex":
        return await verifier._verify_quotex_signup(account_id)
    else:
        return {
            "verified": False,
            "error": f"Broker não suportado: {broker}"
        }

