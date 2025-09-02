"""
Automation Hook - Hook para aplicar expects_reply automaticamente

Monitora envio de automações e configura estado de aguardando confirmação
automaticamente quando uma automação tem expects_reply definido.
"""
import time
import logging
import yaml
import os
from typing import Dict, Any, Optional

from app.core.contexto_lead import get_contexto_lead_service

logger = logging.getLogger(__name__)

# Cache do catálogo de automações
_catalog_cache = None


class AutomationHook:
    """
    Hook que monitora envio de automações e configura aguardando automaticamente.
    """
    
    def __init__(self):
        self.contexto_service = get_contexto_lead_service()
    
    async def on_automation_sent(
        self, 
        automation_id: str, 
        lead_id: Optional[int], 
        success: bool = True,
        provider_message_id: Optional[str] = None,
        prompt_text: Optional[str] = None
    ) -> None:
        """
        Chamado após uma automação ser enviada com sucesso.
        
        Args:
            automation_id: ID da automação enviada
            lead_id: ID do lead
            success: Se o envio foi bem-sucedido
            provider_message_id: ID da mensagem no provider (Telegram, etc.)
            prompt_text: Texto da pergunta enviada
        """
        if not success or not lead_id or not automation_id:
            return
        
        try:
            # Buscar configuração da automação
            automation_config = await self._get_automation_config(automation_id)
            
            if not automation_config:
                logger.debug(f"Automation config not found: {automation_id}")
                return
            
            # Verificar se tem expects_reply
            expects_reply = automation_config.get("expects_reply")
            if not expects_reply:
                return
            
            target = expects_reply.get("target")
            if not target:
                logger.warning(f"expects_reply without target in automation: {automation_id}")
                return
            
            # Obter TTL do target
            ttl_minutes = await self._get_target_ttl(target)
            ttl_seconds = ttl_minutes * 60
            
            # Extrair texto da pergunta se não fornecido
            if not prompt_text:
                output = automation_config.get("output", {})
                prompt_text = output.get("text", "")
            
            # Configurar estado aguardando com informações completas
            aguardando = {
                "tipo": "confirmacao",
                "target": target,
                "automation_id": automation_id,
                "lead_id": lead_id,
                "provider_message_id": provider_message_id,
                "prompt_text": prompt_text,
                "ttl": int(time.time()) + ttl_seconds,
                "created_at": int(time.time())
            }
            
            await self.contexto_service.atualizar_contexto(
                lead_id=lead_id,
                aguardando=aguardando,
                ultima_automacao_enviada=automation_id
            )
            
            logger.info(f"🪝 [AutomationHook] Set waiting confirmation for lead {lead_id}: {target} (ttl: {ttl_minutes}min)")
            logger.info(f"🪝 [AutomationHook] Automation {automation_id} configured with expects_reply.target={target}")
            
            # Log estruturado para observabilidade
            logger.info(f"{{'event':'hook_waiting_set', 'automation_id':'{automation_id}', 'lead_id':{lead_id}, 'target':'{target}', 'ttl_seconds':{ttl_seconds}}}")
            
        except Exception as e:
            logger.error(f"Error in automation hook: {str(e)}")
    
    async def _get_automation_config(self, automation_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém configuração de uma automação do catálogo YAML.
        
        Args:
            automation_id: ID da automação
            
        Returns:
            Configuração da automação ou None
        """
        global _catalog_cache
        
        if _catalog_cache is None:
            try:
                # Carregar catalog.yml
                catalog_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                    "policies", "catalog.yml"
                )
                
                if os.path.exists(catalog_path):
                    with open(catalog_path, 'r', encoding='utf-8') as f:
                        catalog_list = yaml.safe_load(f) or []
                        
                    # Converter lista em dict indexado por ID
                    _catalog_cache = {item.get("id"): item for item in catalog_list if item.get("id")}
                    logger.info(f"Loaded {len(_catalog_cache)} automations from catalog")
                else:
                    logger.warning(f"Catalog YAML not found: {catalog_path}")
                    _catalog_cache = {}
                    
            except Exception as e:
                logger.error(f"Error loading catalog YAML: {str(e)}")
                _catalog_cache = {}
        
        return _catalog_cache.get(automation_id)
    
    async def _get_target_ttl(self, target: str) -> int:
        """
        Obtém TTL em minutos para um target de confirmação.
        
        Args:
            target: Nome do target
            
        Returns:
            TTL em minutos (default: 30)
        """
        try:
            # Carregar confirm_targets.yml
            targets_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "policies", "confirm_targets.yml"
            )
            
            if os.path.exists(targets_path):
                with open(targets_path, 'r', encoding='utf-8') as f:
                    targets = yaml.safe_load(f) or {}
                    
                target_config = targets.get(target, {})
                return target_config.get("max_age_minutes", 30)
            else:
                logger.warning(f"Confirm targets YAML not found: {targets_path}")
                return 30
                
        except Exception as e:
            logger.error(f"Error loading target TTL: {str(e)}")
            return 30


# Instância global do hook
_automation_hook = None

def get_automation_hook() -> AutomationHook:
    """Obtém instância singleton do hook de automação."""
    global _automation_hook
    if _automation_hook is None:
        _automation_hook = AutomationHook()
    return _automation_hook
