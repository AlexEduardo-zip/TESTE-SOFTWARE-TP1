from tsbanking.database import (
    get_saldo, atualizar_saldo, registrar_operacao,
    get_extrato, limpar_extrato, get_conta
)
from fastapi import HTTPException


def validar_conta(conta):
    try:
        return get_conta(conta)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"Conta '{conta}' não encontrada")


def validar_valor(valor):
    if valor <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")


def depositar(valor, conta="principal"):
    validar_conta(conta)
    validar_valor(valor)

    saldo = get_saldo(conta)
    novo = saldo + valor
    atualizar_saldo(novo, conta)
    registrar_operacao("deposito", valor, conta)
    return {"mensagem": "Depósito realizado", "novo_saldo": novo}


def sacar(valor, conta="principal"):
    validar_conta(conta)
    validar_valor(valor)

    saldo = get_saldo(conta)
    if valor > saldo:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    novo = saldo - valor
    atualizar_saldo(novo, conta)
    registrar_operacao("saque", valor, conta)
    return {"mensagem": "Saque realizado", "novo_saldo": novo}


def consultar_saldo(conta="principal"):
    validar_conta(conta)
    return get_saldo(conta)


def consultar_extrato(conta="principal"):
    validar_conta(conta)
    return get_extrato(conta)


def limpar(conta="principal"):
    validar_conta(conta)
    limpar_extrato(conta)
    return {"mensagem": "Extrato limpo"}


def transferir(valor, conta_destino):
    validar_conta("principal")
    validar_conta(conta_destino)
    validar_valor(valor)

    origem_saldo = get_saldo("principal")
    if valor > origem_saldo:
        raise HTTPException(
            status_code=400, detail="Saldo insuficiente para transferência")

    # Debita e credita
    sacar(valor, "principal")
    depositar(valor, conta_destino)
    return {"mensagem": f"Transferido R$ {valor:.2f} para {conta_destino}"}
