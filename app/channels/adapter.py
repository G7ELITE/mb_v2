"""
Adapter para transformar payload unificado (texto/mídia/botões) para cada canal.
Transforma as ações do plano em formatos específicos de cada plataforma.
"""
from typing import Any, Dict, List


def to_telegram(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte payload unificado para formato do Telegram.
    
    Args:
        payload: Dicionário com estrutura unificada de ação
        
    Returns:
        Dicionário formatado para API do Telegram
    """
    result = {
        "_telegram_mapped": True,
        "src": payload
    }
    
    action_type = payload.get("type", "")
    
    if action_type == "send_message":
        result.update({
            "method": "sendMessage",
            "text": payload.get("text", ""),
            "parse_mode": "HTML"
        })
        
        # Adicionar botões se existirem
        buttons = payload.get("buttons")
        if buttons:
            result["reply_markup"] = _build_telegram_keyboard(buttons)
    
    elif action_type == "send_photo":
        result.update({
            "method": "sendPhoto",
            "photo": payload.get("media", {}).get("url", ""),
            "caption": payload.get("text", "")
        })
        
        buttons = payload.get("buttons")
        if buttons:
            result["reply_markup"] = _build_telegram_keyboard(buttons)
    
    return result


def to_whatsapp(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte payload unificado para formato do WhatsApp Business API.
    Placeholder para implementação futura.
    
    Args:
        payload: Dicionário com estrutura unificada de ação
        
    Returns:
        Dicionário formatado para WhatsApp Business API
    """
    return {
        "_whatsapp_mapped": True,
        "src": payload,
        "method": "send_message",
        "text": payload.get("text", "Mensagem não suportada no WhatsApp ainda")
    }


def _build_telegram_keyboard(buttons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Constrói keyboard inline do Telegram a partir de lista de botões.
    
    Args:
        buttons: Lista de dicionários com definição dos botões
        
    Returns:
        Objeto reply_markup para Telegram
    """
    inline_keyboard = []
    
    for button in buttons:
        btn_obj = {
            "text": button.get("label", "Botão")
        }
        
        kind = button.get("kind", "callback")
        if kind == "callback":
            btn_obj["callback_data"] = button.get("id", "unknown")
        elif kind == "url":
            btn_obj["url"] = button.get("url", "#")
        
        # Cada botão em uma linha por simplicidade
        inline_keyboard.append([btn_obj])
    
    return {"inline_keyboard": inline_keyboard}


def normalize_inbound_event(platform: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza evento de entrada de qualquer plataforma para formato unificado.
    
    Args:
        platform: Nome da plataforma (telegram, whatsapp, etc.)
        raw_data: Dados brutos do webhook
        
    Returns:
        Evento normalizado em formato unificado
    """
    if platform == "telegram":
        return _normalize_telegram_update(raw_data)
    elif platform == "whatsapp":
        return _normalize_whatsapp_update(raw_data)
    else:
        return {
            "platform": platform,
            "user_id": "unknown",
            "message_text": "",
            "raw": raw_data
        }


def _normalize_telegram_update(update: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza update do Telegram."""
    message = update.get("message", {})
    callback_query = update.get("callback_query", {})
    
    if callback_query:
        # Callback de botão
        return {
            "platform": "telegram",
            "user_id": str(callback_query.get("from", {}).get("id", "")),
            "message_text": callback_query.get("data", ""),
            "type": "callback",
            "raw": update
        }
    else:
        # Mensagem de texto
        return {
            "platform": "telegram",
            "user_id": str(message.get("from", {}).get("id", "")),
            "message_text": message.get("text", ""),
            "type": "text",
            "raw": update
        }


def _normalize_whatsapp_update(update: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza update do WhatsApp (placeholder)."""
    return {
        "platform": "whatsapp",
        "user_id": "unknown",
        "message_text": "",
        "type": "text",
        "raw": update
    }
