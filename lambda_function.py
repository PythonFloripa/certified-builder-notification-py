import logging
from datetime import datetime
import json
from src.infrastructure.container.dependency_container import container
from src.domain.dto.certificate_notification import CertificateNotificationBatch, CertificateNotificationResponse
from src.application.process_certificate_notification import ProcessCertificateNotification
from src.domain.dto.processed_certificate_notification import ProcessedCertificateNotification
from src.application.certificate_notification_tech_floripa import CertificateNotificationTechFloripa
from src.domain.dto.tech_floripa_notification import TechFloripaNotification


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_notifications_from_event(event) -> CertificateNotificationBatch:
    """
    Extrai e valida as notificações de certificado do evento SQS.
    
    Args:
        event: Evento SQS contendo as notificações
        
    Returns:
        CertificateNotificationBatch: Batch de notificações validado
    """
    body = event.get('Records')[0].get('body')
    if isinstance(body, str):
        body = json.loads(body)
    
    # Se o body é uma lista, encapsula na estrutura esperada pelo modelo
    if isinstance(body, list):
        notifications_data = {"notifications": body}
    else:
        # Se já é um objeto, usa diretamente
        notifications_data = body
    
    return CertificateNotificationBatch.model_validate(notifications_data)
    


def lambda_handler(event, context):
    try:
        process_certificate_notification: ProcessCertificateNotification = container.get('process_certificate_notification')
        certificate_notification_tech_floripa: CertificateNotificationTechFloripa = container.get('certificate_notification_tech_floripa')
        
        result: ProcessedCertificateNotification = process_certificate_notification.execute(
            get_notifications_from_event(event)
        )

        notifications: TechFloripaNotification = TechFloripaNotification.from_certificates(result.updated_certificates)
        if certificate_notification_tech_floripa.send_notification(notifications):
            logger.info(f"Notificação enviada com sucesso: {result.updated_certificates[0].product_id}")
            return {
                "statusCode": 200,
                "body": {
                    "message": "Notificação enviada com sucesso",  
                }
            }
        else:
            logger.error(f"Erro ao enviar notificação: {result.updated_certificates[0].product_id}")
            return {
                "statusCode": 500,
                "message": "Erro ao enviar notificação - " + result.updated_certificates[0].product_id
            }
    except Exception as e:
        logger.error(f"Erro ao processar notificação de certificado: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Erro ao processar notificação de certificado",
                "error": str(e)
            })
        }
    

