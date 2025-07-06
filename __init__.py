"""
Telegram Voice Bot - Бот для распознавания речи
"""

from .config import Config
from .voice_bot import VoiceBot
from .models import ChatData
from .chat_manager import ChatManager
from .connection_manager import ConnectionManager
from .utils import setup_logging, split_text

__version__ = "1.0.0"
__all__ = [
    'Config',
    'VoiceBot', 
    'ChatData',
    'ChatManager',
    'ConnectionManager',
    'setup_logging',
    'split_text'
]
