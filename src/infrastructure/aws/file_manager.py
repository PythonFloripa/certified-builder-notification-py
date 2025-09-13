import logging
from typing import Dict, Any
from src.infrastructure.aws.boto_aws import get_instance_aws, ServiceNameAWS
from src.infrastructure.config.config import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class FileManager:
    """
    Gerencia operações de arquivos no S3.
    """

    def __init__(self):
        self.aws = get_instance_aws(ServiceNameAWS.S3)
        self.bucket_name = config.S3_BUCKET_NAME

    def get_url(self, key: str) -> str:
        """
        Gera uma URL pré-assinada para acessar (GET) um objeto no S3.
        Configura response-content-disposition=inline para visualização direta no navegador.
        
        Args:
            key: Chave do objeto no S3
            
        Returns:
            URL pré-assinada para acesso ao objeto (válida por 7 dias)
            
        Raises:
            Exception: Se houver erro ao gerar a URL
        """
        try:
            logger.info(f"Getting URL for key {key}")
            
            # Gera URL pré-assinada para GET com response-content-disposition=inline
            # Tempo de expiração configurado para 7 dias (604800 segundos)
            presigned_url = self.aws.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ResponseContentDisposition': 'inline'
                },
                ExpiresIn=604800  # 7 dias em segundos
            )
            
            logger.info(f"Successfully retrieved URL for key {presigned_url}")
            return presigned_url
            
        except Exception as e:
            logger.error(f"Error generating presigned URL for key {key}: {e}")
            return None

    def check_key_exists(self, key: str) -> bool:
        """
        Verifica se uma chave (key) existe no bucket S3.
        
        Args:
            key: Chave do objeto no S3
            
        Returns:
            bool: True se a chave existir, False caso contrário
        """
        try:
            logger.info(f"Verificando existência da chave: {key}")
            
            # Usa head_object para verificar se o objeto existe sem baixá-lo
            self.aws.head_object(Bucket=self.bucket_name, Key=key)
            
            logger.info(f"Chave {key} encontrada no bucket")
            return True
            
        except self.aws.exceptions.NoSuchKey:
            logger.info(f"Chave {key} não encontrada no bucket")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar existência da chave {key}: {e}")
            return False

    def generate_download_url(self, certificate_id: str) -> str:
        """
        Gera URL de download usando API Gateway baseada no ID do certificado.
        
        Args:
            certificate_id: ID do certificado (UUID)
            
        Returns:
            str: URL completa para download do certificado via API Gateway
        """
        try:
            # Obtém a URL base do endpoint de download da configuração centralizada
            download_base_url = config.API_GATEWAY_DOWNLOAD_URL
            
            if not download_base_url:
                logger.error("Configuração API_GATEWAY_DOWNLOAD_URL não encontrada")
                return ""
            
            # Constrói URL completa para o certificado específico
            download_url = f"{download_base_url}?id={certificate_id}"
            
            logger.info(f"URL de download gerada: {download_url}")
            return download_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar URL de download para certificado {certificate_id}: {e}")
            return ""
    