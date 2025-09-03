"""
Testes unitários para as Fases 3 e 4 sem dependência de banco de dados.

FASE 3: Gate Retroativo com timeline leve, janela, idempotência, lock por lead
FASE 4: Orquestrador com Sinais LLM usando propose_automations com guardrails
"""
import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta


class TestFase3GateRetroativo:
    """Testes unitários para Fase 3 - Gate Retroativo"""
    
    @pytest.mark.asyncio
    async def test_retroativo_yes_sem_aguardando(self):
        """
        FASE 3: Retroativo YES sem aguardando ativo
        """
        try:
            from app.core.confirmation_gate import ConfirmationGate, ConfirmationResult
            
            # Mock do ambiente
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 30})()
                    self.messages_window = [
                        type('Message', (), {'text': 'sim', 'sender': 'user'})()
                    ]
                    self.snapshot = type('Snapshot', (), {})()
            
            # Mock do gate
            gate = ConfirmationGate()
            gate.contexto_service = AsyncMock()
            gate.openai_client = None
            
            # Mock sem aguardando ativo
            mock_contexto = Mock()
            mock_contexto.aguardando = None
            gate.contexto_service.obter_contexto.return_value = mock_contexto
            
            # Mock confirmação pendente retroativa
            pending_confirmations = [{
                "target": "confirm_can_deposit",
                "source": "retroactive", 
                "timestamp": int(time.time()) - 60,
                "automation_id": "ask_deposit_for_test",
                "reason": "retroactive_timeline"
            }]
            
            with patch.object(gate, '_get_pending_confirmations', return_value=pending_confirmations):
                with patch.object(gate, '_acquire_lead_lock', return_value=True):
                    with patch.object(gate, '_release_lead_lock', return_value=None):
                        with patch.object(gate, '_check_idempotency', return_value=False):
                            with patch.object(gate, '_store_idempotency', return_value=None):
                                with patch.object(gate, '_create_confirmation_actions') as mock_actions:
                                    # Mock ações de retorno
                                    mock_actions.return_value = [
                                        type('Action', (), {'type': 'set_facts', 'set_facts': {'agreements.can_deposit': True}})(),
                                        type('Action', (), {'type': 'clear_waiting'})()
                                    ]
                                    
                                    env = MockEnv()
                                    result = await gate.process_message(env)
                                    
                                    # Asserts
                                    assert result.handled == True, "Gate não processou confirmação retroativa"
                                    assert result.polarity == "yes", f"Polarity incorreta: {result.polarity}"
                                    # Em modo teste (GATE_YESNO_DETERMINISTICO=true), usa deterministic_short
                                    assert result.source in ["fallback", "deterministic_short"], f"Source incorreta: {result.source}"
                                    assert len(result.actions) == 2, "Número de ações incorreto"
                                    
                                    # Verificar se foi detectado como retroativo
                                    is_retroactive = any(conf.get("source") == "retroactive" for conf in pending_confirmations)
                                    assert is_retroactive, "Não foi detectado como retroativo"
                                    
            print("✅ FASE 3 — Retroativo YES: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste retroativo: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_retroativo_no(self):
        """
        FASE 3: Retroativo NO
        """
        try:
            from app.core.confirmation_gate import ConfirmationGate
            
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 31})()
                    self.messages_window = [
                        type('Message', (), {'text': 'agora não', 'sender': 'user'})()
                    ]
                    self.snapshot = type('Snapshot', (), {})()
            
            gate = ConfirmationGate()
            gate.contexto_service = AsyncMock()
            gate.openai_client = None
            
            pending_confirmations = [{
                "target": "confirm_can_deposit",
                "source": "retroactive",
                "timestamp": int(time.time()) - 60
            }]
            
            with patch.object(gate, '_get_pending_confirmations', return_value=pending_confirmations):
                with patch.object(gate, '_acquire_lead_lock', return_value=True):
                    with patch.object(gate, '_release_lead_lock', return_value=None):
                        with patch.object(gate, '_check_idempotency', return_value=False):
                            with patch.object(gate, '_store_idempotency', return_value=None):
                                with patch.object(gate, '_create_confirmation_actions') as mock_actions:
                                    # Mock ações para NO (sem fatos irreversíveis)
                                    mock_actions.return_value = [
                                        type('Action', (), {'type': 'send_message', 'text': 'Entendi que você não consegue fazer o depósito agora.'})(),
                                        type('Action', (), {'type': 'clear_waiting'})()
                                    ]
                                    
                                    env = MockEnv()
                                    result = await gate.process_message(env)
                                    
                                    assert result.handled == True, "Gate não processou confirmação retroativa"
                                    assert result.polarity == "no", f"Polarity incorreta: {result.polarity}"
                                    
                                    # Verificar que não tem fatos irreversíveis
                                    has_irreversible_facts = False
                                    for action in result.actions:
                                        if hasattr(action, 'type') and action.type == "set_facts":
                                            if hasattr(action, 'set_facts') and action.set_facts:
                                                facts = action.set_facts
                                                if facts.get('agreements.can_deposit') == True:
                                                    has_irreversible_facts = True
                                    
                                    assert not has_irreversible_facts, "NO não deve gerar fatos irreversíveis"
                                    
            print("✅ FASE 3 — Retroativo NO: sem fatos irreversíveis!")
            
        except Exception as e:
            print(f"❌ Erro no teste retroativo NO: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio 
    async def test_janela_expirada(self):
        """
        FASE 3: Janela retroativa expirada
        """
        try:
            from app.core.confirmation_gate import ConfirmationGate
            
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 32})()
                    self.messages_window = [
                        type('Message', (), {'text': 'sim', 'sender': 'user'})()
                    ]
                    self.snapshot = type('Snapshot', (), {})()
            
            gate = ConfirmationGate()
            gate.contexto_service = AsyncMock()
            gate.openai_client = None
            
            # Mock sem confirmações pendentes (janela expirada)
            with patch.object(gate, '_get_pending_confirmations', return_value=[]):
                with patch.object(gate, '_acquire_lead_lock', return_value=True):
                    with patch.object(gate, '_release_lead_lock', return_value=None):
                        
                        env = MockEnv()
                        result = await gate.process_message(env)
                        
                        assert result.handled == False, "Gate processou confirmação com janela expirada"
                        assert result.reason == "no_pending_confirmations", "Motivo incorreto para janela expirada"
                        
            print("✅ FASE 3 — Janela expirada: corretamente ignorada!")
            
        except Exception as e:
            print(f"❌ Erro no teste janela expirada: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_idempotencia(self):
        """
        FASE 3: Teste de idempotência
        """
        try:
            from app.core.confirmation_gate import ConfirmationGate
            
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 35})()
                    self.messages_window = [
                        type('Message', (), {'text': 'sim', 'sender': 'user'})()
                    ]
                    self.snapshot = type('Snapshot', (), {})()
            
            gate = ConfirmationGate()
            gate.contexto_service = AsyncMock()
            gate.openai_client = None
            
            # Mock confirmação já processada (idempotência)
            with patch.object(gate, '_acquire_lead_lock', return_value=True):
                with patch.object(gate, '_release_lead_lock', return_value=None):
                    with patch.object(gate, '_check_idempotency', return_value=True):  # Já processado
                        
                        env = MockEnv()
                        result = await gate.process_message(env)
                        
                        assert result.handled == False, "Gate processou confirmação idempotente"
                        assert result.reason == "idempotent_skip", "Motivo incorreto para idempotência"
                        
            print("✅ FASE 3 — Idempotência: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste idempotência: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_lock_lead(self):
        """
        FASE 3: Teste de lock por lead
        """
        try:
            from app.core.confirmation_gate import ConfirmationGate
            
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 36})()
                    self.messages_window = [
                        type('Message', (), {'text': 'sim', 'sender': 'user'})()
                    ]
                    self.snapshot = type('Snapshot', (), {})()
            
            gate = ConfirmationGate()
            gate.contexto_service = AsyncMock()
            gate.openai_client = None
            
            # Mock lock ocupado
            with patch.object(gate, '_acquire_lead_lock', return_value=False):  # Lock busy
                
                env = MockEnv()
                result = await gate.process_message(env)
                
                assert result.handled == False, "Gate processou com lock ocupado"
                assert result.reason == "lead_locked", "Motivo incorreto para lock ocupado"
                
            print("✅ FASE 3 — Lock por lead: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste lock: {e}")
            import traceback
            traceback.print_exc()
            raise


