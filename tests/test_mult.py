import pytest
from fastapi.testclient import TestClient
from tsbanking.main import app
from tsbanking.database import limpar_extrato, atualizar_saldo

@pytest.fixture
def client():
    return TestClient(app)

# Limpa extratos antes de cada teste para isolamento
@pytest.fixture(autouse=True)
def clean_extratos():
    limpar_extrato("principal")
    limpar_extrato("destino")
    atualizar_saldo(0, "principal")
    atualizar_saldo(0, "destino")
    yield
    limpar_extrato("principal")
    limpar_extrato("destino")
    atualizar_saldo(0, "principal")
    atualizar_saldo(0, "destino")

def depositar(client, conta, valor):
    return client.post("/depositar", json={"valor": valor, "conta": conta})

def saldo(client, conta):
    return client.get(f"/saldo?conta={conta}")

def extrato(client, conta):
    return client.get(f"/extrato?conta={conta}")

def transferir(client, valor, conta_destino, tipo="PIX", conta_origem="principal"):
    return client.post("/transferir", json={
        "valor": valor,
        "conta_destino": conta_destino,
        "tipo_transferencia": tipo,
        "conta_origem": conta_origem
    })

# 1. Depositar em conta1, transferir para conta2, checar saldos e extratos
def test_deposito_transferencia_saldos_extratos(client):
    depositar(client, "principal", 1000)
    r1 = saldo(client, "principal")
    assert r1.status_code == 200 and r1.json()["saldo"] >= 1000
    transferir(client, 300, "destino")
    r2 = saldo(client, "principal")
    r3 = saldo(client, "destino")
    assert r2.json()["saldo"] == r1.json()["saldo"] - 300
    assert r3.json()["saldo"] >= 300
    e1 = extrato(client, "principal")
    e2 = extrato(client, "destino")
    assert any("transferencia" in x.get("op", "") for x in e1.json()["extrato"])
    assert any("transferencia" in x.get("op", "") for x in e2.json()["extrato"])

# 2. Transferência PIX noturna acima do limite
def test_pix_noturno_limite(client, monkeypatch):
    from datetime import datetime as dt
    class MockNoite(dt):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 22, 0)
    monkeypatch.setattr("tsbanking.main.datetime", MockNoite)
    depositar(client, "principal", 2000)
    resp = client.post("/transferir", json={"valor": 1500, "conta_destino": "destino", "tipo_transferencia": "PIX"})
    assert resp.status_code == 400
    resp2 = client.post("/transferir", json={"valor": 900, "conta_destino": "destino", "tipo_transferencia": "PIX"})
    assert resp2.status_code == 200
    ext = extrato(client, "principal").json()["extrato"]
    assert any("transferencia" in x["op"] for x in ext)

# 3. Transferência DOC acima do limite
def test_doc_limite(client):
    depositar(client, "principal", 20000)
    resp = client.post("/transferir", json={"valor": 15000, "conta_destino": "destino", "tipo_transferencia": "DOC"})
    assert resp.status_code == 400
    resp2 = client.post("/transferir", json={"valor": 9000, "conta_destino": "destino", "tipo_transferencia": "DOC"})
    assert resp2.status_code == 200
    ext = extrato(client, "principal").json()["extrato"]
    assert any("transferencia" in x["op"] for x in ext)

# 4. Transferência TED fora do horário
def test_ted_horario_limite(client, monkeypatch):
    from datetime import datetime as dt
    class MockForaHorario(dt):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 18, 0)
    monkeypatch.setattr("tsbanking.main.datetime", MockForaHorario)
    depositar(client, "principal", 60000)
    resp = client.post("/transferir", json={"valor": 1000, "conta_destino": "destino", "tipo_transferencia": "TED"})
    assert resp.status_code == 400
    class MockHorario(dt):
        @classmethod
        def now(cls):
            return cls(2024, 1, 1, 10, 0)
    monkeypatch.setattr("tsbanking.main.datetime", MockHorario)
    resp2 = client.post("/transferir", json={"valor": 20000, "conta_destino": "destino", "tipo_transferencia": "TED"})
    assert resp2.status_code == 200
    resp3 = client.post("/transferir", json={"valor": 60000, "conta_destino": "destino", "tipo_transferencia": "TED"})
    assert resp3.status_code == 400
    ext = extrato(client, "principal").json()["extrato"]
    assert any("transferencia" in x["op"] for x in ext)

# 5. Investimento CDB e resgate
def test_investimento_cdb_resgate(client):
    depositar(client, "principal", 2000)
    client.post("/investir", json={"valor": 1000, "tipo_investimento": "CDB"})
    saldo_antes = saldo(client, "principal").json()["saldo"]
    resp = client.post("/resgatar_investimento", json={"tipo_investimento": "CDB"})
    assert resp.status_code == 200
    saldo_depois = saldo(client, "principal").json()["saldo"]
    assert saldo_depois > saldo_antes
    ext = extrato(client, "principal").json()["extrato"]
    assert any("aplicacao_CDB" in x["op"] for x in ext)
    assert any("resgate_CDB" in x["op"] for x in ext)

# 6. Investimento poupança e resgate
def test_investimento_poupanca_resgate(client):
    depositar(client, "principal", 1500)
    client.post("/investir", json={"valor": 500, "tipo_investimento": "POUPANCA"})
    saldo_antes = saldo(client, "principal").json()["saldo"]
    resp = client.post("/resgatar_investimento", json={"tipo_investimento": "POUPANCA"})
    assert resp.status_code == 200
    saldo_depois = saldo(client, "principal").json()["saldo"]
    assert saldo_depois > saldo_antes
    ext = extrato(client, "principal").json()["extrato"]
    assert any("aplicacao_POUPANCA" in x["op"] for x in ext)
    assert any("resgate_POUPANCA" in x["op"] for x in ext)

