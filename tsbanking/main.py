from datetime import datetime, time
from fastapi import FastAPI, HTTPException, Query
from tsbanking.models import (
    Transacao, Transferencia, TipoTransferencia,
    TipoInvestimento, InvestimentoAplicacao, InvestimentoResgate,
    TipoCaixa, SaqueCaixa
)
from tsbanking.services import (
    depositar, sacar, consultar_saldo, consultar_extrato, limpar, transferir,
    aplicar_investimento, resgatar_investimento, saque_caixa
)

app = FastAPI()


@app.get("/saldo")
def saldo():
    return {"saldo": consultar_saldo()}


@app.post("/depositar")
def depositar_valor(transacao: Transacao):
    return depositar(transacao.valor)


@app.post("/sacar")
def sacar_valor(transacao: Transacao):
    # Permitir informar a conta no corpo, padrão principal
    conta = getattr(transacao, "conta", "principal") if hasattr(transacao, "conta") else "principal"
    return sacar(transacao.valor, conta)


@app.get("/extrato")
def extrato(conta: str = Query("principal")):
    return {"extrato": consultar_extrato(conta)}


@app.post("/limpar")
def limpar_historico():
    return limpar()


@app.post("/transferir")
def transferir_endpoint(transfer: Transferencia):
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

    # Executa a transferência usando o serviço correto (registra no extrato)
    from tsbanking import services
    conta_origem = getattr(transfer, "conta_origem", "principal") if hasattr(transfer, "conta_origem") else "principal"
    return services.transferir(
        transfer.valor,
        transfer.conta_destino,
        conta_origem
    )


@app.post("/investir")
def investir(aplicacao: InvestimentoAplicacao):
    return aplicar_investimento(aplicacao.valor, aplicacao.tipo_investimento)


@app.post("/resgatar_investimento")
def resgatar(resgate: InvestimentoResgate):
    return resgatar_investimento(resgate.tipo_investimento)


@app.post("/saque_caixa")
def saque_em_caixa(saida: SaqueCaixa):
    return saque_caixa(saida.valor, saida.tipo_caixa)
