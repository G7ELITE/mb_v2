"""
Testes para as melhorias implementadas.

Valida as funcionalidades de contexto persistente, resposta curta,
RAG, comparador semântico e outras melhorias.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from app.core.resposta_curta import RespostaCurtaService
from app.core.rag_service import RagService
from app.core.comparador_semantico import ComparadorSemantico
from app.core.contexto_lead import ContextoLeadService
from app.core.config_melhorias import normalizar_action_type
from app.tools.apply_plan import normalizar_action_para_envio
from app.data.schemas import ContextoLead, Snapshot, Message


class TestRespostaCurta:
    """Testes para o serviço de resposta curta."""
    
    def test_detectar_afirmacao_por_regex(self):
        """Testa detecção de afirmação por regex."""
        service = RespostaCurtaService()
        
        casos_afirmacao = ["sim", "s", "ok", "claro", "consigo", "bora", "vamos"]
        for caso in casos_afirmacao:
            resultado = service._detectar_por_regex(caso)
            assert resultado == "afirmacao", f"Falhou para: {caso}"
    
    def test_detectar_negacao_por_regex(self):
        """Testa detecção de negação por regex."""
        service = RespostaCurtaService()
        
        casos_negacao = ["não", "nao", "n", "agora não", "ainda não"]
        for caso in casos_negacao:
            resultado = service._detectar_por_regex(caso)
            assert resultado == "negacao", f"Falhou para: {caso}"
    
    def test_mensagem_curta_ambigua(self):
        """Testa detecção de mensagem curta e ambígua."""
        service = RespostaCurtaService()
        
        assert service._eh_mensagem_curta_ambigua("talvez")
        assert service._eh_mensagem_curta_ambigua("sei lá")
        assert not service._eh_mensagem_curta_ambigua("Esta é uma mensagem muito longa que não deveria ser considerada curta")


class TestRagService:
    """Testes para o serviço de RAG."""
    
    def test_extrair_topico(self):
        """Testa extração de tópico da query."""
        service = RagService()
        
        assert service._extrair_topico("como fazer depósito?") == "depósito"
        assert service._extrair_topico("quero criar conta") == "conta"
        assert service._extrair_topico("posso testar?") == "teste"
    
    def test_cache_valido(self):
        """Testa validação do cache."""
        service = RagService()
        
        # Cache inexistente
        assert not service._cache_valido("topico_inexistente")


class TestComparadorSemantico:
    """Testes para o comparador semântico."""
    
    def test_normalizar_texto(self):
        """Testa normalização de texto."""
        comparador = ComparadorSemantico()
        
        texto = "Olá! Como você está? 😊"
        normalizado = comparador._normalizar_texto(texto)
        
        assert "olá" in normalizado
        assert "?" not in normalizado
        assert "😊" not in normalizado
    
    def test_calcular_similaridade(self):
        """Testa cálculo de similaridade."""
        comparador = ComparadorSemantico()
        
        # Textos idênticos
        score = comparador._calcular_similaridade("hello world", "hello world")
        assert score == 1.0
        
        # Textos completamente diferentes
        score = comparador._calcular_similaridade("hello", "goodbye")
        assert score < 0.5


class TestConfigMelhorias:
    """Testes para configurações das melhorias."""
    
    def test_normalizar_action_type(self):
        """Testa normalização de action_type."""
        assert normalizar_action_type("message") == "send_message"
        assert normalizar_action_type("send_message") == "send_message"
        assert normalizar_action_type("msg") == "send_message"
        assert normalizar_action_type("unknown") == "unknown"


class TestNormalizacaoAction:
    """Testes para normalização de actions."""
    
    def test_normalizar_action_basica(self):
        """Testa normalização básica de action."""
        action = {
            "type": "send_message",
            "text": "Olá!"
        }
        
        resultado = normalizar_action_para_envio(action)
        
        assert resultado["text"] == "Olá!"
        assert resultado["buttons"] == []
        assert resultado["media"] == []
    
    def test_normalizar_action_com_botoes_validos(self):
        """Testa normalização com botões válidos."""
        action = {
            "type": "send_message",
            "text": "Escolha uma opção:",
            "buttons": [
                {"label": "Sim", "kind": "callback", "id": "btn_yes"},
                {"label": "Não", "kind": "callback", "id": "btn_no"}
            ]
        }
        
        resultado = normalizar_action_para_envio(action)
        
        assert len(resultado["buttons"]) == 2
        assert resultado["buttons"][0]["label"] == "Sim"
        assert resultado["buttons"][1]["label"] == "Não"
    
    def test_normalizar_action_com_botoes_invalidos(self):
        """Testa normalização removendo botões inválidos."""
        action = {
            "type": "send_message",
            "text": "Teste",
            "buttons": [
                {"label": "Válido", "kind": "callback"},
                {"kind": "callback"},  # Sem label
                None,  # Nulo
                {"label": "URL sem URL", "kind": "url"},  # URL sem url
                "string"  # Não é dict
            ]
        }
        
        resultado = normalizar_action_para_envio(action)
        
        # Apenas 1 botão válido deve restar
        assert len(resultado["buttons"]) == 1
        assert resultado["buttons"][0]["label"] == "Válido"


class TestFluxoCompleto:
    """Testes de fluxo completo (integração)."""
    
    @pytest.mark.asyncio
    async def test_fluxo_confirmacao_sim(self):
        """Testa fluxo completo de confirmação 'sim'."""
        # Mock do contexto com aguardando confirmação
        contexto_lead = ContextoLead(
            lead_id=1,
            aguardando={
                "tipo": "confirmacao",
                "fato": "can_deposit",
                "origem": "Você consegue fazer um depósito?",
                "ttl": 9999999999  # TTL no futuro
            }
        )
        
        # Mock do snapshot
        snapshot = Snapshot()
        messages = [Message(id="1", text="sim")]
        
        # Testar resposta curta
        service = RespostaCurtaService()
        posicao = await service.interpretar_resposta("sim", contexto_lead, snapshot, messages)
        
        assert posicao == "afirmacao"
    
    def test_criterios_aceitacao_basicos(self):
        """Testa critérios de aceitação básicos."""
        # Critério: Nenhum erro 'NoneType has no len()' ao enviar mensagens sem botões/mídia
        action = {"type": "send_message", "text": "Teste"}
        resultado = normalizar_action_para_envio(action)
        
        # Deve funcionar sem erro
        assert resultado["text"] == "Teste"
        assert isinstance(resultado["buttons"], list)
        assert isinstance(resultado["media"], list)
        
        # Critério: action_type padronizado
        assert normalizar_action_type("message") == "send_message"


if __name__ == "__main__":
    pytest.main([__file__])
