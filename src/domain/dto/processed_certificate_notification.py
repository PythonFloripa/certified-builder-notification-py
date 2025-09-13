from pydantic import BaseModel
from typing import List
from src.domain.entity.certificate import Certificate


class ProcessedCertificateNotification(BaseModel):
    """
    Modelo de resposta do processamento de notificação de certificado.
    """
    updated_certificates: List[Certificate]
    total_notifications: int