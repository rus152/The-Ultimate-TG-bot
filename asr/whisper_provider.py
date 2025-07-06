"""
Провайдер для OpenAI Whisper
"""

import whisper
import logging
from typing import Dict, Any, Union, Optional
from pathlib import Path
from torch import cuda

from .base import ASRProvider

logger = logging.getLogger(__name__)


class WhisperProvider(ASRProvider):
    """Провайдер для OpenAI Whisper"""
    
    AVAILABLE_MODELS = {
        'tiny': 'Наименьшая модель, быстрая но менее точная',
        'base': 'Базовая модель, баланс скорости и точности',
        'small': 'Небольшая модель, хорошая точность',
        'medium': 'Средняя модель, высокая точность',
        'large': 'Большая модель, максимальная точность',
        'turbo': 'Оптимизированная модель, быстрая и точная'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model_name = self.config.get('model_name', 'turbo')
        self.device = self.config.get('device', 'auto')
        self.language = self.config.get('language', None)
        
    @property
    def provider_name(self) -> str:
        return "OpenAI Whisper"
    
    @property
    def supported_formats(self) -> list:
        return ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.opus', '.wma']
    
    def load_model(self) -> None:
        """Загрузка модели Whisper"""
        try:
            logger.info(f"Загрузка модели Whisper: {self.model_name}")
            
            # Определение устройства
            if self.device == 'auto':
                device = "cuda" if cuda.is_available() else "cpu"
                logger.info(f"Автоматически выбрано устройство: {device}")
            else:
                device = self.device
                logger.info(f"Используется устройство: {device}")
            
            # Загрузка модели
            self.model = whisper.load_model(self.model_name, device=device)
            self.is_loaded = True
            
            logger.info(f"Модель {self.model_name} успешно загружена на {device}")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели Whisper: {e}")
            raise
    
    def transcribe(self, audio_path: Union[str, Path]) -> str:
        """Транскрибирование аудиофайла с помощью Whisper"""
        if not self.is_loaded:
            raise RuntimeError("Модель не загружена. Вызовите load_model() сначала.")
        
        if not self.validate_audio_file(audio_path):
            raise ValueError(f"Невалидный аудиофайл: {audio_path}")
        
        try:
            logger.info(f"Начало транскрипции файла: {audio_path}")
            
            # Опции для транскрипции
            options = {}
            if self.language:
                options['language'] = self.language
            
            # Транскрипция
            result = self.model.transcribe(str(audio_path), **options)
            transcription = result['text'].strip()
            
            logger.info(f"Транскрипция завершена. Длина текста: {len(transcription)} символов")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Ошибка транскрипции: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели Whisper"""
        info = {
            'provider': self.provider_name,
            'model_name': self.model_name,
            'device': self.device,
            'language': self.language,
            'is_loaded': self.is_loaded,
            'supported_formats': self.supported_formats,
            'available_models': self.AVAILABLE_MODELS
        }
        
        if self.is_loaded:
            info['cuda_available'] = cuda.is_available()
            info['model_description'] = self.AVAILABLE_MODELS.get(
                self.model_name, 
                'Неизвестная модель'
            )
        
        return info
    
    def set_language(self, language: str) -> None:
        """Установка языка для распознавания"""
        self.language = language
        logger.info(f"Установлен язык: {language}")
    
    def change_model(self, model_name: str) -> None:
        """Смена модели (требует перезагрузки)"""
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Неизвестная модель: {model_name}")
        
        self.model_name = model_name
        logger.info(f"Модель изменена на: {model_name}")
        
        # Перезагрузка модели
        if self.is_loaded:
            self.cleanup()
            self.load_model()
    
    def cleanup(self) -> None:
        """Очистка ресурсов Whisper"""
        super().cleanup()
        logger.info("Ресурсы Whisper очищены")
