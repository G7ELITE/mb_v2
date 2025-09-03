"""
Tests for confirmation flow functionality
"""
import pytest
import time
from unittest.mock import Mock, patch
from app.core.confirmation_gate import ConfirmationGate, ConfirmationResult
from app.core.automation_hook import AutomationHook
from app.core.orchestrator import handle_fallback_flow
from app.data.schemas import Env, Lead
from app.infra.logging import log_structured


class TestConfirmationFlow:
    """Test confirmation flow from hook to gate to orchestrator."""
    
    @pytest.fixture
    def mock_contexto_service(self):
        """Mock contexto service."""
        service = Mock()
        service.obter_contexto = Mock()
        service.atualizar_contexto = Mock()
        return service
    
    @pytest.fixture
    def mock_lead_env(self):
        """Mock lead environment."""
        lead = Lead(id=123, name="Test User", platform_user_id="test_123")
        env = Mock(spec=Env)
        env.lead = lead
        env.messages_window = []
        env.snapshot = {}
        return env
    
    def test_automation_hook_sets_waiting_state(self, mock_contexto_service):
        """Test that automation hook correctly sets waiting state."""
        hook = AutomationHook()
        hook.contexto_service = mock_contexto_service
        
        # Mock automation config
        with patch.object(hook, '_get_automation_config') as mock_get_config:
            mock_get_config.return_value = {
                "id": "ask_deposit_for_test",
                "expects_reply": {
                    "target": "confirm_can_deposit"
                },
                "output": {
                    "text": "Can you make a deposit?"
                }
            }
            
            with patch.object(hook, '_get_target_ttl') as mock_get_ttl:
                mock_get_ttl.return_value = 30  # 30 minutes
                
                # Execute hook
                import asyncio
                asyncio.run(hook.on_automation_sent(
                    automation_id="ask_deposit_for_test",
                    lead_id=123,
                    success=True,
                    provider_message_id="msg_456",
                    prompt_text="Can you make a deposit?"
                ))
                
                # Verify context was updated
                mock_contexto_service.atualizar_contexto.assert_called_once()
                call_args = mock_contexto_service.atualizar_contexto.call_args
                
                assert call_args[1]['lead_id'] == 123
                assert 'aguardando' in call_args[1]
                
                aguardando = call_args[1]['aguardando']
                assert aguardando['tipo'] == 'confirmacao'
                assert aguardando['target'] == 'confirm_can_deposit'
                assert aguardando['automation_id'] == 'ask_deposit_for_test'
                assert aguardando['lead_id'] == 123
                assert 'ttl' in aguardando
    
    def test_gate_processes_yes_confirmation(self, mock_contexto_service, mock_lead_env):
        """Test gate correctly processes 'yes' confirmation."""
        gate = ConfirmationGate()
        gate.contexto_service = mock_contexto_service
        
        # Mock lead message saying "sim"
        mock_message = Mock()
        mock_message.text = "sim"
        mock_lead_env.messages_window = [mock_message]
        
        # Mock context with waiting confirmation
        mock_context = {
            "aguardando": {
                "tipo": "confirmacao",
                "target": "confirm_can_deposit",
                "automation_id": "ask_deposit_for_test",
                "ttl": int(time.time()) + 1800,  # 30 minutes from now
                "created_at": int(time.time())
            }
        }
        mock_contexto_service.obter_contexto.return_value = mock_context
        
        # Mock pending confirmations
        with patch.object(gate, '_get_pending_confirmations') as mock_get_pending:
            mock_get_pending.return_value = [{
                "target": "confirm_can_deposit",
                "automation_id": "ask_deposit_for_test",
                "ttl": int(time.time()) + 1800
            }]
            
            # Mock deterministic response
            with patch.object(gate, '_deterministic_short_response') as mock_det_response:
                mock_result = ConfirmationResult(
                    handled=True,
                    target="confirm_can_deposit",
                    polarity="yes",
                    source="deterministic"
                )
                mock_det_response.return_value = mock_result
                
                with patch.object(gate, '_create_confirmation_actions') as mock_create_actions:
                    mock_create_actions.return_value = [{"type": "set_facts", "facts": {"agreements.can_deposit": True}}]
                    
                    with patch.object(gate, '_store_idempotency'):
                        with patch.object(gate, '_acquire_lead_lock', return_value=True):
                            with patch.object(gate, '_release_lead_lock'):
                                with patch.object(gate, '_is_short_response', return_value=True):
                                    with patch('app.settings.settings.GATE_YESNO_DETERMINISTICO', True):
                                        # Execute gate
                                        import asyncio
                                        result = asyncio.run(gate.process_message(mock_lead_env))
                                        
                                        # Verify confirmation was handled
                                        assert result.handled == True
                                        assert result.polarity == "yes"
                                        assert result.target == "confirm_can_deposit"
    
    def test_orchestrator_fallback_for_empty_catalog(self, mock_lead_env):
        """Test orchestrator fallback when catalog is empty."""
        # Mock empty catalogs
        with patch('app.core.orchestrator.load_catalog', return_value=[]):
            with patch('app.core.orchestrator.load_procedures', return_value=[]):
                
                # Mock simple confirmation message
                mock_message = Mock()
                mock_message.text = "sim"
                mock_lead_env.messages_window = [mock_message]
                
                import asyncio
                result = asyncio.run(handle_fallback_flow(mock_lead_env))
                
                # Should detect empty catalog
                assert 'actions' in result
                assert len(result['actions']) == 1
                
                message_text = result['actions'][0].text
                assert "configuração inicial" in message_text or "automações estão sendo preparadas" in message_text
    
    def test_orchestrator_orphaned_confirmation_fallback(self, mock_lead_env):
        """Test orchestrator fallback for orphaned confirmation."""
        # Mock non-empty catalogs but orphaned confirmation
        with patch('app.core.orchestrator.load_catalog', return_value=[{"id": "test"}]):
            with patch('app.core.orchestrator.load_procedures', return_value=[{"id": "test"}]):
                
                # Mock simple confirmation message
                mock_message = Mock()
                mock_message.text = "sim"
                mock_lead_env.messages_window = [mock_message]
                
                import asyncio
                result = asyncio.run(handle_fallback_flow(mock_lead_env))
                
                # Should detect orphaned confirmation
                assert 'actions' in result
                assert len(result['actions']) == 1
                
                message_text = result['actions'][0].text
                assert "confirmação" in message_text and "não tenho uma pergunta ativa" in message_text


class TestEmptyCatalogHandling:
    """Test handling of empty catalog scenarios."""
    
    def test_catalog_stats_empty_state(self):
        """Test catalog statistics for empty state."""
        from app.api.catalog_reset import CatalogResetService
        
        service = CatalogResetService()
        
        # Mock empty YAML files
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open_yaml([])):
                import asyncio
                stats = asyncio.run(service.get_catalog_stats())
                
                assert stats['automations_count'] == 0
                assert stats['procedures_count'] == 0 
                assert stats['catalog_empty'] == True
                assert stats['procedures_empty'] == True
    
    def test_catalog_reset_creates_empty_files(self):
        """Test that catalog reset creates proper empty YAML files."""
        from app.api.catalog_reset import CatalogResetService
        
        service = CatalogResetService()
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open_yaml([])) as mock_open:
                import asyncio
                result = asyncio.run(service.reset_catalogs())
                
                assert result['catalog_reset'] == True
                assert result['procedures_reset'] == True
                assert 'catalog.yml' in result['files_reset']
                assert 'procedures.yml' in result['files_reset']


def mock_open_yaml(data):
    """Mock open function for YAML files."""
    import yaml
    from unittest.mock import mock_open
    
    return mock_open(read_data=yaml.dump(data))
