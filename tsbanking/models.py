from enum import Enum
from pydantic import BaseModel


class Transacao(BaseModel):
    valor: float
    conta: str = "principal"


class TipoTransferencia(str, Enum):
    PIX = "PIX"
    DOC = "DOC"
    TED = "TED"
    INTERNA = "INTERNA"


class Transferencia(BaseModel):
    valor: float
    conta_destino: str
    tipo_transferencia: TipoTransferencia
    conta_origem: str = "principal"


class TipoInvestimento(str, Enum):
    CDB = "CDB"
    POUPANCA = "POUPANCA"
    TESOURO_DIRETO = "TESOURO_DIRETO"


class InvestimentoAplicacao(BaseModel):
    valor: float
    tipo_investimento: TipoInvestimento


class InvestimentoResgate(BaseModel):
    tipo_investimento: TipoInvestimento


class TipoCaixa(str, Enum):
    CAIXA_10 = "CAIXA_10"
    CAIXA_20 = "CAIXA_20"
    CAIXA_50 = "CAIXA_50"
    CAIXA_100 = "CAIXA_100"


class SaqueCaixa(BaseModel):
    valor: float
    tipo_caixa: TipoCaixa