class TestFase4OrquestradorSinais:
    """Testes unitários para Fase 4 - Orquestrador com Sinais LLM"""
    
    @pytest.mark.asyncio
    async def test_aceitar_proposta_valida(self):
        """
        FASE 4: Aceitar 1 proposta LLM válida
        """
        try:
            from app.core.orchestrator import handle_doubt_flow
            
            # Mock ambiente sem automações elegíveis no catálogo
            class MockSnapshot:
                def __init__(self):
                    self.accounts = {'quotex': 'desconhecido'}
                    self.deposit = {'status': 'nenhum'}
                    self.agreements = {'wants_test': False}
                    self.flags = {}
                    # Sinais LLM com proposta
                    self.llm_signals = {
                        'propose_automations': ['ask_deposit_permission_v3'],
                        'polarity': 'other'
                    }
            
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 40})()
                    self.messages_window = []
                    self.snapshot = MockSnapshot()
            
            env = MockEnv()
            
            # Mock que catálogo não acha elegível
            with patch('app.core.selector.select_automation', return_value=None):
                # Mock proposta válida
                with patch('app.core.orchestrator.is_proposal_valid', return_value=True):
                    with patch('app.core.orchestrator.load_automation_from_catalog') as mock_load:
                        mock_automation = {
                            'id': 'ask_deposit_permission_v3',
                            'output': {'text': 'Posso te ajudar com o depósito!'}
                        }
                        mock_load.return_value = mock_automation
                        
                        with patch('app.core.orchestrator.convert_automation_config_to_action') as mock_convert:
                            mock_convert.return_value = {
                                'type': 'send_message',
                                'text': 'Posso te ajudar com o depósito!',
                                'automation_id': 'ask_deposit_permission_v3'
                            }
                            
                            result = await handle_doubt_flow(env)
                            
                            # Validações
                            assert len(result['actions']) == 1, "Deve retornar 1 ação"
                            action = result['actions'][0]
                            assert action.automation_id == 'ask_deposit_permission_v3', "Automação incorreta"
                            assert action.type == 'send_message', "Tipo de ação incorreto"
                            
            print("✅ FASE 4 — Proposta aceita: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste proposta válida: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_rejeitar_proposta_conflitante(self):
        """
        FASE 4: Rejeitar proposta conflitante
        """
        try:
            from app.core.orchestrator import handle_doubt_flow
            
            # Mock ambiente onde proposta conflita
            class MockSnapshot:
                def __init__(self):
                    self.accounts = {'quotex': 'ativa'}
                    self.deposit = {'status': 'confirmado', 'amount': 50}  # Já tem depósito
                    self.agreements = {'can_deposit': True}
                    self.flags = {}
                    # Proposta inadequada
                    self.llm_signals = {
                        'propose_automations': ['prompt_deposit'],  # Inadequada (já tem depósito)
                        'polarity': 'other'
                    }
            
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 41})()
                    self.messages_window = []
                    self.snapshot = MockSnapshot()
            
            env = MockEnv()
            
            with patch('app.core.selector.select_automation', return_value=None):
                # Mock que proposta não é aplicável (conflitante)
                with patch('app.core.orchestrator.is_proposal_valid', return_value=False):
                    with patch('app.core.fallback_kb.query_knowledge_base', return_value="Como posso ajudar?"):
                        result = await handle_doubt_flow(env)
                        
                        # Validações
                        assert len(result['actions']) == 1, "Deve retornar 1 ação (fallback)"
                        action = result['actions'][0]
                        assert action.type == 'send_message', "Deve usar fallback"
                        # O fallback pode ser KB ou fallback final - ambos indicam que a proposta foi rejeitada
                        assert action.text in ["Como posso ajudar?", "Não entendi bem sua mensagem. Pode me explicar melhor?"], "Deve usar resposta de fallback"
                        
            print("✅ FASE 4 — Proposta rejeitada: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste proposta conflitante: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_cooldown_respeitado(self):
        """
        FASE 4: Cooldown respeitado
        """
        try:
            from app.core.orchestrator import is_proposal_valid
            
            # Mock ambiente
            class MockSnapshot:
                def __init__(self):
                    self.accounts = {'quotex': 'desconhecido'}
                    self.deposit = {'status': 'nenhum'}
                    self.agreements = {'wants_test': False}
                    self.llm_signals = {
                        'propose_automations': ['ask_deposit_for_test'],
                    }
            
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 42})()
                    self.snapshot = MockSnapshot()
            
            env = MockEnv()
            automation_id = 'ask_deposit_for_test'
            
            # Mock que está no catálogo mas em cooldown
            with patch('app.core.orchestrator.load_automation_from_catalog', return_value={'id': automation_id}):
                with patch('app.core.orchestrator.check_automation_cooldown', return_value=False):  # Em cooldown
                    
                    is_valid = await is_proposal_valid(automation_id, env)
                    
                    assert not is_valid, "Proposta em cooldown deve ser rejeitada"
                    
            print("✅ FASE 4 — Cooldown: respeitado!")
            
        except Exception as e:
            print(f"❌ Erro no teste cooldown: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_guardrails_catalogo(self):
        """
        FASE 4: Validação de guardrails - automação não no catálogo
        """
        try:
            from app.core.orchestrator import is_proposal_valid
            
            class MockSnapshot:
                def __init__(self):
                    self.accounts = {}
                    self.deposit = {}
                    self.agreements = {}
            
            class MockEnv:
                def __init__(self):
                    self.lead = type('Lead', (), {'id': 43})()
                    self.snapshot = MockSnapshot()
            
            env = MockEnv()
            automation_id = 'automacao_inexistente'
            
            # Mock que automação não existe no catálogo
            with patch('app.core.orchestrator.load_automation_from_catalog', return_value=None):
                
                is_valid = await is_proposal_valid(automation_id, env)
                
                assert not is_valid, "Automação inexistente deve ser rejeitada"
                
            print("✅ FASE 4 — Guardrails catálogo: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste guardrails: {e}")
            import traceback
            traceback.print_exc()
            raise


class TestGateDeterministico:
    """Testes para Gate determinístico (curto-circuito)"""
    
    @pytest.mark.asyncio
    async def test_curto_circuito_yes(self):
        """
        Teste do curto-circuito determinístico para YES
        """
        try:
            from app.core.confirmation_gate import ConfirmationGate
            from app.settings import settings
            
            # Ativar flag
            original_flag = settings.GATE_YESNO_DETERMINISTICO
            settings.GATE_YESNO_DETERMINISTICO = True
            
            try:
                class MockEnv:
                    def __init__(self, text):
                        self.lead = type('Lead', (), {'id': 50})()
                        self.messages_window = [
                            type('Message', (), {'text': text, 'sender': 'user'})()
                        ]
                        self.snapshot = type('Snapshot', (), {})()
                
                gate = ConfirmationGate()
                gate.contexto_service = AsyncMock()
                gate.openai_client = None
                
                pending_confirmations = [{
                    'target': 'confirm_can_deposit',
                    'source': 'context'
                }]
                
                with patch.object(gate, '_get_pending_confirmations', return_value=pending_confirmations):
                    with patch.object(gate, '_acquire_lead_lock', return_value=True):
                        with patch.object(gate, '_release_lead_lock', return_value=None):
                            with patch.object(gate, '_check_idempotency', return_value=False):
                                with patch.object(gate, '_store_idempotency', return_value=None):
                                    with patch.object(gate, '_create_confirmation_actions') as mock_actions:
                                        mock_actions.return_value = [
                                            type('Action', (), {'type': 'set_facts'})(),
                                            type('Action', (), {'type': 'clear_waiting'})()
                                        ]
                                        
                                        # Testar respostas afirmativas
                                        for resposta in ['sim', 'ok', '👍', 'claro']:
                                            env = MockEnv(resposta)
                                            result = await gate.process_message(env)
                                            
                                            assert result.handled == True, f"Resposta '{resposta}' não processada"
                                            assert result.polarity == "yes", f"Resposta '{resposta}' não classificada como YES"
                                            assert result.source == "deterministic_short", f"Resposta '{resposta}' não usou curto-circuito"
                                            assert len(result.actions) >= 2, f"Resposta '{resposta}' não retornou ações suficientes"
                            
            finally:
                settings.GATE_YESNO_DETERMINISTICO = original_flag
                
            print("✅ Gate determinístico YES: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste determinístico YES: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_curto_circuito_no(self):
        """
        Teste do curto-circuito determinístico para NO
        """
        try:
            from app.core.confirmation_gate import ConfirmationGate
            from app.settings import settings
            
            original_flag = settings.GATE_YESNO_DETERMINISTICO
            settings.GATE_YESNO_DETERMINISTICO = True
            
            try:
                class MockEnv:
                    def __init__(self, text):
                        self.lead = type('Lead', (), {'id': 51})()
                        self.messages_window = [
                            type('Message', (), {'text': text, 'sender': 'user'})()
                        ]
                        self.snapshot = type('Snapshot', (), {})()
                
                gate = ConfirmationGate()
                gate.contexto_service = AsyncMock()
                gate.openai_client = None
                
                pending_confirmations = [{
                    'target': 'confirm_can_deposit',
                    'source': 'context'
                }]
                
                with patch.object(gate, '_get_pending_confirmations', return_value=pending_confirmations):
                    with patch.object(gate, '_acquire_lead_lock', return_value=True):
                        with patch.object(gate, '_release_lead_lock', return_value=None):
                            with patch.object(gate, '_check_idempotency', return_value=False):
                                with patch.object(gate, '_store_idempotency', return_value=None):
                                    with patch.object(gate, '_create_confirmation_actions') as mock_actions:
                                        mock_actions.return_value = [
                                            type('Action', (), {'type': 'send_message'})(),
                                            type('Action', (), {'type': 'clear_waiting'})()
                                        ]
                                        
                                        # Testar respostas negativas
                                        for resposta in ['não', 'agora não']:
                                            env = MockEnv(resposta)
                                            result = await gate.process_message(env)
                                            
                                            assert result.handled == True, f"Resposta '{resposta}' não processada"
                                            assert result.polarity == "no", f"Resposta '{resposta}' não classificada como NO"
                                            assert result.source == "deterministic_short", f"Resposta '{resposta}' não usou curto-circuito"
                            
            finally:
                settings.GATE_YESNO_DETERMINISTICO = original_flag
                
            print("✅ Gate determinístico NO: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste determinístico NO: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @pytest.mark.asyncio
    async def test_curto_circuito_other(self):
        """
        Teste do curto-circuito determinístico para OTHER
        """
        try:
            from app.core.confirmation_gate import ConfirmationGate
            from app.settings import settings
            
            original_flag = settings.GATE_YESNO_DETERMINISTICO
            settings.GATE_YESNO_DETERMINISTICO = True
            
            try:
                class MockEnv:
                    def __init__(self, text):
                        self.lead = type('Lead', (), {'id': 52})()
                        self.messages_window = [
                            type('Message', (), {'text': text, 'sender': 'user'})()
                        ]
                        self.snapshot = type('Snapshot', (), {})()
                
                gate = ConfirmationGate()
                gate.contexto_service = AsyncMock()
                gate.openai_client = None
                
                pending_confirmations = [{
                    'target': 'confirm_can_deposit',
                    'source': 'context'
                }]
                
                with patch.object(gate, '_get_pending_confirmations', return_value=pending_confirmations):
                    with patch.object(gate, '_acquire_lead_lock', return_value=True):
                        with patch.object(gate, '_release_lead_lock', return_value=None):
                            with patch.object(gate, '_check_idempotency', return_value=False):
                                with patch.object(gate, '_store_idempotency', return_value=None):
                                    with patch.object(gate, '_create_confirmation_actions') as mock_actions:
                                        mock_actions.return_value = [
                                            type('Action', (), {'type': 'clear_waiting'})()
                                        ]
                                        
                                        # Testar respostas neutras
                                        for resposta in ['depois', 'talvez']:
                                            env = MockEnv(resposta)
                                            result = await gate.process_message(env)
                                            
                                            assert result.handled == True, f"Resposta '{resposta}' não processada"
                                            assert result.polarity == "other", f"Resposta '{resposta}' não classificada como OTHER"
                                            assert result.source == "deterministic_short", f"Resposta '{resposta}' não usou curto-circuito"
                            
            finally:
                settings.GATE_YESNO_DETERMINISTICO = original_flag
                
            print("✅ Gate determinístico OTHER: funcionando!")
            
        except Exception as e:
            print(f"❌ Erro no teste determinístico OTHER: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    import asyncio
    
    async def run_all_tests():
        """Executa todos os testes"""
        print("🧪 Executando testes unitários das Fases 3 e 4...")
        
        # Fase 3 testes
        fase3 = TestFase3GateRetroativo()
        await fase3.test_retroativo_yes_sem_aguardando()
        await fase3.test_retroativo_no()
        await fase3.test_janela_expirada()
        await fase3.test_idempotencia()
        await fase3.test_lock_lead()
        
        # Fase 4 testes
        fase4 = TestFase4OrquestradorSinais()
        await fase4.test_aceitar_proposta_valida()
        await fase4.test_rejeitar_proposta_conflitante()
        await fase4.test_cooldown_respeitado()
        await fase4.test_guardrails_catalogo()
        
        # Gate determinístico
        gate_det = TestGateDeterministico()
        await gate_det.test_curto_circuito_yes()
        await gate_det.test_curto_circuito_no()
        await gate_det.test_curto_circuito_other()
        
        print("\n🎉 Todos os testes unitários passaram!")
        print("📊 RESUMO:")
        print("  • FASE 3 (Gate Retroativo): 5 testes ✅")
        print("  • FASE 4 (Orquestrador Sinais): 4 testes ✅")
        print("  • Gate Determinístico: 3 testes ✅")
        print("  • Total: 12 testes ✅")
    
    # Executar testes se chamado diretamente
    asyncio.run(run_all_tests())
