"""
Фабрика для создания провайдеров ASR
"""

import logging
from typing import Dict, Any, Optional, Type
from enum import Enum

from .base import ASRProvider
from .whisper_provider import WhisperProvider
from .nemo_provider import NemoProvider

logger = logging.getLogger(__name__)


class ASRProviderType(Enum):
    """Типы провайдеров ASR"""
    WHISPER = "whisper"
    NEMO = "nemo"


class ASRFactory:
    """Фабрика для создания провайдеров ASR"""
    
    _providers: Dict[ASRProviderType, Type[ASRProvider]] = {
        ASRProviderType.WHISPER: WhisperProvider,
        ASRProviderType.NEMO: NemoProvider,
    }
    
    @classmethod
    def create_provider(
        cls,
        provider_type: ASRProviderType,
        config: Optional[Dict[str, Any]] = None
    ) -> ASRProvider:
        """
        Создание провайдера ASR
        
        Args:
            provider_type: Тип провайдера
            config: Конфигурация для провайдера
            
        Returns:
            Экземпляр провайдера ASR
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Неизвестный тип провайдера: {provider_type}")
        
        provider_class = cls._providers[provider_type]
        
        try:
            logger.info(f"Создание провайдера: {provider_type.value}")
            provider = provider_class(config)
            logger.info(f"Провайдер {provider_type.value} успешно создан")
            return provider
            
        except Exception as e:
            logger.error(f"Ошибка создания провайдера {provider_type.value}: {e}")
            raise
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, str]:
        """Получение списка доступных провайдеров"""
        providers = {}
        
        for provider_type, provider_class in cls._providers.items():
            try:
                # Проверяем, можно ли создать провайдер
                temp_provider = provider_class({})
                providers[provider_type.value] = temp_provider.provider_name
                
            except Exception as e:
                logger.warning(f"Провайдер {provider_type.value} недоступен: {e}")
                providers[provider_type.value] = f"Недоступен: {e}"
        
        return providers
    
    @classmethod
    def create_from_string(
        cls,
        provider_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ASRProvider:
        """
        Создание провайдера из строки
        
        Args:
            provider_name: Имя провайдера ('whisper' или 'nemo')
            config: Конфигурация
            
        Returns:
            Экземпляр провайдера
        """
        try:
            provider_type = ASRProviderType(provider_name.lower())
            return cls.create_provider(provider_type, config)
            
        except ValueError:
            available = list(cls._providers.keys())
            raise ValueError(f"Неизвестный провайдер: {provider_name}. Доступные: {available}")
    
    @classmethod
    def get_default_config(cls, provider_type: ASRProviderType) -> Dict[str, Any]:
        """Получение конфигурации по умолчанию для провайдера"""
        default_configs = {
            ASRProviderType.WHISPER: {
                'model_name': 'turbo',
                'device': 'auto',
                'language': None
            },
            ASRProviderType.NEMO: {
                'model_name': 'nvidia/parakeet-tdt-0.6b-v2',
                'device': 'cuda',
                'batch_size': 1
            }
        }
        
        return default_configs.get(provider_type, {})
    
    @classmethod
    def register_provider(
        cls,
        provider_type: ASRProviderType,
        provider_class: Type[ASRProvider]
    ) -> None:
        """Регистрация нового провайдера"""
        if not issubclass(provider_class, ASRProvider):
            raise TypeError("Класс провайдера должен наследоваться от ASRProvider")
        
        cls._providers[provider_type] = provider_class
        logger.info(f"Провайдер {provider_type.value} зарегистрирован")
    
    @classmethod
    def get_provider_info(cls, provider_type: ASRProviderType) -> Dict[str, Any]:
        """Получение информации о провайдере"""
        if provider_type not in cls._providers:
            raise ValueError(f"Неизвестный тип провайдера: {provider_type}")
        
        provider_class = cls._providers[provider_type]
        
        # Создаем временный экземпляр для получения информации
        try:
            temp_provider = provider_class({})
            return {
                'name': temp_provider.provider_name,
                'supported_formats': temp_provider.supported_formats,
                'available': True,
                'error': None
            }
        except Exception as e:
            return {
                'name': provider_type.value,
                'supported_formats': [],
                'available': False,
                'error': str(e)
            }
