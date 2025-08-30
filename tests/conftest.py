"""
Configurações globais para testes.
"""
import pytest
import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configurar variáveis de ambiente para testes
os.environ["APP_ENV"] = "test"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_NAME"] = "manyblack_v2_test"
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
os.environ["TELEGRAM_WEBHOOK_SECRET"] = "test_secret"
os.environ["JWT_SECRET"] = "test_jwt_secret"


@pytest.fixture
def mock_env():
    """Fixture com ambiente mock para testes."""
    from app.data.schemas import Env, Lead, Snapshot, Message
    
    return Env(
        lead=Lead(id=1, nome="Test User", lang="pt-BR"),
        snapshot=Snapshot(
            accounts={"quotex": "desconhecido", "nyrion": "desconhecido"},
            deposit={"status": "nenhum"},
            agreements={"can_deposit": False},
            flags={"explained": False}
        ),
        candidates={"email": "test@example.com"},
        messages_window=[Message(id="msg1", text="Quero testar")],
        apply=True
    )


@pytest.fixture
def mock_telegram_update():
    """Fixture com update mock do Telegram."""
    return {
        "update_id": 123,
        "message": {
            "message_id": 456,
            "from": {
                "id": 789,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 789,
                "type": "private"
            },
            "text": "Olá, quero testar o robô"
        }
    }

