"""
Testes para componentes do core engine.
"""
import pytest
from app.core.snapshot_builder import extract_candidates, build_snapshot
from app.core.selector import evaluate_eligibility_rule
from app.core.procedures import is_step_satisfied
from app.data.schemas import Snapshot


class TestSnapshotBuilder:
    """Testes para o snapshot builder."""
    
    def test_extract_email_candidates(self):
        """Testa extração de emails."""
        text = "Meu email é test@example.com para contato"
        candidates = extract_candidates(text)
        assert "email" in candidates
        assert candidates["email"] == "test@example.com"
    
    def test_extract_id_candidates(self):
        """Testa extração de IDs."""
        text = "Minha conta é 123456789"
        candidates = extract_candidates(text)
        assert "nyrion_id" in candidates
        assert candidates["nyrion_id"] == "123456789"
    
    def test_extract_intent_candidates(self):
        """Testa extração de intenções."""
        text = "Quero testar o robô"
        candidates = extract_candidates(text)
        assert "intent" in candidates
        assert candidates["intent"] == "teste"
    
    @pytest.mark.asyncio
    async def test_build_snapshot(self):
        """Testa construção de snapshot."""
        inbound = {
            "platform": "telegram",
            "user_id": "123",
            "message_text": "test@example.com"
        }
        
        env = await build_snapshot(inbound)
        assert env.lead.lang == "pt-BR"
        assert "email" in env.candidates


class TestSelector:
    """Testes para o selector de automações."""
    
    def test_evaluate_deposit_rule(self):
        """Testa avaliação de regras de depósito."""
        snapshot = Snapshot(
            agreements={"can_deposit": False},
            deposit={"status": "nenhum"}
        )
        
        # Teste regra positiva
        rule = "não concordou em depositar e não depositou"
        assert evaluate_eligibility_rule(rule, snapshot) == True
        
        # Teste após concordar
        snapshot.agreements["can_deposit"] = True
        assert evaluate_eligibility_rule(rule, snapshot) == False
    
    def test_evaluate_account_rule(self):
        """Testa avaliação de regras de conta."""
        snapshot = Snapshot(
            accounts={"quotex": "desconhecido", "nyrion": "desconhecido"}
        )
        
        rule = "não tem conta"
        assert evaluate_eligibility_rule(rule, snapshot) == True
        
        # Teste após ter conta
        snapshot.accounts["quotex"] = "verificado"
        rule = "tem conta"
        assert evaluate_eligibility_rule(rule, snapshot) == True


class TestProcedures:
    """Testes para procedimentos."""
    
    def test_is_step_satisfied(self):
        """Testa verificação de satisfação de passos."""
        snapshot = Snapshot(
            agreements={"can_deposit": True},
            deposit={"status": "confirmado"}
        )
        
        # Passo satisfeito
        condition = "o lead concordou em depositar"
        assert is_step_satisfied(condition, snapshot) == True
        
        # Passo não satisfeito
        condition = "depósito confirmado"
        assert is_step_satisfied(condition, snapshot) == True
        
        # Teste com condição não satisfeita
        snapshot.deposit["status"] = "nenhum"
        assert is_step_satisfied(condition, snapshot) == False

