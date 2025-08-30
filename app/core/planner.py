"""
Planner - Renderizador de planos

Renderiza automações do catálogo em actions (texto/mídia/botões/track/set_facts).
Aplica templates dinâmicos e configurações específicas do contexto.
"""
import logging
import re
from typing import Dict, Any, List, Optional
from string import Template

from app.data.schemas import Action, Plan

logger = logging.getLogger(__name__)


def render_plan(plan: Plan, context: Dict[str, Any]) -> Plan:
    """
    Renderiza plano aplicando contexto e templates.
    
    Args:
        plan: Plano original
        context: Contexto para renderização
        
    Returns:
        Plano renderizado
    """
    logger.info(f"Renderizando plano com {len(plan.actions)} ações")
    
    rendered_actions = []
    
    for action in plan.actions:
        rendered_action = render_action(action, context)
        rendered_actions.append(rendered_action)
    
    plan.actions = rendered_actions
    return plan


def render_action(action: Action, context: Dict[str, Any]) -> Action:
    """
    Renderiza uma ação individual aplicando templates.
    
    Args:
        action: Ação original
        context: Contexto para renderização
        
    Returns:
        Ação renderizada
    """
    # Criar cópia da ação para não modificar original
    rendered_dict = action.dict() if hasattr(action, 'dict') else action.__dict__.copy()
    
    # Renderizar texto se existir
    if rendered_dict.get("text"):
        rendered_dict["text"] = render_template(rendered_dict["text"], context)
    
    # Renderizar URLs se existirem
    if rendered_dict.get("url"):
        rendered_dict["url"] = render_template(rendered_dict["url"], context)
    
    # Renderizar botões se existirem
    if rendered_dict.get("buttons"):
        rendered_dict["buttons"] = render_buttons(rendered_dict["buttons"], context)
    
    # Processar set_facts se existir
    if rendered_dict.get("set_facts"):
        rendered_dict["set_facts"] = render_set_facts(rendered_dict["set_facts"], context)
    
    # Processar tracking se existir
    if rendered_dict.get("track"):
        rendered_dict["track"] = render_tracking(rendered_dict["track"], context)
    
    return Action(**rendered_dict)


def render_template(template_text: str, context: Dict[str, Any]) -> str:
    """
    Renderiza template usando contexto fornecido.
    
    Args:
        template_text: Texto com placeholders
        context: Contexto para substituição
        
    Returns:
        Texto renderizado
    """
    if not template_text:
        return template_text
    
    try:
        # Usar Template do Python para substituições seguras
        template = Template(template_text)
        
        # Aplicar contexto com fallbacks seguros
        safe_context = build_safe_context(context)
        
        return template.safe_substitute(safe_context)
        
    except Exception as e:
        logger.warning(f"Erro ao renderizar template: {str(e)}")
        return template_text


