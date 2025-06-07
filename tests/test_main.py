from fastapi import HTTPException
import pytest
from datetime import datetime as real_datetime, datetime, timedelta
from fastapi.testclient import TestClient
from tsbanking.main import app
from tsbanking.database import atualizar_saldo, limpar_extrato, get_saldo, get_extrato
from tsbanking.services import transferir


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


# --- Testes de investimentos ---


def test_investir_cdb_valido(client):
    # Deposita saldo suficiente
    client.post("/depositar", json={"valor": 1000})
    response = client.post(
        "/investir", json={"valor": 500, "tipo_investimento": "CDB"})
    assert response.status_code == 200
    assert "Aplicado" in response.json().get("mensagem", "")


def test_investir_saldo_insuficiente(client):
    response = client.post(
        "/investir", json={"valor": 999999, "tipo_investimento": "CDB"})
    assert response.status_code == 400
    assert "Saldo insuficiente" in response.json().get("detail", "")


def test_resgatar_cdb(client):
    # Deposita e investe
    client.post("/depositar", json={"valor": 1000})
    from datetime import datetime, timedelta
    data_aplic = datetime(2024, 1, 1, 10, 0)
    data_resg = data_aplic + timedelta(days=1)
    client.post("/investir", json={"valor": 500, "tipo_investimento": "CDB"})
    from tsbanking.database import get_investimento
    get_investimento("CDB")["data_aplicacao"] = data_aplic.isoformat()
    response = client.post("/resgatar_investimento",
                           json={"tipo_investimento": "CDB"})
    assert response.status_code == 200
    assert "Resgatado" in response.json().get("mensagem", "")
    assert response.json()["juros"] > 0


def test_cdb_rendimento_30_dias(client):
    client.post("/depositar", json={"valor": 1000})
    data_aplic = datetime(2024, 1, 1, 10, 0)
    data_resg = data_aplic + timedelta(days=30)
    # Aplica investimento com data específica
    response = client.post(
        "/investir", json={"valor": 500, "tipo_investimento": "CDB"})
    assert response.status_code == 200
    # Força a data de aplicação
    from tsbanking.database import get_investimento
    get_investimento("CDB")["data_aplicacao"] = data_aplic.isoformat()
    # Resgata após 30 dias
    from tsbanking.services import resgatar_investimento
    result = resgatar_investimento("CDB", data_resgate=data_resg.isoformat())
    assert result["dias"] == 30
    assert result["juros"] > 0


def test_poupanca_rendimento_10_dias(client):
    client.post("/depositar", json={"valor": 1000})
    data_aplic = datetime(2024, 1, 1, 10, 0)
    data_resg = data_aplic + timedelta(days=10)
    response = client.post(
        "/investir", json={"valor": 200, "tipo_investimento": "POUPANCA"})
    assert response.status_code == 200
    from tsbanking.database import get_investimento
    get_investimento("POUPANCA")["data_aplicacao"] = data_aplic.isoformat()
    from tsbanking.services import resgatar_investimento
    result = resgatar_investimento(
        "POUPANCA", data_resgate=data_resg.isoformat())
    assert result["dias"] == 10
    assert result["juros"] > 0


def test_tesouro_rendimento_60_dias(client):
    client.post("/depositar", json={"valor": 1000})
    data_aplic = datetime(2024, 1, 1, 10, 0)
    data_resg = data_aplic + timedelta(days=60)
    response = client.post(
        "/investir", json={"valor": 300, "tipo_investimento": "TESOURO_DIRETO"})
    assert response.status_code == 200
    from tsbanking.database import get_investimento
    get_investimento("TESOURO_DIRETO")[
        "data_aplicacao"] = data_aplic.isoformat()
    from tsbanking.services import resgatar_investimento
    result = resgatar_investimento(
        "TESOURO_DIRETO", data_resgate=data_resg.isoformat())
    assert result["dias"] == 60
    assert result["juros"] > 0


