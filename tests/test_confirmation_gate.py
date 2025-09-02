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


async def apply_actions_for_test(actions, lead_id: int):
    """
    Executor de ações para testes E2E.
    
    Args:
        actions: Lista de Action objects
        lead_id: ID do lead
        
    Returns:
        Dict com resultados da aplicação
    """
    results = {
        "set_facts": False,
        "clear_waiting": False,
        "send_message": False,
        "errors": []
    }
    
    try:
        contexto_service = get_contexto_lead_service()
        
        for action in actions:
            if action.type == "set_facts":
                # Persistir fatos no storage
                if hasattr(action, 'set_facts') and action.set_facts:
                    profile_updates = {}
                    for key, value in action.set_facts.items():
                        if "." in key:
                            parts = key.split(".")
                            current = profile_updates
                            for part in parts[:-1]:
                                if part not in current:
                                    current[part] = {}
                                current = current[part]
                            current[parts[-1]] = value
                        else:
                            profile_updates[key] = value
                    
                    # Atualizar perfil do lead
                    from app.data.repo import LeadRepository
                    from app.data.database import SessionLocal
                    db = SessionLocal()
                    try:
                        repo = LeadRepository(db)
                        repo.update_profile_facts(lead_id, profile_updates)
                        results["set_facts"] = True
                    finally:
                        db.close()
            
            elif action.type == "clear_waiting":
                # Limpar estado aguardando
                await contexto_service.limpar_aguardando(lead_id)
                results["clear_waiting"] = True
            
            elif action.type == "send_message":
                # Mock para testes - apenas logar
                results["send_message"] = True
                print(f"📤 [TEST] Mensagem enviada: {getattr(action, 'text', 'N/A')}")
        
        # Log estruturado para observabilidade
        print(f"{{'event':'test_apply_actions', 'set_facts':{results['set_facts']}, 'clear_waiting':{results['clear_waiting']}}}")
        
    except Exception as e:
        results["errors"].append(str(e))
        print(f"❌ Erro ao aplicar ações: {e}")
    
    return results


