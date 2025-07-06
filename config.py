"""
Конфигурация бота
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Config:
    """Конфигурация бота с настройками по умолчанию"""
    
    # Основные настройки
    telegram_bot_token: str
    debug_chat_id: Optional[int] = None
    debug_mode: bool = False
    
    # Папки для файлов
    voice_folder: str = 'voice_messages'
    video_note_folder: str = 'video_notes'
    
    # Настройки обработки
    max_message_length: int = 3696
    log_level: str = 'INFO'
    
    # ASR настройки
    asr_provider: str = 'whisper'
    asr_model_name: str = 'turbo'
    asr_device: str = 'auto'
    asr_language: Optional[str] = None
    
    # Значения по умолчанию
    DEFAULT_VALUES = {
        'DEBUG_MODE': 'False',
        'VOICE_FOLDER': 'voice_messages',
        'VIDEO_NOTE_FOLDER': 'video_notes',
        'MAX_MESSAGE_LENGTH': '3696',
        'LOG_LEVEL': 'INFO',
        'ASR_PROVIDER': 'whisper',
        'ASR_MODEL_NAME': 'turbo',
        'ASR_DEVICE': 'auto',
        'ASR_LANGUAGE': None
    }
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Создает конфигурацию из переменных окружения"""
        # Обязательные параметры
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError('TELEGRAM_BOT_TOKEN not found in environment variables')
        
        # Парсинг DEBUG_CHAT_ID
        debug_chat_id_str = os.getenv('DEBUG_CHAT_ID')
        debug_chat_id = None
        if debug_chat_id_str:
            try:
                debug_chat_id = int(debug_chat_id_str)
            except ValueError:
                raise ValueError('Invalid DEBUG_CHAT_ID. It should be a numeric value.')
        
        # Получение остальных параметров с использованием значений по умолчанию
        debug_mode = os.getenv('DEBUG_MODE', cls.DEFAULT_VALUES['DEBUG_MODE']).lower() == 'true'
        voice_folder = os.getenv('VOICE_FOLDER', cls.DEFAULT_VALUES['VOICE_FOLDER'])
        video_note_folder = os.getenv('VIDEO_NOTE_FOLDER', cls.DEFAULT_VALUES['VIDEO_NOTE_FOLDER'])
        max_message_length = int(os.getenv('MAX_MESSAGE_LENGTH', cls.DEFAULT_VALUES['MAX_MESSAGE_LENGTH']))
        log_level = os.getenv('LOG_LEVEL', cls.DEFAULT_VALUES['LOG_LEVEL'])
        
        # ASR настройки
        asr_provider = os.getenv('ASR_PROVIDER', cls.DEFAULT_VALUES['ASR_PROVIDER'])
        asr_model_name = os.getenv('ASR_MODEL_NAME', cls.DEFAULT_VALUES['ASR_MODEL_NAME'])
        asr_device = os.getenv('ASR_DEVICE', cls.DEFAULT_VALUES['ASR_DEVICE'])
        asr_language = os.getenv('ASR_LANGUAGE', cls.DEFAULT_VALUES['ASR_LANGUAGE'])
        
        return cls(
            telegram_bot_token=token,
            debug_chat_id=debug_chat_id,
            debug_mode=debug_mode,
            voice_folder=voice_folder,
            video_note_folder=video_note_folder,
            max_message_length=max_message_length,
            log_level=log_level,
            asr_provider=asr_provider,
            asr_model_name=asr_model_name,
            asr_device=asr_device,
            asr_language=asr_language
        )
    
    def get_asr_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию для ASR провайдера"""
        return {
            'model_name': self.asr_model_name,
            'device': self.asr_device,
            'language': self.asr_language
        }
    
    @classmethod
    def get_default_value(cls, key: str) -> str:
        """Получает значение по умолчанию для указанного ключа"""
        return cls.DEFAULT_VALUES.get(key, '')
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует конфигурацию в словарь"""
        return {
            'telegram_bot_token': '***' if self.telegram_bot_token else None,
            'debug_chat_id': self.debug_chat_id,
            'debug_mode': self.debug_mode,
            'voice_folder': self.voice_folder,
            'video_note_folder': self.video_note_folder,
            'max_message_length': self.max_message_length,
            'log_level': self.log_level,
            'asr_provider': self.asr_provider,
            'asr_model_name': self.asr_model_name,
            'asr_device': self.asr_device,
            'asr_language': self.asr_language
        }
