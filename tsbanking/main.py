from datetime import datetime, time
from fastapi import FastAPI, HTTPException
from tsbanking.models import Transacao, Transferencia, TipoTransferencia
from tsbanking.services import depositar, sacar, consultar_saldo, consultar_extrato, limpar, transferir

app = FastAPI()


@app.get("/saldo")
def saldo():
    return {"saldo": consultar_saldo()}


@app.post("/depositar")
def depositar_valor(transacao: Transacao):
    return depositar(transacao.valor)


@app.post("/sacar")
def sacar_valor(transacao: Transacao):
    return sacar(transacao.valor)


@app.get("/extrato")
def extrato():
    return {"extrato": consultar_extrato()}


@app.post("/limpar")
def limpar_historico():
    return limpar()


@app.post("/transferir")
def transferir(transfer: Transferencia):
    agora = datetime.now()
    hora_atual = agora.time()

    if transfer.tipo_transferencia == TipoTransferencia.PIX:
        # Restrição de valor para horário noturno (20h às 6h)
        if hora_atual >= time(20, 0) or hora_atual <= time(6, 0):
            if transfer.valor > 1000:
                raise HTTPException(
                    status_code=400,
                    detail="Transferência PIX noturna acima do limite de R$1000"
                )

    elif transfer.tipo_transferencia == TipoTransferencia.DOC:
        if transfer.valor > 10000:
            raise HTTPException(
                status_code=400,
                detail="Valor excede limite do DOC (R$10.000)"
            )

    elif transfer.tipo_transferencia == TipoTransferencia.TED:
        # TED permitido apenas entre 6h e 17h
        if not (time(6, 0) <= hora_atual <= time(17, 0)):
            raise HTTPException(
                status_code=400,
                detail="TED só permitido entre 06:00 e 17:00"
            )
        if transfer.valor > 50000:
            raise HTTPException(
                status_code=400,
                detail="Valor excede limite do TED (R$50.000)"
            )

    elif transfer.tipo_transferencia == TipoTransferencia.INTERNA:
        if transfer.valor > 100000:
            raise HTTPException(
                status_code=400,
                detail="Valor excede limite da transferência interna (R$100.000)"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Tipo de transferência inválido"
        )

    # Validação de saldo (opcional: ajustar conforme sua lógica real)
    if transfer.valor > consultar_saldo():
        raise HTTPException(
            status_code=400,
            detail="Saldo insuficiente"
        )

    # Executa a transferência (ex: debita da conta atual e credita em outra)
    sacar(transfer.valor)  # Exemplo: debita valor da conta do usuário

    return {
        "status": "Transferência realizada",
        "tipo": transfer.tipo_transferencia,
        "valor": transfer.valor,
        "destino": transfer.conta_destino
    }
