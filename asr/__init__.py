"""
ASR (Automatic Speech Recognition) модуль для Telegram бота
"""

from .base import ASRProvider
from .whisper_provider import WhisperProvider
from .nemo_provider import NemoProvider
from .factory import ASRFactory, ASRProviderType

__all__ = ['ASRProvider', 'WhisperProvider', 'NemoProvider', 'ASRFactory', 'ASRProviderType']
