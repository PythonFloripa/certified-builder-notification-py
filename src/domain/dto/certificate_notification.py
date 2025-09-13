from pydantic import BaseModel, Field
from typing import List

class CertificateNotificationResponse(BaseModel):
    """
    Modelo de resposta da fila de notificação de certificados.
    Representa o resultado do processamento de um certificado.
    [{"order_id": 452, "product_id": 316, "product_name": "Evento de Teste", "email": "jardelgodinho@gmail.com", "certificate_key": "certificates/316/452/Jardel_GodinhoEvento_de_Teste_AD9-B58-BFA.png", "success": true}, {"order_id": 317, "product_id": 316, "product_name": "Evento de Teste", "email": "jardel.godinho@gmail.com", "certificate_key": "certificates/316/317/Jardel_GodinhoEvento_de_Teste_443-C8D-B05.png", "success": true}]
    """
    order_id: int = Field(..., description="ID da ordem processada")
    product_id: int = Field(..., description="ID do produto")
    product_name: str = Field(..., description="Nome do produto")
    email: str = Field(..., description="Email do participante")
    certificate_key: str = Field(..., description="Chave/caminho do certificado no S3")
    success: bool = Field(..., description="Status do processamento do certificado")

class CertificateNotificationBatch(BaseModel):
    """
    Lote de notificações de certificados recebidas da fila.
    """
    notifications: List[CertificateNotificationResponse] = Field(
        default_factory=list,
        description="Lista de notificações de certificados"
    )