# 7. Investimento tesouro e resgate
def test_investimento_tesouro_resgate(client):
    depositar(client, "principal", 3000)
    client.post("/investir", json={"valor": 2000, "tipo_investimento": "TESOURO_DIRETO"})
    saldo_antes = saldo(client, "principal").json()["saldo"]
    resp = client.post("/resgatar_investimento", json={"tipo_investimento": "TESOURO_DIRETO"})
    assert resp.status_code == 200
    saldo_depois = saldo(client, "principal").json()["saldo"]
    assert saldo_depois > saldo_antes
    ext = extrato(client, "principal").json()["extrato"]
    assert any("aplicacao_TESOURO_DIRETO" in x["op"] for x in ext)
    assert any("resgate_TESOURO_DIRETO" in x["op"] for x in ext)

# 8. Saque em espécie múltiplo permitido
def test_saque_caixa_multiplos(client):
    depositar(client, "principal", 100)
    resp = client.post("/saque_caixa", json={"valor": 50, "tipo_caixa": "CAIXA_50"})
    assert resp.status_code == 200
    resp2 = client.post("/saque_caixa", json={"valor": 55, "tipo_caixa": "CAIXA_50"})
    assert resp2.status_code == 400
    ext = extrato(client, "principal").json()["extrato"]
    assert any("saque_caixa_50" in x["op"] for x in ext)

# 9. Limpeza de extrato
def test_limpeza_extrato(client):
    depositar(client, "principal", 100)
    client.post("/sacar", json={"valor": 50})
    resp = client.post("/limpar")
    assert resp.status_code == 200
    ext = extrato(client, "principal").json()["extrato"]
    assert ext == []

# 10. Transferência interna válida
def test_transferencia_interna(client):
    depositar(client, "principal", 200000)
    resp = client.post("/transferir", json={"valor": 90000, "conta_destino": "destino", "tipo_transferencia": "INTERNA"})
    assert resp.status_code == 200
    ext = extrato(client, "principal").json()["extrato"]
    assert any("transferencia" in x["op"] for x in ext)

# 11. Transferência interna acima do limite
def test_transferencia_interna_acima_limite(client):
    depositar(client, "principal", 200000)
    resp = client.post("/transferir", json={"valor": 150000, "conta_destino": "destino", "tipo_transferencia": "INTERNA"})
    assert resp.status_code == 400

# 12. Depósito valor negativo
def test_deposito_negativo(client):
    resp = client.post("/depositar", json={"valor": -100, "conta": "principal"})
    assert resp.status_code == 400
    ext = extrato(client, "principal").json()["extrato"]
    # Não deve registrar operação
    assert all("deposito" not in x["op"] for x in ext)

# 13. Saque saldo insuficiente
def test_saque_insuficiente(client):
    depositar(client, "principal", 50)
    saldo_atual = saldo(client, "principal").json()["saldo"]
    valor = saldo_atual + 10
    resp = client.post("/sacar", json={"valor": valor, "conta": "principal"})
    assert resp.status_code == 400
    ext = extrato(client, "principal").json()["extrato"]
    # Não deve registrar operação
    assert all("saque" not in x["op"] for x in ext)

# 14. Transferência saldo insuficiente
def test_transferencia_insuficiente(client):
    depositar(client, "principal", 10)
    saldo_atual = saldo(client, "principal").json()["saldo"]
    valor = saldo_atual + 10
    resp = client.post("/transferir", json={"valor": valor, "conta_destino": "destino", "tipo_transferencia": "PIX"})
    assert resp.status_code == 400
    ext = extrato(client, "principal").json()["extrato"]
    # Não deve registrar operação
    assert all("transferencia" not in x["op"] for x in ext)

# 15. Fluxo completo usuário
def test_fluxo_completo_usuario(client, monkeypatch):
    depositar(client, "principal", 5000)
    client.post("/investir", json={"valor": 2000, "tipo_investimento": "CDB"})
    client.post("/transferir", json={"valor": 1000, "conta_destino": "destino", "tipo_transferencia": "PIX"})
    client.post("/sacar", json={"valor": 500})
    saldo_final = saldo(client, "principal").json()["saldo"]
    ext = extrato(client, "principal").json()["extrato"]
    assert saldo_final <= 5000 - 2000 - 1000 - 500 + 1  # +1 por rendimento
    assert any("aplicacao_CDB" in x["op"] for x in ext)
    assert any("transferencia para destino" in x["op"] for x in ext)
    assert any("saque" in x["op"] for x in ext)

def test_fluxo_usuario_destino_recebe(client):
    depositar(client, "principal", 1000)
    client.post("/transferir", json={"valor": 400, "conta_destino": "destino", "tipo_transferencia": "PIX"})
    saldo_destino = saldo(client, "destino").json()["saldo"]
    ext_destino = extrato(client, "destino").json()["extrato"]
    assert saldo_destino >= 400
    assert any("transferencia de principal" in x["op"] for x in ext_destino)

def test_fluxo_limpeza_e_novo_movimento(client):
    depositar(client, "principal", 100)
    client.post("/sacar", json={"valor": 50})
    client.post("/limpar")
    ext = extrato(client, "principal").json()["extrato"]
    assert ext == []
    client.post("/depositar", json={"valor": 30, "conta": "principal"})
    ext2 = extrato(client, "principal").json()["extrato"]
    assert any("deposito" in x["op"] for x in ext2)
