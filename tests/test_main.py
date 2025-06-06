import pytest
from datetime import datetime as real_datetime
from fastapi.testclient import TestClient
from tsbanking.main import app


@pytest.fixture
def client():
    return TestClient(app)


# Classe base para mock de datetime
class MockDateTime(real_datetime):
    @classmethod
    def now(cls):
        return cls(2024, 1, 1, 10, 0)  # padrão: 10h


# --- Testes básicos de saldo, depósito, saque, extrato, limpar ---


def test_saldo_inicial(client):
    response = client.get("/saldo")
    assert response.status_code == 200
    assert "saldo" in response.json()


def test_deposito_valido(client):
    response = client.post("/depositar", json={"valor": 100.0})
    assert response.status_code == 200
    assert "novo_saldo" in response.json()


def test_deposito_invalido(client):
    response = client.post("/depositar", json={"valor": -50})
    assert response.status_code == 400
    assert "Valor deve ser positivo" in response.text


def test_saque_valido(client):
    response = client.post("/sacar", json={"valor": 50.0})
    assert response.status_code == 200
    assert "novo_saldo" in response.json()


def test_saque_invalido(client):
    response = client.post("/sacar", json={"valor": 999999})
    assert response.status_code == 400  # espera erro
    assert "erro" in response.json() or "detail" in response.json()


def test_extrato(client):
    response = client.get("/extrato")
    assert response.status_code == 200
    assert isinstance(response.json().get("extrato", []), list)


def test_limpar_extrato(client):
    response = client.post("/limpar")
    assert response.status_code == 200
    assert response.json().get("mensagem") == "Extrato limpo"


# --- Testes de transferências gerais ---


def test_transferencia_valida(client):
    response = client.post("/transferir", json={
        "valor": 10,
        "conta_destino": "destino",
        "tipo_transferencia": "PIX"
    })
    assert response.status_code == 200


def test_transferencia_invalida_valor_alto(client):
    response = client.post("/transferir", json={
        "valor": 999999,
        "conta_destino": "destino",
        "tipo_transferencia": "PIX"
    })
    assert response.status_code == 400


# --- Testes PIX com monkeypatch ---


def test_pix_valido_dia(client, monkeypatch):
    class MockDia(real_datetime):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 14, 0)

    monkeypatch.setattr("tsbanking.main.datetime", MockDia)

    response = client.post("/transferir", json={
        "valor": 500,
        "conta_destino": "123",
        "tipo_transferencia": "PIX"
    })
    assert response.status_code == 200


def test_pix_noturno_acima_limite(client, monkeypatch):
    class MockNoite(real_datetime):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 22, 0)

    monkeypatch.setattr("tsbanking.main.datetime", MockNoite)

    response = client.post("/transferir", json={
        "valor": 1500,
        "conta_destino": "123",
        "tipo_transferencia": "PIX"
    })
    assert response.status_code == 400
    assert "noturna acima do limite" in response.json().get("detail", "")


# --- Testes DOC ---


def test_doc_valido(client, monkeypatch):
    # Mocka get_saldo para retornar 100000
    monkeypatch.setattr("tsbanking.services.get_saldo",
                        lambda conta="principal": 100000)

    response = client.post("/transferir", json={
        "valor": 9000,
        "conta_destino": "123",
        "tipo_transferencia": "DOC"
    })
    print(response.status_code, response.json())
    assert response.status_code == 200


def test_doc_excede_limite(client):
    response = client.post("/transferir", json={
        "valor": 15000,
        "conta_destino": "123",
        "tipo_transferencia": "DOC"
    })
    assert response.status_code == 400
    assert "excede limite do DOC" in response.json().get("detail", "")


# --- Testes TED com monkeypatch ---


def test_ted_valido(client, monkeypatch):
    class MockHorarioValido(real_datetime):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 10, 0)

    monkeypatch.setattr("tsbanking.main.datetime", MockHorarioValido)
    monkeypatch.setattr("tsbanking.services.get_saldo",
                        lambda conta="principal": 100000)

    response = client.post("/transferir", json={
        "valor": 20000,
        "conta_destino": "123",
        "tipo_transferencia": "TED"
    })
    assert response.status_code == 200


def test_ted_fora_do_horario(client, monkeypatch):
    class MockForaHorario(real_datetime):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 18, 0)

    monkeypatch.setattr("tsbanking.main.datetime", MockForaHorario)

    response = client.post("/transferir", json={
        "valor": 1000,
        "conta_destino": "123",
        "tipo_transferencia": "TED"
    })
    assert response.status_code == 400
    assert "só permitido entre" in response.json().get("detail", "")


def test_ted_excede_limite(client, monkeypatch):
    class MockHorarioValido(real_datetime):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 11, 0)

    monkeypatch.setattr("tsbanking.main.datetime", MockHorarioValido)

    response = client.post("/transferir", json={
        "valor": 60000,
        "conta_destino": "123",
        "tipo_transferencia": "TED"
    })
    assert response.status_code == 400
    assert "excede limite do TED" in response.json().get("detail", "")


# --- Testes transferências internas ---


def test_transferencia_interna_valida(client, monkeypatch):
    monkeypatch.setattr("tsbanking.services.get_saldo",
                        lambda conta="principal": 200000)

    response = client.post("/transferir", json={
        "valor": 90000,
        "conta_destino": "123",
        "tipo_transferencia": "INTERNA"
    })
    assert response.status_code == 200


def test_transferencia_interna_excede_limite(client):
    response = client.post("/transferir", json={
        "valor": 150000,
        "conta_destino": "123",
        "tipo_transferencia": "INTERNA"
    })
    assert response.status_code == 400
    assert "excede limite da transferência interna" in response.json().get("detail", "")


# --- Teste saldo insuficiente para transferência ---


def test_transferencia_saldo_insuficiente(client, monkeypatch):

    class MockDia(real_datetime):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 10, 0)  # horário normal para PIX

    monkeypatch.setattr("tsbanking.main.datetime", MockDia)
    monkeypatch.setattr("tsbanking.services.get_saldo",
                        lambda conta="principal": 9998)

    response = client.post("/transferir", json={
        "valor": 9999,
        "conta_destino": "123",
        "tipo_transferencia": "PIX"
    })
    assert response.status_code == 400
    assert "Saldo insuficiente" in response.json().get("detail", "")
