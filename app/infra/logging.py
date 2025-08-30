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


def log_structured(level: str, event: str, **kwargs):
    """Helper para logs estruturados em JSON."""
    log_entry = {
        "event": event,
        "level": level,
        **kwargs
    }
    logging.getLogger().info(json.dumps(log_entry))
