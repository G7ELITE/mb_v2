"""
Testes para o sistema de confirmação LLM-first com guardrails.

Testa o ConfirmationGate, AutomationHook e lógica de TTL.
"""
import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Imports do sistema
try:
    from app.core.confirmation_gate import ConfirmationGate, ConfirmationResult
    from app.core.automation_hook import AutomationHook
    from app.data.schemas import Env, Lead, Message, Action
except ImportError:
    # Mock para quando dependências não estão disponíveis
    ConfirmationGate = None
    ConfirmationResult = None
    AutomationHook = None
    Action = type('Action', (), {})


@pytest.mark.skipif(ConfirmationGate is None, reason="Dependencies not available")
class TestConfirmationGate:
    """Testes para o gate de confirmação."""
    
    @pytest.fixture
    def mock_env(self):
        """Cria um ambiente mock para testes."""
        lead = Mock()
        lead.id = 123
        lead.name = "Test Lead"
        lead.channel = "telegram"
        
        message1 = Mock()
        message1.text = "Você consegue fazer um depósito?"
        message1.sender = "bot"
        
        message2 = Mock()
        message2.text = "sim consigo"
        message2.sender = "user"
        
        messages = [message1, message2]
        
        env = Mock()
        env.lead = lead
        env.messages_window = messages
        env.snapshot = Mock()
        env.snapshot.agreements = {"can_deposit": None}
        
        return env
    
    @pytest.fixture
    def confirmation_gate(self):
        """Cria instância do gate para testes."""
        gate = ConfirmationGate()
        gate.contexto_service = Mock()
        gate.openai_client = None  # Desabilitar OpenAI para testes determinísticos
        return gate
    
    @pytest.mark.asyncio
    async def test_no_pending_confirmations(self, confirmation_gate, mock_env):
        """Testa que sem confirmações pendentes, nada é processado."""
        
        # Mock: sem confirmações pendentes
        confirmation_gate.contexto_service.obter_contexto.return_value = Mock()
        confirmation_gate.contexto_service.obter_contexto.return_value.aguardando = None
        
        with patch.object(confirmation_gate, '_get_pending_confirmations', return_value=[]):
            result = await confirmation_gate.process_message(mock_env)
        
        assert not result.handled
        assert result.reason == "no_pending_confirmations"
    
    @pytest.mark.asyncio
    async def test_deterministic_yes_confirmation(self, confirmation_gate, mock_env):
        """Testa confirmação determinística 'sim'."""
        
        # Mock: confirmação pendente
        pending = [{"target": "confirm_can_deposit", "source": "context"}]
        
        with patch.object(confirmation_gate, '_get_pending_confirmations', return_value=pending):
            mock_action = Mock()
            mock_action.action_type = "set_facts"
            mock_action.facts = {"agreements.can_deposit": True}
            with patch.object(confirmation_gate, '_create_confirmation_actions', return_value=[mock_action]) as mock_create_actions:
                result = await confirmation_gate.process_message(mock_env)
        
        assert result.handled
        assert result.target == "confirm_can_deposit"
        assert result.polarity == "yes"
        assert result.source == "fallback"
        assert result.confidence >= 0.70
        mock_create_actions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deterministic_no_confirmation(self, confirmation_gate, mock_env):
        """Testa confirmação determinística 'não'."""
        
        # Modificar mensagem para 'não'
        mock_env.messages_window[-1].text = "não consigo"
        pending = [{"target": "confirm_can_deposit", "source": "context"}]
        
        with patch.object(confirmation_gate, '_get_pending_confirmations', return_value=pending):
            mock_action1 = Mock()
            mock_action1.action_type = "set_facts"
            mock_action1.facts = {"agreements.can_deposit": False}
            mock_action2 = Mock()
            mock_action2.action_type = "send_message"
            mock_action2.automation_id = "deposit_help"
            with patch.object(confirmation_gate, '_create_confirmation_actions', return_value=[mock_action1, mock_action2]) as mock_create_actions:
                result = await confirmation_gate.process_message(mock_env)
        
        assert result.handled
        assert result.target == "confirm_can_deposit"
        assert result.polarity == "no"
        assert result.source == "fallback"
        assert result.confidence >= 0.70
        mock_create_actions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ambiguous_message_not_confirmed(self, confirmation_gate, mock_env):
        """Testa que mensagens ambíguas não são confirmadas."""
        
        # Mensagem ambígua
        mock_env.messages_window[-1].text = "talvez amanhã"
        pending = [{"target": "confirm_can_deposit", "source": "context"}]
        
        with patch.object(confirmation_gate, '_get_pending_confirmations', return_value=pending):
            result = await confirmation_gate.process_message(mock_env)
        
        assert not result.handled
        assert result.reason == "deterministic_no_match"
    
    @pytest.mark.asyncio
    async def test_ttl_expired_confirmation(self, confirmation_gate, mock_env):
        """Testa que confirmações expiradas (TTL) não são processadas."""
        
        # Mock contexto com TTL expirado
        expired_ttl = int(time.time()) - 100  # 100 segundos atrás
        mock_contexto = Mock()
        mock_contexto.aguardando = {
            "tipo": "confirmacao",
            "fato": "confirm_can_deposit",
            "ttl": expired_ttl
        }
        
        confirmation_gate.contexto_service.obter_contexto.return_value = mock_contexto
        
        with patch.object(confirmation_gate, '_is_target_valid', return_value=True):
            result = await confirmation_gate.process_message(mock_env)
        
        assert not result.handled
        assert result.reason == "no_pending_confirmations"
    
    @pytest.mark.asyncio
    async def test_target_whitelist_validation(self, confirmation_gate, mock_env):
        """Testa validação da whitelist de targets."""
        
        # Target inválido (não na whitelist)
        pending = [{"target": "invalid_target", "source": "context"}]
        
        with patch.object(confirmation_gate, '_get_pending_confirmations', return_value=pending):
            with patch.object(confirmation_gate, '_is_target_valid', return_value=False):
                result = await confirmation_gate.process_message(mock_env)
        
        assert not result.handled
        assert result.reason == "no_pending_confirmations"
    
    @pytest.mark.asyncio
    async def test_create_confirmation_actions_yes(self, confirmation_gate):
        """Testa criação de ações para confirmação 'sim'."""
        
        result = ConfirmationResult(
            handled=True,
            target="confirm_can_deposit",
            polarity="yes"
        )
        
        # Mock target config
        target_config = {
            "on_yes": {
                "facts": {"agreements.can_deposit": True}
            }
        }
        
        with patch.object(confirmation_gate, '_get_target_config', return_value=target_config):
            actions = await confirmation_gate._create_confirmation_actions(result, 123)
        
        assert len(actions) == 2  # set_facts + clear_waiting
        assert actions[0].action_type == "set_facts"
        assert actions[0].facts == {"agreements.can_deposit": True}
        assert actions[1].action_type == "clear_waiting"
    
    @pytest.mark.asyncio
    async def test_create_confirmation_actions_no(self, confirmation_gate):
        """Testa criação de ações para confirmação 'não'."""
        
        result = ConfirmationResult(
            handled=True,
            target="confirm_can_deposit",
            polarity="no"
        )
        
        # Mock target config
        target_config = {
            "on_no": {
                "facts": {"agreements.can_deposit": False},
                "automation": "deposit_help"
            }
        }
        
        with patch.object(confirmation_gate, '_get_target_config', return_value=target_config):
            actions = await confirmation_gate._create_confirmation_actions(result, 123)
        
        assert len(actions) == 3  # set_facts + send_message + clear_waiting
        assert actions[0].action_type == "set_facts"
        assert actions[0].facts == {"agreements.can_deposit": False}
        assert actions[1].action_type == "send_message"
        assert actions[1].automation_id == "deposit_help"
        assert actions[2].action_type == "clear_waiting"


