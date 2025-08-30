"""
Testes básicos da aplicação principal.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Testa endpoint raiz."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ManyBlack V2"


def test_health_endpoint():
    """Testa endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_info_endpoint():
    """Testa endpoint de informações."""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ManyBlack V2"
    assert data["version"] == "2.0.0"
    assert "features" in data


def test_telegram_info_endpoint():
    """Testa endpoint de informações do Telegram."""
    response = client.get("/channels/telegram/info")
    assert response.status_code == 200
    data = response.json()
    assert data["channel"] == "telegram"


def test_whatsapp_info_endpoint():
    """Testa endpoint de informações do WhatsApp."""
    response = client.get("/channels/whatsapp/info")
    assert response.status_code == 200
    data = response.json()
    assert data["channel"] == "whatsapp"
    assert data["implemented"] == False