def test_resgate_data_invalida(client):
    client.post("/depositar", json={"valor": 1000})
    data_aplic = datetime(2024, 1, 10, 10, 0)
    data_resg = datetime(2024, 1, 1, 10, 0)  # anterior à aplicação
    response = client.post(
        "/investir", json={"valor": 100, "tipo_investimento": "CDB"})
    assert response.status_code == 200
    from tsbanking.database import get_investimento
    get_investimento("CDB")["data_aplicacao"] = data_aplic.isoformat()
    from tsbanking.services import resgatar_investimento, HTTPException
    try:
        resgatar_investimento("CDB", data_resgate=data_resg.isoformat())
        assert False, "Deveria lançar exceção de data inválida"
    except HTTPException as e:
        assert "anterior à aplicação" in str(e.detail)


# --- Testes de saque em espécie em caixas eletrônicos ---


def test_saque_caixa_10_valido(client):
    client.post("/depositar", json={"valor": 100})
    response = client.post(
        "/saque_caixa", json={"valor": 40, "tipo_caixa": "CAIXA_10"})
    assert response.status_code == 200
    assert "Saque de R$ 40.00 realizado no caixa 10" in response.json().get("mensagem", "")


def test_saque_caixa_10_invalido(client):
    client.post("/depositar", json={"valor": 100})
    response = client.post(
        "/saque_caixa", json={"valor": 25, "tipo_caixa": "CAIXA_10"})
    assert response.status_code == 400
    assert "múltiplo de 10" in response.json().get("detail", "")


def test_saque_caixa_50_valido(client):
    client.post("/depositar", json={"valor": 200})
    response = client.post(
        "/saque_caixa", json={"valor": 150, "tipo_caixa": "CAIXA_50"})
    assert response.status_code == 200
    assert "Saque de R$ 150.00 realizado no caixa 50" in response.json().get("mensagem", "")


def test_saque_caixa_50_invalido(client):
    client.post("/depositar", json={"valor": 200})
    response = client.post(
        "/saque_caixa", json={"valor": 120, "tipo_caixa": "CAIXA_50"})
    assert response.status_code == 400
    assert "múltiplo de 50" in response.json().get("detail", "")


# --- Testes adicionais de cobertura e comportamentos não permitidos ---
def test_saque_caixa_tipo_invalido(client):
    client.post("/depositar", json={"valor": 100})
    response = client.post(
        "/saque_caixa", json={"valor": 50, "tipo_caixa": "CAIXA_X"})
    assert response.status_code == 422
    assert (
        "Input should be" in response.text or
        "Unprocessable Entity" in response.text or
        "is not a valid enumeration member" in response.text
    )


def test_transferencia_tipo_invalido(client):
    response = client.post("/transferir", json={
        "valor": 10,
        "conta_destino": "destino",
        "tipo_transferencia": "INVALIDA"
    })
    assert response.status_code == 422
    assert (
        "Input should be" in response.text or
        "Unprocessable Entity" in response.text or
        "is not a valid enumeration member" in response.text
    )


def test_investir_tipo_invalido(client):
    client.post("/depositar", json={"valor": 100})
    response = client.post(
        "/investir", json={"valor": 50, "tipo_investimento": "BITCOIN"})
    assert response.status_code == 422 or "tipo_investimento" in response.text


def test_resgatar_sem_aplicacao(client):
    response = client.post("/resgatar_investimento",
                           json={"tipo_investimento": "POUPANCA"})
    assert response.status_code == 400
    assert "Nenhum valor aplicado" in response.json().get("detail", "")


def test_deposito_zero(client):
    response = client.post("/depositar", json={"valor": 0})
    assert response.status_code == 400
    assert "Valor deve ser positivo" in response.text


def test_saque_zero(client):
    response = client.post("/sacar", json={"valor": 0})
    assert response.status_code == 400
    assert "Valor deve ser positivo" in response.text


