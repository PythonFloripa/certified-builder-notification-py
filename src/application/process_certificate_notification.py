import logging
from typing import List
from datetime import datetime
from src.domain.dto.certificate_notification import CertificateNotificationResponse, CertificateNotificationBatch
from src.domain.repository.certificate_repository import CertificateRepository
from src.domain.entity.certificate import Certificate
from src.domain.dto.processed_certificate_notification import ProcessedCertificateNotification
from src.infrastructure.aws.file_manager import FileManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ProcessCertificateNotification:
    """
    Processa notificações de certificados gerados e atualiza o banco de dados.
    """
    
    def __init__(self, certificate_repository: CertificateRepository, file_manager: FileManager):
        """
        Inicializa o processador de notificações de certificado.
        
        Args:
            certificate_repository: Repositório para operações com certificados
            file_manager: Gerenciador de arquivos para URLs de certificados
        """
        self.certificate_repository = certificate_repository
        self.file_manager = file_manager

    def execute(self, notifications: CertificateNotificationBatch) -> ProcessedCertificateNotification:
        logger.info(f"Iniciando processamento de {len(notifications.notifications)} notificações de certificados")
        
        updated_certificates: List[Certificate] = []
        
        for notification in notifications.notifications:
            try:
                existing_certificate = self.certificate_repository.get_by_order_id(notification.order_id)
                
                if existing_certificate and len(existing_certificate) > 0:
                    existing_certificate = existing_certificate[0]
                    updated_certificate = self._update_certificate_with_notification(
                        existing_certificate, 
                        notification
                    )
                    
                    # Salva as alterações no banco
                    # Converte UUID para string para compatibilidade com BaseRepository
                    self.certificate_repository.update(
                        str(updated_certificate.id),
                        updated_certificate
                    )
                    
                    updated_certificate.authenticity_verification_url = notification.authenticity_verification_url
                    updated_certificate.validation_code = notification.validation_code
                    
                    updated_certificates.append(updated_certificate)
                    
                    logger.info(f"Certificado atualizado com sucesso - Order ID: {notification.order_id}")
                else:
                    logger.warning(f"Certificado não encontrado para Order ID: {notification.order_id}")
                    
            except Exception as e:
                logger.error(f"Erro ao processar notificação para Order ID {notification.order_id}: {str(e)}")
                
        
        result = ProcessedCertificateNotification(
                updated_certificates=updated_certificates,
                total_notifications=len(notifications.notifications)
            )
        
        logger.info(f"Processamento concluído: {len(updated_certificates)} sucessos")
        return result

    def _update_certificate_with_notification(
        self, 
        certificate: Certificate, 
        notification: CertificateNotificationResponse
    ) -> Certificate:
        """
        Atualiza um certificado existente com dados da notificação.
        
        Args:
            certificate: Certificado existente no banco
            notification: Dados da notificação recebida
            
        Returns:
            Certificate: Certificado atualizado
        """
        # Atualiza os campos relacionados ao resultado do processamento
        certificate.success = notification.success
        certificate.certificate_key = notification.certificate_key
        certificate.generated_date = datetime.now().isoformat()
        
        # Se o processamento foi bem-sucedido, verifica se o certificado existe no S3
        if notification.success and notification.certificate_key:
            certificate.certificate_url = self._check_and_generate_certificate_url(
                notification.certificate_key, 
                certificate.id
            )
        
        return certificate

    def _check_and_generate_certificate_url(self, certificate_key: str, certificate_id: str) -> str:
        """
        Verifica se o certificado existe no S3 e gera URL de download via API Gateway.
        
        Args:
            certificate_key: Chave do arquivo no S3
            certificate_id: ID do certificado (UUID)
            
        Returns:
            str: URL de download via API Gateway se o arquivo existir, string vazia caso contrário
        """
        # Verifica se a chave existe no bucket S3
        key_exists = self.file_manager.check_key_exists(certificate_key)
        
        if key_exists:
            # Se existe, gera URL usando API Gateway + ID do certificado
            download_url = self.file_manager.generate_download_url(str(certificate_id))
            logger.info(f"Certificado encontrado no S3. URL de download gerada: {download_url}")
            return download_url
        else:
            # Se não existe, retorna string vazia
            logger.warning(f"Certificado não encontrado no S3 para a chave: {certificate_key}")
            return ""    