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
