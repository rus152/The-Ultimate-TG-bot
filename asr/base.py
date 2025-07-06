"""
Базовый абстрактный класс для провайдеров ASR
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ASRProvider(ABC):
    """Абстрактный базовый класс для провайдеров распознавания речи"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model = None
        self.is_loaded = False
        
    @abstractmethod
    def load_model(self) -> None:
        """Загрузка модели"""
        pass
    
    @abstractmethod
    def transcribe(self, audio_path: Union[str, Path]) -> str:
        """
        Транскрибирование аудиофайла
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            Распознанный текст
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Имя провайдера"""
        pass
    
    @property
    @abstractmethod
    def supported_formats(self) -> list:
        """Поддерживаемые форматы аудио"""
        pass
    
    def is_model_loaded(self) -> bool:
        """Проверка, загружена ли модель"""
        return self.is_loaded
    
    def validate_audio_file(self, audio_path: Union[str, Path]) -> bool:
        """Валидация аудиофайла"""
        path = Path(audio_path)
        
        if not path.exists():
            logger.error(f"Аудиофайл не найден: {audio_path}")
            return False
            
        if not path.is_file():
            logger.error(f"Путь не является файлом: {audio_path}")
            return False
            
        if path.suffix.lower() not in self.supported_formats:
            logger.warning(f"Возможно неподдерживаемый формат: {path.suffix}")
            
        return True
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        logger.info(f"Очистка ресурсов для провайдера {self.provider_name}")
        self.model = None
        self.is_loaded = False
