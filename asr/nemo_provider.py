"""
Провайдер для NVIDIA NeMo ASR
"""

import logging
from typing import Dict, Any, Union, List
from pathlib import Path

from .base import ASRProvider

logger = logging.getLogger(__name__)


class NemoProvider(ASRProvider):
    """Провайдер для NVIDIA NeMo ASR"""
    
    AVAILABLE_MODELS = {
        'nvidia/parakeet-tdt-0.6b-v2': 'Parakeet TDT 0.6B v2 - быстрая модель',
        'nvidia/parakeet-tdt-1.1b': 'Parakeet TDT 1.1B - средняя модель',
        # Добавьте другие модели по мере необходимости
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.model_name = self.config.get('model_name', 'nvidia/parakeet-tdt-0.6b-v2')
        self.device = self.config.get('device', 'cuda')
        self.batch_size = self.config.get('batch_size', 1)
        self.nemo_asr = None
        
        # Проверка наличия nemo
        self._check_nemo_installation()
    
    def _check_nemo_installation(self) -> None:
        """Проверка установки NeMo"""
        try:
            import nemo.collections.asr as nemo_asr
            self.nemo_asr = nemo_asr
            logger.info("NeMo ASR найден и импортирован")
        except ImportError as e:
            logger.error(f"NeMo ASR не установлен: {e}")
            logger.info("Для установки используйте: pip install nemo_toolkit[asr]")
            raise ImportError("NeMo ASR не найден. Установите nemo_toolkit[asr]")
    
    @property
    def provider_name(self) -> str:
        return "NVIDIA NeMo ASR"
    
    @property
    def supported_formats(self) -> list:
        return ['.wav', '.flac', '.mp3', '.ogg']
    
    def load_model(self) -> None:
        """Загрузка модели NeMo"""
        try:
            logger.info(f"Загрузка модели NeMo: {self.model_name}")
            
            # Загрузка предобученной модели
            self.model = self.nemo_asr.models.ASRModel.from_pretrained(
                model_name=self.model_name
            )
            
            # Перенос на устройство
            if self.device == 'cuda':
                self.model = self.model.cuda()
            
            self.is_loaded = True
            logger.info(f"Модель {self.model_name} успешно загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели NeMo: {e}")
            raise
    
    def transcribe(self, audio_path: Union[str, Path]) -> str:
        """Транскрибирование аудиофайла с помощью NeMo"""
        if not self.is_loaded:
            raise RuntimeError("Модель не загружена. Вызовите load_model() сначала.")
        
        if not self.validate_audio_file(audio_path):
            raise ValueError(f"Невалидный аудиофайл: {audio_path}")
        
        try:
            logger.info(f"Начало транскрипции файла: {audio_path}")
            
            # Транскрипция
            audio_files = [str(audio_path)]
            results = self.model.transcribe(audio_files)
            
            if results and len(results) > 0:
                transcription = results[0].text.strip()
                logger.info(f"Транскрипция завершена. Длина текста: {len(transcription)} символов")
                return transcription
            else:
                logger.warning("Результат транскрипции пуст")
                return ""
                
        except Exception as e:
            logger.error(f"Ошибка транскрипции NeMo: {e}")
            raise
    
    def transcribe_batch(self, audio_paths: List[Union[str, Path]]) -> List[str]:
        """Пакетная транскрипция (преимущество NeMo)"""
        if not self.is_loaded:
            raise RuntimeError("Модель не загружена. Вызовите load_model() сначала.")
        
        logger.info(f"Начало пакетной транскрипции {len(audio_paths)} файлов")
        
        try:
            # Валидация всех файлов
            valid_paths = []
            for path in audio_paths:
                if self.validate_audio_file(path):
                    valid_paths.append(str(path))
                else:
                    logger.warning(f"Пропуск невалидного файла: {path}")
            
            if not valid_paths:
                logger.error("Нет валидных файлов для транскрипции")
                return []
            
            # Пакетная транскрипция
            results = self.model.transcribe(valid_paths)
            
            transcriptions = []
            for result in results:
                transcriptions.append(result.text.strip())
            
            logger.info(f"Пакетная транскрипция завершена: {len(transcriptions)} результатов")
            return transcriptions
            
        except Exception as e:
            logger.error(f"Ошибка пакетной транскрипции: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели NeMo"""
        info = {
            'provider': self.provider_name,
            'model_name': self.model_name,
            'device': self.device,
            'batch_size': self.batch_size,
            'is_loaded': self.is_loaded,
            'supported_formats': self.supported_formats,
            'available_models': self.AVAILABLE_MODELS,
            'supports_batch': True
        }
        
        if self.is_loaded:
            try:
                import torch
                info['cuda_available'] = torch.cuda.is_available()
                info['model_description'] = self.AVAILABLE_MODELS.get(
                    self.model_name, 
                    'Неизвестная модель'
                )
            except ImportError:
                info['cuda_available'] = False
        
        return info
    
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
        """Очистка ресурсов NeMo"""
        super().cleanup()
        logger.info("Ресурсы NeMo очищены")
