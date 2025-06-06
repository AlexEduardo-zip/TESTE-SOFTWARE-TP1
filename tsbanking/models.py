from enum import Enum
from pydantic import BaseModel


class Transacao(BaseModel):
    valor: float


class TipoTransferencia(str, Enum):
    PIX = "PIX"
    DOC = "DOC"
    TED = "TED"
    INTERNA = "INTERNA"


class Transferencia(BaseModel):
    valor: float
    conta_destino: str
    tipo_transferencia: TipoTransferencia