@pytest.mark.asyncio
async def test_fase_1_e2e_hook_gate_actions():
    """
    Teste E2E da FASE 1: Hook + Gate + Aplicação de ações
    """
    try:
        print("🧪 Testando FASE 1 — Hook + Gate + Aplicação de ações...")
        
        # 1. Simular hook sendo chamado
        from app.core.automation_hook import get_automation_hook
        from app.core.contexto_lead import get_contexto_lead_service
        
        hook = get_automation_hook()
        contexto_service = get_contexto_lead_service()
        
        await hook.on_automation_sent(
            automation_id='ask_deposit_for_test',
            lead_id=8,
            success=True,
            provider_message_id='msg_123',
            prompt_text='Para liberar o teste, você consegue fazer um pequeno depósito?'
        )
        
        print("✅ Hook executado - aguardando criado")
        
        # 2. Verificar contexto
        contexto = await contexto_service.obter_contexto(8)
        assert contexto.aguardando is not None, "Aguardando não foi criado"
        assert contexto.ultima_automacao_enviada == 'ask_deposit_for_test', "Última automação não foi salva"
        print(f"✅ Contexto: aguardando={contexto.aguardando is not None}, última_automacao={contexto.ultima_automacao_enviada}")
        
        # 3. Simular mensagem do usuário "sim"
        class MockEnv:
            def __init__(self):
                self.lead = type('Lead', (), {'id': 8})()
                self.messages_window = [
                    type('Message', (), {'text': 'sim', 'sender': 'user'})()
                ]
                self.snapshot = type('Snapshot', (), {})()
        
        env = MockEnv()
        gate = get_confirmation_gate()
        result = await gate.process_message(env)
        
        # 4. Validar resultado do Gate
        assert result.handled == True, "Gate não processou a confirmação"
        assert len(result.actions) >= 2, "Gate não retornou ações suficientes"
        print(f"✅ Gate: handled={result.handled}, polarity={result.polarity}, actions={len(result.actions)}")
        
        # 5. Aplicar ações retornadas pelo Gate
        apply_results = await apply_actions_for_test(result.actions, 8)
        
        # 6. Re-ler contexto para validar
        contexto_final = await contexto_service.obter_contexto(8)
        
        # 7. Asserts finais
        assert apply_results["clear_waiting"] == True, "clear_waiting não foi aplicado"
        assert apply_results["set_facts"] == True, "set_facts não foi aplicado"
        assert contexto_final.aguardando is None, "Aguardando não foi limpo"
        
        # Verificar se fatos foram persistidos (via LeadProfile)
        from app.data.repo import LeadRepository
        from app.data.database import SessionLocal
        db = SessionLocal()
        try:
            repo = LeadRepository(db)
            profile = repo.get_lead_profile(8)
            if profile and hasattr(profile, 'agreements'):
                agreements = profile.agreements or {}
                assert agreements.get('can_deposit') == True, "Fato agreements.can_deposit não foi persistido"
        finally:
            db.close()
        
        print("✅ FASE 1 E2E: Todas as ações aplicadas e validadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste E2E: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_gate_deterministico_curto():
    """
    Teste do Gate determinístico para respostas curtas
    """
    try:
        print("🧪 Testando Gate determinístico — respostas curtas...")
        
        # Ativar flag de determinismo
        from app.settings import settings
        original_flag = settings.GATE_YESNO_DETERMINISTICO
        settings.GATE_YESNO_DETERMINISTICO = True
        
        try:
            # 1. Criar aguardando para confirmação
            from app.core.automation_hook import get_automation_hook
            from app.core.contexto_lead import get_contexto_lead_service
            
            hook = get_automation_hook()
            contexto_service = get_contexto_lead_service()
            
            await hook.on_automation_sent(
                automation_id='ask_deposit_for_test',
                lead_id=9,  # Usar lead diferente
                success=True,
                provider_message_id='msg_456',
                prompt_text='Para liberar o teste, você consegue fazer um pequeno depósito?'
            )
            
            # 2. Testar respostas curtas afirmativas
            afirmativas = ["sim", "ok", "👍", "claro"]
            for resposta in afirmativas:
                class MockEnv:
                    def __init__(self, text):
                        self.lead = type('Lead', (), {'id': 9})()
                        self.messages_window = [
                            type('Message', (), {'text': text, 'sender': 'user'})()
                        ]
                        self.snapshot = type('Snapshot', (), {})()
                
                env = MockEnv(resposta)
                gate = get_confirmation_gate()
                result = await gate.process_message(env)
                
                assert result.handled == True, f"Resposta '{resposta}' não foi processada"
                assert result.polarity == "yes", f"Resposta '{resposta}' não foi classificada como YES"
                assert result.source == "deterministic_short", f"Resposta '{resposta}' não usou curto-circuito"
                
                # Verificar ações para YES
                assert len(result.actions) >= 2, f"Resposta '{resposta}' não retornou ações suficientes"
                has_clear_waiting = any(action.type == "clear_waiting" for action in result.actions)
                has_set_facts = any(action.type == "set_facts" for action in result.actions)
                assert has_clear_waiting, f"Resposta '{resposta}' não incluiu clear_waiting"
                assert has_set_facts, f"Resposta '{resposta}' não incluiu set_facts"
                print(f"✅ '{resposta}' → YES (curto-circuito) - clear_waiting: {has_clear_waiting}, set_facts: {has_set_facts}")
            
            # 3. Testar respostas curtas negativas
            negativas = ["não", "agora não"]
            for resposta in negativas:
                env = MockEnv(resposta)
                gate = get_confirmation_gate()
                result = await gate.process_message(env)
                
                assert result.handled == True, f"Resposta '{resposta}' não foi processada"
                assert result.polarity == "no", f"Resposta '{resposta}' não foi classificada como NO"
                assert result.source == "deterministic_short", f"Resposta '{resposta}' não usou curto-circuito"
                
                # Verificar ações para NO (não deve ter set_facts irreversível)
                assert len(result.actions) >= 1, f"Resposta '{resposta}' não retornou ações"
                has_clear_waiting = any(action.type == "clear_waiting" for action in result.actions)
                has_set_facts = any(action.type == "set_facts" for action in result.actions)
                assert has_clear_waiting, f"Resposta '{resposta}' não incluiu clear_waiting"
                # NO pode ter set_facts, mas não deve ser irreversível
                print(f"✅ '{resposta}' → NO (curto-circuito) - clear_waiting: {has_clear_waiting}, set_facts: {has_set_facts}")
            
            # 4. Testar respostas neutras/adiamento
            neutras = ["depois", "talvez"]
            for resposta in neutras:
                env = MockEnv(resposta)
                gate = get_confirmation_gate()
                result = await gate.process_message(env)
                
                assert result.handled == True, f"Resposta '{resposta}' não foi processada"
                assert result.polarity == "other", f"Resposta '{resposta}' não foi classificada como OTHER"
                assert result.source == "deterministic_short", f"Resposta '{resposta}' não usou curto-circuito"
                
                # Verificar ações para OTHER (não deve ter set_facts irreversível)
                assert len(result.actions) >= 1, f"Resposta '{resposta}' não retornou ações"
                has_clear_waiting = any(action.type == "clear_waiting" for action in result.actions)
                has_set_facts = any(action.type == "set_facts" for action in result.actions)
                assert has_clear_waiting, f"Resposta '{resposta}' não incluiu clear_waiting"
                # OTHER não deve ter set_facts irreversível
                print(f"✅ '{resposta}' → OTHER (curto-circuito) - clear_waiting: {has_clear_waiting}, set_facts: {has_set_facts}")
            
            # 5. Testar resposta longa (deve cair no fluxo normal)
            env = MockEnv("Consigo fazer o depósito sim, mas preciso de ajuda")
            gate = get_confirmation_gate()
            result = await gate.process_message(env)
            
            # Resposta longa pode ou não ser processada, mas não deve usar curto-circuito
            if result.handled:
                assert result.source != "deterministic_short", "Resposta longa usou curto-circuito incorretamente"
                print(f"✅ Resposta longa → {result.polarity} (fluxo normal)")
            else:
                print("✅ Resposta longa → não processada (esperado)")
            
            print("✅ Gate determinístico: Todas as respostas curtas processadas corretamente!")
            
        finally:
            # Restaurar flag original
            settings.GATE_YESNO_DETERMINISTICO = original_flag
            print("✅ Flag GATE_YESNO_DETERMINISTICO restaurada")
        
    except Exception as e:
        print(f"❌ Erro no teste determinístico: {e}")
        import traceback
        traceback.print_exc()
        raise
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


@pytest.mark.asyncio
async def test_fase_2_intake_sempre_llm():
    """
    Teste E2E da FASE 2: Intake sempre-LLM com schema válido
    """
    try:
        print("🧪 Testando FASE 2 — Intake sempre-LLM com schema válido...")
        
        # 1. Construir MockEnv com janela de mensagens coerente
        class MockEnv:
            def __init__(self):
                self.lead = type('Lead', (), {'id': 10, 'platform': 'telegram'})()
                self.messages_window = [
                    type('Message', (), {'text': 'Quero testar o robô', 'sender': 'user'})(),
                    type('Message', (), {'text': 'Para liberar o teste, você consegue fazer um pequeno depósito?', 'sender': 'bot'})()
                ]
                self.snapshot = type('Snapshot', (), {
                    'accounts': {'quotex': 'desconhecido', 'nyrion': 'desconhecido'},
                    'deposit': {'status': 'nenhum', 'amount': None, 'confirmed': False},
                    'agreements': {'can_deposit': False, 'wants_test': True}
                })()
                self.candidates = {}
        
        env = MockEnv()
        
        # 2. Executar intake sempre-LLM
        from app.core.intake_agent import run_intake_always_llm
        
        enriched_env = await run_intake_always_llm(env)
        
        # 3. Coletar signals
        assert hasattr(enriched_env.snapshot, 'llm_signals'), "Signals não foram adicionados ao snapshot"
        signals = enriched_env.snapshot.llm_signals
        
        # 4. Validar signals
        assert isinstance(signals.get('intents'), list), "intents deve ser uma lista"
        assert signals.get('polarity') in ['yes', 'no', 'other', 'sarcastic'], f"polarity inválida: {signals.get('polarity')}"
        assert isinstance(signals.get('targets'), dict), "targets deve ser um dict"
        assert isinstance(signals.get('facts'), list), "facts deve ser uma lista"
        assert isinstance(signals.get('propose_automations'), list), "propose_automations deve ser uma lista"
        assert isinstance(signals.get('needs_clarifying'), bool), "needs_clarifying deve ser um boolean"
        
        # 5. Verificar se pelo menos um campo tem dados úteis
        has_useful_data = (
            len(signals.get('intents', [])) > 0 or
            len(signals.get('targets', {})) > 0 or
            len(signals.get('facts', [])) > 0 or
            len(signals.get('propose_automations', [])) > 0
        )
        
        assert has_useful_data, "Signals não contêm dados úteis"
        
        # 6. VALIDAÇÕES ADICIONAIS - Endurecer o teste
        # Verificar ausência de erro
        assert signals.get("error") in (None, ""), f"Erro encontrado nos signals: {signals.get('error')}"
        
        # Validar proposta contra catálogo
        propose_automations = signals.get('propose_automations', [])
        if propose_automations:
            # IDs válidos do catálogo (exemplos)
            valid_automation_ids = [
                'ask_deposit_for_test', 
                'ask_deposit_permission_v3', 
                'prompt_deposit',
                'signup_link_v3',
                'deposit_help_quick_v3'
            ]
            
            for proposed_id in propose_automations:
                assert proposed_id in valid_automation_ids, f"Automação proposta '{proposed_id}' não está no catálogo válido"
                print(f"✅ Proposta válida: {proposed_id}")
        
        # Verificar self-consistency
        used_samples = signals.get('used_samples', 1)
        assert used_samples == 2, f"Self-consistency não foi aplicada: used_samples={used_samples}"
        
        # Verificar agreement score (se implementado)
        agreement_score = signals.get('agreement_score')
        if agreement_score is not None:
            assert 0.0 <= agreement_score <= 1.0, f"Agreement score inválido: {agreement_score}"
            print(f"✅ Agreement score: {agreement_score}")
        
        # 7. VALIDAÇÕES DE CONTEÚDO MÍNIMO
        # Verificar intents não vazio
        intents = signals.get('intents', [])
        assert len(intents) > 0, "Intents não pode estar vazio"
        
        # Verificar polarity válida
        polarity = signals.get('polarity')
        assert polarity in ['yes', 'no', 'other', 'sarcastic'], f"Polarity inválida: {polarity}"
        
        # Verificar pelo menos um entre targets, facts ou propose_automations
        targets = signals.get('targets', {})
        facts = signals.get('facts', [])
        propose_automations = signals.get('propose_automations', [])
        
        has_content = len(targets) > 0 or len(facts) > 0 or len(propose_automations) > 0
        assert has_content, "Deve ter pelo menos um entre targets, facts ou propose_automations"
        
        # 8. RESUMO FINAL
        print("📊 RESUMO FASE 2 - Intake Blindado:")
        print(f"  • Intents: {len(intents)} ({', '.join(intents[:3])}{'...' if len(intents) > 3 else ''})")
        print(f"  • Polarity: {polarity}")
        print(f"  • Has targets: {len(targets) > 0}")
        print(f"  • Facts count: {len(facts)}")
        print(f"  • Propose count: {len(propose_automations)}")
        print(f"  • Used samples: {used_samples}")
        print(f"  • Agreement score: {agreement_score}")
        print(f"  • Error: {signals.get('error')}")
        print("✅ FASE 2 E2E: Intake sempre-LLM funcionando com schema válido e validações blindadas!")
        
    except Exception as e:
        print(f"❌ Erro no teste Intake: {e}")
        import traceback
        traceback.print_exc()
        raise


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


# Testes E2E adicionais
@pytest.mark.asyncio
async def test_gate_deterministico_yes_com_acoes():
    """
    Teste E2E: Gate determinístico — YES com ações
    """
    try:
        print("🧪 Testando Gate determinístico — YES com ações...")
        
        # Ativar flag de determinismo
        from app.settings import settings
        original_flag = settings.GATE_YESNO_DETERMINISTICO
        settings.GATE_YESNO_DETERMINISTICO = True
        
        try:
            class MockEnv:
                def __init__(self, text):
                    self.lead = type('Lead', (), {'id': 11})()
                    self.messages_window = [
                        type('Message', (), {'text': text, 'sender': 'user'})()
                    ]
                    self.snapshot = type('Snapshot', (), {})()
            
            gate = get_confirmation_gate()
            
            # Mock do método _get_pending_confirmations para target de depósito
            async def mock_get_pending(contexto_lead, env):
                return [{
                    'target': 'confirm_can_deposit',
                    'source': 'context',
                    'timestamp': int(asyncio.get_event_loop().time()),
                    'automation_id': 'ask_deposit_for_test'
                }]
            
            gate._get_pending_confirmations = mock_get_pending
            
            # Testar 'sim'
            env = MockEnv('sim')
            result = await gate.process_message(env)
            
            # Asserts
            assert result.handled == True, "Resposta 'sim' não foi processada"
            assert result.source == "deterministic_short", "Resposta 'sim' não usou curto-circuito"
            assert result.polarity == "yes", "Resposta 'sim' não foi classificada como YES"
            
            # Verificar ações
            assert len(result.actions) >= 2, "Não retornou ações suficientes"
            has_clear_waiting = any(action.type == "clear_waiting" for action in result.actions)
            has_set_facts = any(action.type == "set_facts" for action in result.actions)
            assert has_clear_waiting, "Não incluiu clear_waiting"
            assert has_set_facts, "Não incluiu set_facts"
            
            print("✅ Gate determinístico YES: Ações corretas aplicadas!")
            
        finally:
            settings.GATE_YESNO_DETERMINISTICO = original_flag
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_gate_deterministico_no():
    """
    Teste E2E: Gate determinístico — NO
    """
    try:
        print("🧪 Testando Gate determinístico — NO...")
        
        from app.settings import settings
        original_flag = settings.GATE_YESNO_DETERMINISTICO
        settings.GATE_YESNO_DETERMINISTICO = True
        
        try:
            class MockEnv:
                def __init__(self, text):
                    self.lead = type('Lead', (), {'id': 12})()
                    self.messages_window = [
                        type('Message', (), {'text': text, 'sender': 'user'})()
                    ]
                    self.snapshot = type('Snapshot', (), {})()
            
            gate = get_confirmation_gate()
            
            async def mock_get_pending(contexto_lead, env):
                return [{
                    'target': 'confirm_can_deposit',
                    'source': 'context',
                    'timestamp': int(asyncio.get_event_loop().time()),
                    'automation_id': 'ask_deposit_for_test'
                }]
            
            gate._get_pending_confirmations = mock_get_pending
            
            # Testar 'não'
            env = MockEnv('não')
            result = await gate.process_message(env)
            
            # Asserts
            assert result.handled == True, "Resposta 'não' não foi processada"
            assert result.source == "deterministic_short", "Resposta 'não' não usou curto-circuito"
            assert result.polarity == "no", "Resposta 'não' não foi classificada como NO"
            
            # Verificar ações
            assert len(result.actions) >= 1, "Não retornou ações"
            has_clear_waiting = any(action.type == "clear_waiting" for action in result.actions)
            assert has_clear_waiting, "Não incluiu clear_waiting"
            
            print("✅ Gate determinístico NO: Ações corretas aplicadas!")
            
        finally:
            settings.GATE_YESNO_DETERMINISTICO = original_flag
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_gate_deterministico_other():
    """
    Teste E2E: Gate determinístico — OTHER
    """
    try:
        print("🧪 Testando Gate determinístico — OTHER...")
        
        from app.settings import settings
        original_flag = settings.GATE_YESNO_DETERMINISTICO
        settings.GATE_YESNO_DETERMINISTICO = True
        
        try:
            class MockEnv:
                def __init__(self, text):
                    self.lead = type('Lead', (), {'id': 13})()
                    self.messages_window = [
                        type('Message', (), {'text': text, 'sender': 'user'})()
                    ]
                    self.snapshot = type('Snapshot', (), {})()
            
            gate = get_confirmation_gate()
            
            async def mock_get_pending(contexto_lead, env):
                return [{
                    'target': 'confirm_can_deposit',
                    'source': 'context',
                    'timestamp': int(asyncio.get_event_loop().time()),
                    'automation_id': 'ask_deposit_for_test'
                }]
            
            gate._get_pending_confirmations = mock_get_pending
            
            # Testar 'depois' e 'talvez'
            for resposta in ['depois', 'talvez']:
                env = MockEnv(resposta)
                result = await gate.process_message(env)
                
                # Asserts
                assert result.handled == True, f"Resposta '{resposta}' não foi processada"
                assert result.source == "deterministic_short", f"Resposta '{resposta}' não usou curto-circuito"
                assert result.polarity == "other", f"Resposta '{resposta}' não foi classificada como OTHER"
                
                # Verificar ações
                assert len(result.actions) >= 1, f"Resposta '{resposta}' não retornou ações"
                has_clear_waiting = any(action.type == "clear_waiting" for action in result.actions)
                assert has_clear_waiting, f"Resposta '{resposta}' não incluiu clear_waiting"
                
                print(f"✅ '{resposta}' → OTHER (curto-circuito)")
            
            print("✅ Gate determinístico OTHER: Todas as respostas neutras processadas!")
            
        finally:
            settings.GATE_YESNO_DETERMINISTICO = original_flag
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        raise


@pytest.mark.asyncio
async def test_fase_2_intake_blindado():
    """
    Teste E2E: Fase 2 — intake blindado
    """
    try:
        print("🧪 Testando Fase 2 — intake blindado...")
        
        # Executar o teste da FASE 2 com os novos asserts
        await test_fase_2_intake_sempre_llm()
        
        print("✅ Fase 2 blindada: Todas as validações passaram!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        raise


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