"""
UTM - Sistema de rastreamento UTM

Gerencia parâmetros UTM e rastreamento de origem de tráfego.
"""
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class UTMTracker:
    """Rastreador de parâmetros UTM."""
    
    def __init__(self):
        self.utm_params = [
            "utm_source",
            "utm_medium", 
            "utm_campaign",
            "utm_term",
            "utm_content"
        ]
    
    def extract_utm_from_url(self, url: str) -> Dict[str, str]:
        """
        Extrai parâmetros UTM de uma URL.
        
        Args:
            url: URL para análise
            
        Returns:
            Dicionário com parâmetros UTM
        """
        utm_data = {}
        
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            for param in self.utm_params:
                if param in query_params:
                    utm_data[param] = query_params[param][0]
        
        except Exception as e:
            logger.warning(f"Erro ao extrair UTM de URL: {str(e)}")
        
        return utm_data
    
    def build_utm_context(self, source_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Constrói contexto UTM a partir de dados de origem.
        
        Args:
            source_data: Dados de origem
            
        Returns:
            Contexto UTM
        """
        utm_context = {}
        
        # Mapear plataforma para source
        platform = source_data.get("platform", "")
        if platform:
            utm_context["utm_source"] = platform
        
        # Definir medium baseado no tipo
        message_type = source_data.get("type", "")
        if message_type == "callback":
            utm_context["utm_medium"] = "bot_button"
        else:
            utm_context["utm_medium"] = "bot_message"
        
        # Campaign padrão
        utm_context["utm_campaign"] = "lead_engagement"
        
        return utm_context
    
    def create_tracking_url(
        self, 
        base_url: str, 
        utm_context: Dict[str, str]
    ) -> str:
        """
        Cria URL com parâmetros UTM.
        
        Args:
            base_url: URL base
            utm_context: Contexto UTM
            
        Returns:
            URL com UTM
        """
        if not utm_context:
            return base_url
        
        # Construir query string UTM
        utm_params = []
        for key, value in utm_context.items():
            if key.startswith("utm_") and value:
                utm_params.append(f"{key}={value}")
        
        if not utm_params:
            return base_url
        
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}{'&'.join(utm_params)}"


# Instância global do tracker
utm_tracker = UTMTracker()


def extract_utm_from_referrer(referrer: str) -> Dict[str, str]:
    """
    Extrai UTM de URL de referência.
    
    Args:
        referrer: URL de referência
        
    Returns:
        Parâmetros UTM extraídos
    """
    return utm_tracker.extract_utm_from_url(referrer)


def build_bot_utm_context(platform: str, interaction_type: str) -> Dict[str, str]:
    """
    Constrói contexto UTM para interações do bot.
    
    Args:
        platform: Plataforma de origem
        interaction_type: Tipo de interação
        
    Returns:
        Contexto UTM
    """
    return utm_tracker.build_utm_context({
        "platform": platform,
        "type": interaction_type
    })

