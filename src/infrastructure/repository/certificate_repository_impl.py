import json
import logging
from typing import List, Optional
from src.domain.entity.certificate import Certificate
from src.domain.repository.certificate_repository import CertificateRepository
from src.infrastructure.aws.dynamodb_service import DynamoDBService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CertificateRepositoryImpl(CertificateRepository):    
    def __init__(self, dynamodb_service: DynamoDBService, entity_name: str = "certificates"):
        # Armazena o nome da entidade ao invés do nome completo da tabela
        self.dynamodb_service = dynamodb_service
        self.entity_name = entity_name
    
    def create(self, entity: Certificate) -> Certificate:
        try:
            item = entity.model_dump()
            # Usa build_table_name para obter o nome correto da tabela
            self.dynamodb_service.put_item(item, self.entity_name)
            
            logger.info(f"Certificado criado com sucesso: {entity.id}")
            return entity
            
        except Exception as e:
            logger.error(f"Erro ao criar certificado: {str(e)}")
            raise
    
    def get_by_id(self, entity_id: str) -> Optional[Certificate]:
        """
        Busca um certificado pelo ID.
        Para manter compatibilidade com BaseRepository, usa scan para buscar por id.
        """
        try:
            # Usa scan para buscar apenas por id, seguindo o contrato do BaseRepository
            filter_expression = "id = :id"
            expression_values = {":id": entity_id}
            
            items = self.dynamodb_service.scan_table(
                self.entity_name, 
                filter_expression, 
                expression_values
            )
            
            if items:
                return Certificate(**items[0])
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar certificado por ID {entity_id}: {str(e)}")
            raise
    
    def get_all(self) -> List[Certificate]:
        try:
            items = self.dynamodb_service.scan_table(self.entity_name)
            certificates = []
            
            for item in items:
                certificates.append(Certificate(**item))
            
            return certificates
            
        except Exception as e:
            logger.error(f"Erro ao buscar todos os certificados: {str(e)}")
            raise
    
    def update(self, entity_id: str, entity: Certificate) -> Optional[Certificate]:
        try:
            # Para o método update do BaseRepository, usamos o entity_id como string
            # mas precisamos da chave composta. O entity_id será o id da entidade.
            # Primeiro buscamos o certificado para obter o order_id
            existing_certificate = self.get_by_id(entity_id)
            if not existing_certificate:
                logger.warning(f"Certificado não encontrado para atualização: {entity_id}")
                return None
            
            # Converte a entidade para dicionário
            update_data = entity.model_dump()
            
            # Remove as chaves primárias do update_data
            if 'id' in update_data:
                del update_data['id']
            if 'order_id' in update_data:
                del update_data['order_id']
            
            if 'authenticity_verification_url' in update_data:
                del update_data['authenticity_verification_url']
            if 'validation_code' in update_data:
                del update_data['validation_code']

            # Constrói a expressão de atualização
            update_expression = "SET "
            expression_values = {}
            expression_names = {}
            
            for key, value in update_data.items():
                if value is not None:
                    update_expression += f"#{key} = :{key}, "
                    expression_values[f":{key}"] = value
                    expression_names[f"#{key}"] = key
            
            # Remove a vírgula extra no final
            update_expression = update_expression.rstrip(", ")
            
            # Converte os valores para o formato JSON do DynamoDB
            expression_values = self.dynamodb_service._convert_to_dynamodb_format(expression_values)
            
            # Atualiza o item usando a chave composta
            key = {"id": str(entity_id), "order_id": existing_certificate.order_id}
            # Converte a chave para o formato JSON do DynamoDB
            key = self.dynamodb_service._convert_to_dynamodb_format(key)
            
            # CORREÇÃO: Usa build_table_name para obter o nome correto da tabela
            response = self.dynamodb_service.aws.update_item(
                TableName=self.dynamodb_service.build_table_name(self.entity_name),
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names,
                ReturnValues="ALL_NEW"
            )
            
            if 'Attributes' in response:
                # Converte a resposta do DynamoDB de volta para Certificate
                result_dict = self.dynamodb_service._convert_from_dynamodb_format(response['Attributes'])
                return Certificate(**result_dict)
            return None
            
        except Exception as e:
            logger.error(f"Erro ao atualizar certificado {entity_id}: {str(e)}")
            raise
    
    def delete(self, entity_id: str) -> bool:
        """
        Remove um certificado pelo ID.
        Para manter compatibilidade com BaseRepository, busca por id e remove.
        """
        try:
            # Primeiro busca o certificado para obter a chave completa
            filter_expression = "id = :id"
            expression_values = {":id": entity_id}
            
            items = self.dynamodb_service.scan_table(
                self.entity_name, 
                filter_expression, 
                expression_values
            )
            
            if items:
                # Deleta o primeiro item encontrado
                item = items[0]
                key = {"id": item['id'], "order_id": item['order_id']}
                self.dynamodb_service.delete_item(key, self.entity_name)
                
                logger.info(f"Certificado {entity_id} removido com sucesso")
                return True
            
            logger.warning(f"Certificado {entity_id} não encontrado para remoção")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover certificado {entity_id}: {str(e)}")
            return False
    
    def exists(self, entity_id: str) -> bool:
        """
        Verifica se um certificado existe pelo ID.
        Para manter compatibilidade com BaseRepository, usa scan para buscar por id.
        """
        try:
            # Usa scan para buscar apenas por id, seguindo o contrato do BaseRepository
            filter_expression = "id = :id"
            expression_values = {":id": entity_id}
            
            items = self.dynamodb_service.scan_table(
                self.entity_name, 
                filter_expression, 
                expression_values
            )
            
            return len(items) > 0
            
        except Exception as e:
            logger.error(f"Erro ao verificar existência do certificado {entity_id}: {str(e)}")
            return False
    
    def get_by_order_id(self, order_id: int) -> List[Certificate]:
        try:
            # Como a tabela tem chave composta (id + order_id), usamos scan para buscar por order_id
            filter_expression = "order_id = :order_id"
            expression_values = {":order_id": order_id}
            
            items = self.dynamodb_service.scan_table(
                self.entity_name, 
                filter_expression, 
                expression_values
            )
            
            certificates = []
            for item in items:
                certificates.append(Certificate(**item))
            
            return certificates
            
        except Exception as e:
            logger.error(f"Erro ao buscar certificados por order_id {order_id}: {str(e)}")
            raise
    
    def get_by_participant_email(self, email: str) -> List[Certificate]:
        try:
            filter_expression = "participant_email = :email"
            expression_values = {":email": email}
            
            items = self.dynamodb_service.scan_table(
                self.entity_name, 
                filter_expression, 
                expression_values
            )
            
            certificates = []
            for item in items:
                certificates.append(Certificate(**item))
            
            return certificates
            
        except Exception as e:
            logger.error(f"Erro ao buscar certificados por email {email}: {str(e)}")
            raise
    
    def get_by_email_and_product_id(self, email: str, product_id: int) -> List[Certificate]:
        """
        Busca certificados por email do participante e product_id.
        Usado pelo endpoint que recebe email como path e product_id como query parameter.
        """
        try:
            filter_expression = "participant_email = :email AND product_id = :product_id"
            expression_values = {
                ":email": email,
                ":product_id": product_id
            }
            
            items = self.dynamodb_service.scan_table(
                self.entity_name, 
                filter_expression, 
                expression_values
            )
            
            certificates = []
            for item in items:
                certificates.append(Certificate(**item))
            
            logger.info(f"Encontrados {len(certificates)} certificados para email {email} e product_id {product_id}")
            return certificates
            
        except Exception as e:
            logger.error(f"Erro ao buscar certificados por email {email} e product_id {product_id}: {str(e)}")
            raise
    
    def get_by_product_id(self, product_id: int) -> List[Certificate]:
        try:
            filter_expression = "product_id = :product_id"
            expression_values = {":product_id": product_id}
            
            items = self.dynamodb_service.scan_table(
                self.entity_name, 
                filter_expression, 
                expression_values
            )
            
            certificates = []
            for item in items:
                certificates.append(Certificate(**item))
            
            return certificates
            
        except Exception as e:
            logger.error(f"Erro ao buscar certificados por product_id {product_id}: {str(e)}")
            raise
    
    def get_successful_certificates(self) -> List[Certificate]:
        try:
            filter_expression = "success = :success"
            expression_values = {":success": True}
            
            items = self.dynamodb_service.scan_table(
                self.entity_name, 
                filter_expression, 
                expression_values
            )
            
            certificates = []
            for item in items:
                certificates.append(Certificate(**item))
            
            return certificates
            
        except Exception as e:
            logger.error(f"Erro ao buscar certificados bem-sucedidos: {str(e)}")
            raise
