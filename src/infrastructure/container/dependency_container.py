"""
Container de Dependências para centralizar a injeção de dependências.
Segue o padrão Dependency Injection Container para Clean Architecture.
"""
from typing import Dict, Any, Callable
from src.infrastructure.aws.dynamodb_service import DynamoDBService
from src.infrastructure.repository.certificate_repository_impl import CertificateRepositoryImpl
from src.infrastructure.aws.file_manager import FileManager
from src.infrastructure.config.config import config

class DependencyContainer:
    """
    Container de dependências que centraliza a criação e injeção de dependências.
    Segue o padrão Singleton para garantir uma única instância.
    """
    
    _instance = None
    _services: Dict[str, Any] = {}
    _singletons: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DependencyContainer, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._services:
            self._register_services()
    
    def _register_services(self):
        """
        Registra todos os serviços no container.
        Define como cada dependência deve ser criada.
        """
        # Registra serviços de infraestrutura
        self._services['dynamodb_service'] = self._create_dynamodb_service
        self._services['file_manager'] = self._create_file_manager
        # Registra repositórios
        self._services['certificate_repository'] = self._create_certificate_repository
        # Registra aplicações
        self._services['certificate_notification_tech_floripa'] = self._create_certificate_notification_tech_floripa
        
        self._services['process_certificate_notification'] = self._create_process_certificate_notification

    def get(self, service_name: str) -> Any:
        """
        Obtém uma instância do serviço solicitado.
        Cria singleton automaticamente se necessário.
        
        Args:
            service_name: Nome do serviço registrado
            
        Returns:
            Any: Instância do serviço
        """
        if service_name not in self._services:
            raise ValueError(f"Serviço '{service_name}' não registrado no container")
        
        # Verifica se já existe uma instância singleton
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Cria nova instância
        instance = self._services[service_name]()
        
        # Armazena como singleton se necessário
        self._singletons[service_name] = instance
        
        return instance
    
    def reset(self):
        """
        Reseta o container, removendo todas as instâncias singleton.
        Útil para testes.
        """
        self._singletons.clear()
    
    # Métodos de criação de serviços de infraestrutura
    def _create_dynamodb_service(self) -> DynamoDBService:
        """Cria uma instância do DynamoDBService."""
        return DynamoDBService()
    
    def _create_file_manager(self) -> FileManager:
        """Cria uma instância do FileManager."""
        return FileManager()
    
    def _create_certificate_notification_tech_floripa(self):
        """Cria uma instância do CertificateNotificationTechFloripa."""
        # Importação dinâmica para evitar importação circular
        from src.application.certificate_notification_tech_floripa import CertificateNotificationTechFloripa
        return CertificateNotificationTechFloripa()
    
    # Métodos de criação de repositórios
    def _create_certificate_repository(self) -> CertificateRepositoryImpl:
        """Cria uma instância do CertificateRepositoryImpl."""
        dynamodb_service = self.get('dynamodb_service')
        # Passa apenas o nome da entidade, não o nome completo da tabela
        return CertificateRepositoryImpl(dynamodb_service, 'certificates')

    def _create_process_certificate_notification(self):
        """Cria uma instância do ProcessCertificateNotification."""
        # Importação dinâmica para evitar importação circular
        from src.application.process_certificate_notification import ProcessCertificateNotification
        
        # Injeta as dependências necessárias no construtor
        certificate_repository = self.get('certificate_repository')
        file_manager = self.get('file_manager')
        
        return ProcessCertificateNotification(certificate_repository, file_manager)

# Instância global do container
container = DependencyContainer()
