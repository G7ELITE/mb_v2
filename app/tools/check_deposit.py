"""
Check Deposit - Verificador de depósito

Contrato de verificação de depósito nas corretoras.
Verifica status e valores de depósitos do lead.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.data.schemas import Env
from app.infra.logging import log_structured

logger = logging.getLogger(__name__)


class DepositChecker:
    """Verificador de depósitos em corretoras."""
    
    def __init__(self):
        self.timeout = 15.0
        self.max_retries = 2
        self.min_deposit_amount = 10.0  # Valor mínimo considerado válido
    
    async def check_lead_deposits(self, env: Env) -> Dict[str, Any]:
        """
        Verifica depósitos do lead nas corretoras.
        
        Args:
            env: Ambiente com dados do lead
            
        Returns:
            Resultado da verificação de depósitos
        """
        candidates = env.candidates
        snapshot = env.snapshot
        
        results = {
            "deposits_found": [],
            "total_amount": 0.0,
            "status": "none",
            "last_deposit_date": None,
            "errors": []
        }
        
        # Determinar contas para verificar
        accounts_to_check = self._determine_accounts_to_check(candidates, snapshot)
        
        if not accounts_to_check:
            logger.info("Nenhuma conta para verificar depósitos")
            return results
        
        # Executar verificações em paralelo
        verification_tasks = []
        
        for account in accounts_to_check:
            broker = account["broker"]
            account_id = account["account_id"]
            
            if broker == "nyrion":
                task = self._check_nyrion_deposits(account_id)
            elif broker == "quotex":
                task = self._check_quotex_deposits(account_id)
            else:
                continue
            
            verification_tasks.append((broker, account_id, task))
        
        # Executar verificações
        if verification_tasks:
            verification_results = await self._execute_parallel_checks(verification_tasks)
            results.update(self._consolidate_deposit_results(verification_results))
        
        log_structured("info", "deposit_check_completed", {
            "deposits_found": len(results["deposits_found"]),
            "total_amount": results["total_amount"],
            "status": results["status"]
        })
        
        return results
    
    def _determine_accounts_to_check(self, candidates: Dict[str, Any], snapshot) -> List[Dict[str, str]]:
        """Determina quais contas verificar baseado em candidatos e snapshot."""
        accounts = []
        
        # Verificar candidatos diretos
        if "nyrion_id" in candidates:
            accounts.append({
                "broker": "nyrion",
                "account_id": candidates["nyrion_id"]
            })
        
        if "quotex_id" in candidates:
            accounts.append({
                "broker": "quotex", 
                "account_id": candidates["quotex_id"]
            })
        
        # Verificar contas já conhecidas no snapshot
        snapshot_accounts = snapshot.accounts
        for broker, status in snapshot_accounts.items():
            if status not in ["desconhecido", "unknown"]:
                # Assumir que o status contém o ID da conta (simplificação)
                if broker not in [acc["broker"] for acc in accounts]:
                    accounts.append({
                        "broker": broker,
                        "account_id": status  # Simplificação para demo
                    })
        
        return accounts
    
    async def _execute_parallel_checks(self, tasks: List[tuple]) -> Dict[str, Any]:
        """Executa verificações de depósito em paralelo."""
        results = {}
        
        try:
            async_tasks = []
            task_map = []
            
            for broker, account_id, task in tasks:
                async_tasks.append(task)
                task_map.append((broker, account_id))
            
            completed = await asyncio.wait_for(
                asyncio.gather(*async_tasks, return_exceptions=True),
                timeout=self.timeout
            )
            
            # Processar resultados
            for i, (broker, account_id) in enumerate(task_map):
                result = completed[i]
                key = f"{broker}:{account_id}"
                
                if isinstance(result, Exception):
                    results[key] = {"error": str(result)}
                else:
                    results[key] = result
                    
        except asyncio.TimeoutError:
            logger.warning("Timeout nas verificações de depósito")
            for broker, account_id, _ in tasks:
                key = f"{broker}:{account_id}"
                results[key] = {"error": "timeout"}
        
        return results
    
    def _consolidate_deposit_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Consolida resultados das verificações de depósito."""
        consolidated = {
            "deposits_found": [],
            "total_amount": 0.0,
            "status": "none",
            "last_deposit_date": None,
            "errors": []
        }
        
        all_deposits = []
        total_amount = 0.0
        
        for account_key, result in results.items():
            if "error" in result:
                consolidated["errors"].append(f"{account_key}: {result['error']}")
                continue
            
            account_deposits = result.get("deposits", [])
            for deposit in account_deposits:
                deposit["account"] = account_key
                all_deposits.append(deposit)
                total_amount += deposit.get("amount", 0.0)
        
        # Ordenar depósitos por data (mais recente primeiro)
        all_deposits.sort(
            key=lambda d: d.get("date", "1970-01-01"), 
            reverse=True
        )
        
        consolidated["deposits_found"] = all_deposits
        consolidated["total_amount"] = total_amount
        
        # Determinar status geral
        if not all_deposits:
            consolidated["status"] = "none"
        elif any(d.get("status") == "confirmed" for d in all_deposits):
            consolidated["status"] = "confirmed"
        elif any(d.get("status") == "pending" for d in all_deposits):
            consolidated["status"] = "pending"
        else:
            consolidated["status"] = "unknown"
        
        # Data do último depósito
        if all_deposits:
            consolidated["last_deposit_date"] = all_deposits[0].get("date")
        
        return consolidated
    
    async def _check_nyrion_deposits(self, account_id: str) -> Dict[str, Any]:
        """
        Verifica depósitos no Nyrion.
        TODO: Implementar integração real com API do Nyrion.
        """
        await asyncio.sleep(0.2)  # Simular latência de API
        
        # Stub: simular alguns depósitos de exemplo
        mock_deposits = []
        
        # Simular depósito recente se ID parece válido
        if len(account_id) >= 6 and account_id.isdigit():
            # Simular depósito de 3 dias atrás
            recent_date = (datetime.now() - timedelta(days=3)).isoformat()
            mock_deposits.append({
                "id": f"nyr_dep_{account_id}_001",
                "amount": 25.0,
                "currency": "USD",
                "status": "confirmed",
                "date": recent_date,
                "method": "card"
            })
        
        return {
            "deposits": mock_deposits,
            "account_status": "active"
        }
    
    async def _check_quotex_deposits(self, account_id: str) -> Dict[str, Any]:
        """
        Verifica depósitos no Quotex.
        TODO: Implementar integração real com API do Quotex.
        """
        await asyncio.sleep(0.2)  # Simular latência de API
        
        # Stub: simular alguns depósitos de exemplo
        mock_deposits = []
        
        # Simular depósito pendente se ID parece válido
        if len(account_id) >= 6:
            recent_date = (datetime.now() - timedelta(hours=6)).isoformat()
            mock_deposits.append({
                "id": f"qtx_dep_{account_id}_001",
                "amount": 50.0,
                "currency": "USD",
                "status": "pending",
                "date": recent_date,
                "method": "pix"
            })
        
        return {
            "deposits": mock_deposits,
            "account_status": "active"
        }
    
    async def get_deposit_history(
        self, 
        broker: str, 
        account_id: str, 
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Obtém histórico de depósitos para conta específica.
        
        Args:
            broker: Nome da corretora
            account_id: ID da conta
            days_back: Dias para trás no histórico
            
        Returns:
            Histórico de depósitos
        """
        if broker.lower() == "nyrion":
            result = await self._check_nyrion_deposits(account_id)
        elif broker.lower() == "quotex":
            result = await self._check_quotex_deposits(account_id)
        else:
            return {
                "error": f"Broker não suportado: {broker}",
                "deposits": []
            }
        
        # Filtrar por período (simplificação para demo)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_deposits = []
        
        for deposit in result.get("deposits", []):
            deposit_date = datetime.fromisoformat(deposit.get("date", "1970-01-01"))
            if deposit_date >= cutoff_date:
                filtered_deposits.append(deposit)
        
        return {
            "deposits": filtered_deposits,
            "period_days": days_back,
            "account_status": result.get("account_status", "unknown")
        }


# Instância global do verificador
deposit_checker = DepositChecker()


async def check_deposit_tool(env: Env) -> Dict[str, Any]:
    """
    Tool function para verificação de depósitos.
    Interface padrão chamada pelo intake agent.
    
    Args:
        env: Ambiente com dados do lead
        
    Returns:
        Resultado da verificação
    """
    return await deposit_checker.check_lead_deposits(env)


async def check_minimum_deposit(env: Env, min_amount: float = 10.0) -> bool:
    """
    Verifica se lead tem depósito mínimo.
    
    Args:
        env: Ambiente com dados do lead
        min_amount: Valor mínimo requerido
        
    Returns:
        True se tem depósito mínimo
    """
    result = await deposit_checker.check_lead_deposits(env)
    return result.get("total_amount", 0.0) >= min_amount

