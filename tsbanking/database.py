_db = {
    "contas": {
        "principal": {
            "saldo": 1000.0,
            "extrato": []
        },
        "destino": {
            "saldo": 500.0,
            "extrato": []
        }
    },
    "investimentos": {
        "CDB": {"valor": 0.0, "taxa": 0.015, "data_aplicacao": None},
        "POUPANCA": {"valor": 0.0, "taxa": 0.005, "data_aplicacao": None},
        "TESOURO_DIRETO": {"valor": 0.0, "taxa": 0.01, "data_aplicacao": None}
    }
}


def get_conta(nome="principal"):
    return _db["contas"][nome]


def get_saldo(nome="principal"):
    return get_conta(nome)["saldo"]


def atualizar_saldo(novo_saldo, nome="principal"):
    get_conta(nome)["saldo"] = novo_saldo


def registrar_operacao(operacao: str, valor: float, nome="principal"):
    get_conta(nome)["extrato"].append({"op": operacao, "valor": valor})


def get_extrato(nome="principal"):
    return get_conta(nome)["extrato"]


def limpar_extrato(nome="principal"):
    get_conta(nome)["extrato"] = []


def get_investimento(tipo):
    return _db["investimentos"][tipo]


def atualizar_investimento(tipo, valor):
    _db["investimentos"][tipo]["valor"] = valor


def get_taxa_investimento(tipo):
    return _db["investimentos"][tipo]["taxa"]
