import logging
import httpx
from typing import Dict, Any
from retry import retry
from src.infrastructure.config.config import config
from src.domain.dto.tech_floripa_notification import TechFloripaNotification

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CertificateNotificationTechFloripa:
    """
    Processa notificações de certificados para a Tech Floripa.
    """

    def __init__(self):
        self.url = config.URL_SERVICE_TECH + "/notifies-generation-certificates"
        self.timeout_config = httpx.Timeout(
            connect=15.0,  # Timeout para estabelecer conexão (aumentado)
            read=60.0,     # Timeout para ler resposta (aumentado)
            write=15.0,    # Timeout para enviar dados (aumentado)
            pool=60.0      # Timeout para pool de conexões (aumentado)
        )
        
        # Headers para simular navegador real e melhorar compatibilidade
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'close',  # Evita keep-alive que pode causar problemas
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    @retry(
        exceptions=(httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException),
        tries=3,
        delay=2,
        backoff=2,
        logger=logger
    )
    def send_notification(self, notifications: TechFloripaNotification):
        try:
            logger.info(f"Enviando notificação para a API da Tech Floripa: {notifications.model_dump()}")
            with httpx.Client(
                timeout=self.timeout_config,
                headers=self.headers,
                limits=httpx.Limits(max_keepalive_connections=0, max_connections=5)  # Desabilita keep-alive
                ) as client:
                response = client.post(self.url, json=notifications.model_dump())
                response.raise_for_status()
                logger.info(f"Notificação enviada com sucesso: {response.status_code}")
                return response.status_code == 200
        except httpx.TimeoutException as e:
            logger.error(f"Timeout na conexão: {e}")
            raise Exception(f"Timeout ao conectar com a API: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP {e.response.status_code}: {e}")
            raise Exception(f"Erro HTTP {e.response.status_code}: {e}")
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão: {e}")
            raise Exception(f"Erro de rede: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar ordens: {e}")
            raise