def test_transferencia_valor_zero(client):
    response = client.post("/transferir", json={
        "valor": 0,
        "conta_destino": "destino",
        "tipo_transferencia": "PIX"
    })
    assert response.status_code == 400
    assert "Valor deve ser positivo" in response.text


def test_limpar_extrato_sem_movimentacao(client):
    response = client.post("/limpar")
    assert response.status_code == 200
    assert response.json().get("mensagem") == "Extrato limpo"


def test_extrato_apos_limpar(client):
    client.post("/depositar", json={"valor": 100})
    client.post("/limpar")
    response = client.get("/extrato")
    assert response.status_code == 200
    assert response.json().get("extrato") == []


def test_saque_caixa_saldo_insuficiente(client):
    # Limpa extrato e zera saldo
    client.post("/limpar")
    from tsbanking.database import atualizar_saldo
    atualizar_saldo(0, "principal")
    response = client.post(
        "/saque_caixa", json={"valor": 1000, "tipo_caixa": "CAIXA_100"})
    assert response.status_code == 400
    assert "Saldo insuficiente" in response.json().get("detail", "")

# Testes de transferência entre contas


@pytest.fixture(autouse=True)
def reset_database():
    """Reseta o banco de dados antes de cada teste"""
    atualizar_saldo(1000.0, "principal")
    atualizar_saldo(500.0, "destino")
    limpar_extrato("principal")
    limpar_extrato("destino")


def test_transferencia_bem_sucedida():
    # Testa transferência válida
    resultado = transferir(300.0, "destino", "principal")

    assert resultado["mensagem"] == "Transferido R$ 300.00 para destino"
    assert get_saldo("principal") == 700.0  # 1000 - 300
    assert get_saldo("destino") == 800.0    # 500 + 300

    # Verifica os registros no extrato
    extrato_origem = get_extrato("principal")
    extrato_destino = get_extrato("destino")

    assert extrato_origem[0]["op"] == "transferencia para destino"
    assert extrato_origem[0]["valor"] == 300.0
    assert extrato_destino[0]["op"] == "transferencia de principal"
    assert extrato_destino[0]["valor"] == 300.0


def test_transferencia_conta_origem_invalida():
    # Testa conta de origem inválida
    with pytest.raises(HTTPException) as excinfo:
        transferir(100.0, "destino", "conta_inexistente")

    assert excinfo.value.status_code == 404
    assert "não encontrada" in excinfo.value.detail


def test_transferencia_conta_destino_invalida():
    # Testa conta de destino inválida
    with pytest.raises(HTTPException) as excinfo:
        transferir(100.0, "conta_inexistente", "principal")

    assert excinfo.value.status_code == 404
    assert "não encontrada" in excinfo.value.detail


def test_transferencia_valor_negativo():
    # Testa valor negativo
    with pytest.raises(HTTPException) as excinfo:
        transferir(-100.0, "destino", "principal")

    assert excinfo.value.status_code == 400
    assert "positivo" in excinfo.value.detail


def test_transferencia_saldo_insuficiente():
    # Testa saldo insuficiente
    with pytest.raises(HTTPException) as excinfo:
        transferir(1500.0, "destino", "principal")

    assert excinfo.value.status_code == 400
    assert "insuficiente" in excinfo.value.detail
    assert get_saldo("principal") == 1000.0  # Saldo não deve mudar
    assert get_saldo("destino") == 500.0     # Saldo não deve mudar


def test_transferencia_entre_mesmas_contas():
    # Testa transferência para a mesma conta
    with pytest.raises(HTTPException) as excinfo:
        transferir(100.0, "principal", "principal")

    assert excinfo.value.status_code == 400
    assert "mesma conta" in excinfo.value.detail


def test_transferencia_valor_zero():
    # Testa valor zero
    with pytest.raises(HTTPException) as excinfo:
        transferir(0.0, "destino", "principal")

    assert excinfo.value.status_code == 400
    assert "positivo" in excinfo.value.detail
