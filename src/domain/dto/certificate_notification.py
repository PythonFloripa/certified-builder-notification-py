from pydantic import BaseModel, Field
from typing import List

class CertificateNotificationResponse(BaseModel):
    """
    Modelo de resposta da fila de notificação de certificados.
    Representa o resultado do processamento de um certificado.
    """
    order_id: int = Field(..., description="ID da ordem processada")    
    validation_code: str = Field(..., description="Código de validação do certificado")
    authenticity_verification_url: str = Field(..., description="URL para verificação de autenticidade do certificado")
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