@pytest.mark.skipif(AutomationHook is None, reason="Dependencies not available")
class TestAutomationHook:
    """Testes para o hook de automação."""
    
    @pytest.fixture
    def automation_hook(self):
        """Cria instância do hook para testes."""
        hook = AutomationHook()
        hook.contexto_service = Mock()
        return hook
    
    @pytest.mark.asyncio
    async def test_hook_sets_waiting_state(self, automation_hook):
        """Testa que o hook define estado de aguardando para automação com expects_reply."""
        
        automation_id = "ask_deposit_for_test"
        lead_id = 123
        
        # Mock do catálogo
        mock_catalog = {
            "ask_deposit_for_test": {
                "id": "ask_deposit_for_test",
                "message": "Você consegue fazer um depósito?",
                "expects_reply": {
                    "target": "confirm_can_deposit"
                }
            }
        }
        
        # Mock dos targets
        mock_targets = {
            "confirm_can_deposit": {
                "max_age_minutes": 30
            }
        }
        
        with patch('builtins.open', mock_open_yaml(mock_catalog)):
            with patch.object(automation_hook, '_load_confirm_targets', return_value=mock_targets):
                await automation_hook.on_automation_sent(automation_id, lead_id, True)
        
        # Verificar que definir_aguardando_confirmacao foi chamado
        automation_hook.contexto_service.definir_aguardando_confirmacao.assert_called_once_with(
            lead_id=lead_id,
            fato="confirm_can_deposit",
            ttl_segundos=1800  # 30 minutos * 60
        )
    
    @pytest.mark.asyncio
    async def test_hook_skips_non_reply_automation(self, automation_hook):
        """Testa que o hook ignora automações sem expects_reply."""
        
        automation_id = "simple_message"
        lead_id = 123
        
        # Mock do catálogo sem expects_reply
        mock_catalog = {
            "simple_message": {
                "id": "simple_message",
                "message": "Mensagem simples"
            }
        }
        
        with patch('builtins.open', mock_open_yaml(mock_catalog)):
            await automation_hook.on_automation_sent(automation_id, lead_id, True)
        
        # Verificar que definir_aguardando_confirmacao NÃO foi chamado
        automation_hook.contexto_service.definir_aguardando_confirmacao.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_hook_calculates_correct_ttl(self, automation_hook):
        """Testa que o hook calcula TTL correto em segundos."""
        
        automation_id = "ask_broker_preference"
        lead_id = 123
        
        # Mock com 15 minutos de TTL
        mock_catalog = {
            "ask_broker_preference": {
                "id": "ask_broker_preference",
                "expects_reply": {
                    "target": "confirm_broker_choice"
                }
            }
        }
        
        mock_targets = {
            "confirm_broker_choice": {
                "max_age_minutes": 15
            }
        }
        
        with patch('builtins.open', mock_open_yaml(mock_catalog)):
            with patch.object(automation_hook, '_load_confirm_targets', return_value=mock_targets):
                await automation_hook.on_automation_sent(automation_id, lead_id, True)
        
        # Verificar TTL correto (15 min * 60 = 900 segundos)
        automation_hook.contexto_service.definir_aguardando_confirmacao.assert_called_once_with(
            lead_id=lead_id,
            fato="confirm_broker_choice",
            ttl_segundos=900
        )


