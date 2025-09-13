from pydantic import BaseModel, Field, field_validator
from typing import List, Any
from uuid import UUID


class CertificateNotificationItem(BaseModel):
    """
    Modelo para um item de certificado na notificação da Tech Floripa.
    Garante que UUIDs sejam convertidos para string automaticamente.
    """
    id: str = Field(..., description="ID do certificado (convertido de UUID para string)")
    order_id: int = Field(..., description="ID do pedido")
    product_id: int = Field(..., description="ID do produto")
    product_name: str = Field(..., description="Nome do produto")
    certificate_url: str | None = Field(None, description="URL do certificado")
    success: bool = Field(default=False, description="Status de sucesso da geração")

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v: Any) -> str:
        """
        Converte UUID para string automaticamente.
        Aceita tanto UUID quanto string como entrada.
        """
        if isinstance(v, UUID):
            return str(v)
        return str(v)


class TechFloripaNotification(BaseModel):
    """
    Modelo para o corpo da notificação enviada para a API da Tech Floripa.
    Estrutura completa do payload que será serializado em JSON.
    """
    product_id: int = Field(..., description="ID do produto principal")
    certificates_quantity: int = Field(..., description="Quantidade de certificados processados")
    certificates: List[CertificateNotificationItem] = Field(..., description="Lista de certificados")

    @classmethod
    def from_certificates(cls, certificates: List[Any]) -> 'TechFloripaNotification':
        """
        Método de factory para criar uma instância a partir de uma lista de certificados.
        
        Args:
            certificates: Lista de objetos Certificate da entidade
            
        Returns:
            TechFloripaNotification: Instância configurada para envio
        """
        if not certificates:
            raise ValueError("Lista de certificados não pode estar vazia")
        
        # Converte cada certificado para o formato de notificação
        certificate_items = [
            CertificateNotificationItem(
                id=cert.id,  # Será convertido automaticamente pelo validator
                order_id=cert.order_id,
                product_id=cert.product_id,
                product_name=cert.product_name,
                certificate_url=cert.certificate_url,
                success=cert.success
            )
            for cert in certificates
        ]
        
        return cls(
            product_id=certificates[0].product_id,
            certificates_quantity=len(certificates),  # Corrigido para usar certificates_quantity
            certificates=certificate_items
        )
