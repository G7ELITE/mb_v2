import logging
import json
import sys


def configure_logging():
    """Configura logging estruturado em JSON para o projeto."""
    h = logging.StreamHandler(sys.stdout)
    f = logging.Formatter('%(message)s')
    h.setFormatter(f)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(h)


def log_structured(level: str, event: str, data=None, **kwargs):
    """Helper para logs estruturados em JSON."""
    log_entry = {
        "event": event,
        "level": level,
    }
    
    # Suportar tanto dicionário como kwargs
    if data:
        log_entry.update(data)
    if kwargs:
        log_entry.update(kwargs)
        
    logging.getLogger().info(json.dumps(log_entry))