class TestTTLLogic:
    """Testes específicos para lógica de TTL."""
    
    @pytest.mark.asyncio
    async def test_pending_confirmation_within_ttl(self):
        """Testa que confirmação dentro do TTL é considerada válida."""
        
        gate = ConfirmationGate()
        
        # Criar contexto com TTL válido (30 min no futuro)
        valid_ttl = int(time.time()) + 1800
        mock_contexto = Mock()
        mock_contexto.aguardando = {
            "tipo": "confirmacao",
            "fato": "confirm_can_deposit",
            "ttl": valid_ttl
        }
        
        mock_env = Mock()
        mock_env.lead = Mock()
        mock_env.lead.id = 123
        
        with patch.object(gate, '_is_target_valid', return_value=True):
            pending = await gate._get_pending_confirmations(mock_contexto, mock_env)
        
        assert len(pending) == 1
        assert pending[0]["target"] == "confirm_can_deposit"
    
    @pytest.mark.asyncio
    async def test_pending_confirmation_expired_ttl(self):
        """Testa que confirmação com TTL expirado é ignorada."""
        
        gate = ConfirmationGate()
        
        # Criar contexto com TTL expirado
        expired_ttl = int(time.time()) - 100
        mock_contexto = Mock()
        mock_contexto.aguardando = {
            "tipo": "confirmacao",
            "fato": "confirm_can_deposit",
            "ttl": expired_ttl
        }
        
        mock_env = Mock()
        mock_env.lead = Mock()
        mock_env.lead.id = 123
        
        with patch.object(gate, '_is_target_valid', return_value=True):
            pending = await gate._get_pending_confirmations(mock_contexto, mock_env)
        
        assert len(pending) == 0


# Helpers para testes
def mock_open_yaml(data_dict):
    """Mock para abrir arquivos YAML com dados específicos."""
    import yaml
    yaml_content = yaml.dump(data_dict)
    
    def mock_open_func(*args, **kwargs):
        mock_file = MagicMock()
        mock_file.read.return_value = yaml_content
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = None
        return mock_file
    
    return mock_open_func


if __name__ == "__main__":
    # Executar testes se chamado diretamente
    pytest.main([__file__, "-v"])