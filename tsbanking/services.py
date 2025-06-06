from tsbanking.database import (
    get_saldo, atualizar_saldo, registrar_operacao,
    get_extrato, limpar_extrato, get_conta,
    get_investimento, atualizar_investimento, get_taxa_investimento
)
from fastapi import HTTPException
from datetime import datetime


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


def aplicar_investimento(valor, tipo, conta="principal", data_aplicacao=None):
    validar_conta(conta)
    validar_valor(valor)
    saldo = get_saldo(conta)
    if valor > saldo:
        raise HTTPException(status_code=400, detail="Saldo insuficiente para investir")
    atualizar_saldo(saldo - valor, conta)
    investimento = get_investimento(tipo)
    novo_valor = investimento["valor"] + valor
    # Salva data da aplicação
    if data_aplicacao is None:
        data_aplicacao = datetime.now().isoformat()
    investimento["data_aplicacao"] = data_aplicacao
    atualizar_investimento(tipo, novo_valor)
    registrar_operacao(f"aplicacao_{tipo}", valor, conta)
    return {"mensagem": f"Aplicado R$ {valor:.2f} em {tipo}", "valor_aplicado": novo_valor, "data_aplicacao": data_aplicacao}


def resgatar_investimento(tipo, conta="principal", data_resgate=None):
    validar_conta(conta)
    investimento = get_investimento(tipo)
    valor = investimento["valor"]
    if valor <= 0:
        raise HTTPException(status_code=400, detail="Nenhum valor aplicado neste investimento")
    taxa = get_taxa_investimento(tipo)
    data_aplicacao = investimento.get("data_aplicacao")
    if not data_aplicacao:
        raise HTTPException(status_code=400, detail="Data de aplicação não encontrada")
    if data_resgate is None:
        data_resgate = datetime.now().isoformat()
    # Calcula tempo em dias
    dt_aplic = datetime.fromisoformat(data_aplicacao)
    dt_resg = datetime.fromisoformat(data_resgate)
    dias = (dt_resg - dt_aplic).days
    if dias < 0:
        raise HTTPException(status_code=400, detail="Data de resgate anterior à aplicação")
    # Métricas de rendimento
    if tipo == "CDB":
        rendimento = valor * ((1 + taxa) ** dias - 1)
    elif tipo == "POUPANCA":
        rendimento = valor * taxa * dias
    elif tipo == "TESOURO_DIRETO":
        rendimento = valor * ((1 + taxa) ** (dias/30) - 1)
    else:
        rendimento = valor * taxa * dias
    total = valor + rendimento
    atualizar_investimento(tipo, 0.0)
    saldo = get_saldo(conta)
    atualizar_saldo(saldo + total, conta)
    registrar_operacao(f"resgate_{tipo}", total, conta)
    return {"mensagem": f"Resgatado R$ {total:.2f} de {tipo} (juros: R$ {rendimento:.2f})", "valor_resgatado": total, "juros": rendimento, "dias": dias}


def saque_caixa(valor, tipo_caixa, conta="principal"):
    validar_conta(conta)
    validar_valor(valor)
    saldo = get_saldo(conta)
    # Corrige: saldo deve ser verificado ANTES de calcular múltiplo
    if valor > saldo:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    if tipo_caixa == "CAIXA_10":
        multiplo = 10
    elif tipo_caixa == "CAIXA_20":
        multiplo = 20
    elif tipo_caixa == "CAIXA_50":
        multiplo = 50
    elif tipo_caixa == "CAIXA_100":
        multiplo = 100
    else:
        raise HTTPException(status_code=400, detail="Tipo de caixa inválido")
    if valor % multiplo != 0:
        raise HTTPException(status_code=400, detail=f"Valor deve ser múltiplo de {multiplo} para este caixa")
    novo = saldo - valor
    atualizar_saldo(novo, conta)
    registrar_operacao(f"saque_caixa_{multiplo}", valor, conta)
    return {"mensagem": f"Saque de R$ {valor:.2f} realizado no caixa {multiplo}", "novo_saldo": novo}