def render_buttons(buttons: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Renderiza lista de botões aplicando templates.
    
    Args:
        buttons: Lista de botões
        context: Contexto para renderização
        
    Returns:
        Lista de botões renderizados
    """
    rendered_buttons = []
    
    for button in buttons:
        rendered_button = button.copy()
        
        # Renderizar label
        if "label" in rendered_button:
            rendered_button["label"] = render_template(rendered_button["label"], context)
        
        # Renderizar URL se for botão de URL
        if "url" in rendered_button:
            rendered_button["url"] = render_template(rendered_button["url"], context)
        
        rendered_buttons.append(rendered_button)
    
    return rendered_buttons


def render_set_facts(set_facts: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderiza set_facts aplicando contexto.
    
    Args:
        set_facts: Fatos a serem definidos
        context: Contexto para renderização
        
    Returns:
        Set_facts renderizado
    """
    rendered_facts = {}
    
    for key, value in set_facts.items():
        if isinstance(value, str):
            rendered_facts[key] = render_template(value, context)
        else:
            rendered_facts[key] = value
    
    return rendered_facts


def render_tracking(track: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Renderiza configurações de tracking.
    
    Args:
        track: Configurações de tracking
        context: Contexto para renderização
        
    Returns:
        Tracking renderizado
    """
    rendered_track = track.copy()
    
    # Renderizar campos string no tracking
    for key, value in rendered_track.items():
        if isinstance(value, str):
            rendered_track[key] = render_template(value, context)
    
    return rendered_track


def build_safe_context(context: Dict[str, Any]) -> Dict[str, str]:
    """
    Constrói contexto seguro para templates com fallbacks.
    
    Args:
        context: Contexto original
        
    Returns:
        Contexto seguro com strings
    """
    safe_context = {}
    
    # Variáveis padrão sempre disponíveis
    defaults = {
        "lead_name": "usuário",
        "deposit_help_link": "https://example.com/help",
        "support_link": "https://example.com/support",
        "bot_name": "ManyBlack",
    }
    
    # Aplicar defaults
    safe_context.update(defaults)
    
    # Extrair dados do contexto de forma segura
    if "lead" in context:
        lead = context["lead"]
        if lead.get("nome"):
            safe_context["lead_name"] = str(lead["nome"])
    
    if "snapshot" in context:
        snapshot = context["snapshot"]
        
        # Informações de depósito
        deposit = snapshot.get("deposit", {})
        if deposit.get("amount"):
            safe_context["deposit_amount"] = str(deposit["amount"])
        
        # Status das contas
        accounts = snapshot.get("accounts", {})
        if accounts.get("quotex") != "desconhecido":
            safe_context["quotex_status"] = str(accounts["quotex"])
        if accounts.get("nyrion") != "desconhecido":
            safe_context["nyrion_status"] = str(accounts["nyrion"])
    
    # Converter tudo para string
    return {k: str(v) for k, v in safe_context.items()}


def apply_personalization(action: Action, lead_data: Dict[str, Any]) -> Action:
    """
    Aplica personalização baseada nos dados do lead.
    
    Args:
        action: Ação a ser personalizada
        lead_data: Dados do lead
        
    Returns:
        Ação personalizada
    """
    # Aplicar saudação personalizada
    if action.text and lead_data.get("nome"):
        name = lead_data["nome"]
        
        # Substituir saudações genéricas por personalizadas
        text = action.text
        text = text.replace("usuário", name)
        text = text.replace("Usuário", name.title())
        
        action.text = text
    
    return action


def optimize_message_length(text: str, max_length: int = 4096) -> str:
    """
    Otimiza comprimento da mensagem para limites da plataforma.
    
    Args:
        text: Texto original
        max_length: Comprimento máximo
        
    Returns:
        Texto otimizado
    """
    if len(text) <= max_length:
        return text
    
    # Truncar preservando palavras
    truncated = text[:max_length - 3]
    
    # Encontrar último espaço para não cortar palavra
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:  # Só truncar se não perder muito conteúdo
        truncated = truncated[:last_space]
    
    return truncated + "..."


def inject_utm_tracking(action: Action, utm_context: Dict[str, Any]) -> Action:
    """
    Injeta parâmetros UTM nos links da ação.
    
    Args:
        action: Ação original
        utm_context: Contexto UTM
        
    Returns:
        Ação com UTM injetado
    """
    # Injetar UTM em URLs diretas
    if action.url:
        action.url = add_utm_params(action.url, utm_context)
    
    # Injetar UTM em botões com URL
    if action.buttons:
        for button in action.buttons:
            if button.get("url"):
                button["url"] = add_utm_params(button["url"], utm_context)
    
    return action


def add_utm_params(url: str, utm_context: Dict[str, Any]) -> str:
    """
    Adiciona parâmetros UTM à URL.
    
    Args:
        url: URL original
        utm_context: Contexto UTM
        
    Returns:
        URL com parâmetros UTM
    """
    if not url or not utm_context:
        return url
    
    # Construir parâmetros UTM
    utm_params = []
    
    utm_mapping = {
        "source": "utm_source",
        "medium": "utm_medium", 
        "campaign": "utm_campaign",
        "term": "utm_term",
        "content": "utm_content"
    }
    
    for key, param in utm_mapping.items():
        if key in utm_context:
            utm_params.append(f"{param}={utm_context[key]}")
    
    if not utm_params:
        return url
    
    # Adicionar parâmetros à URL
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{'&'.join(utm_params)}"
