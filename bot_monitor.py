"""
Модуль для мониторинга состояния бота
"""

import logging
import psutil
import time
from typing import Dict, Any
from datetime import datetime

from config import Config
from chat_manager import ChatManager
from connection_manager import ConnectionManager


class BotMonitor:
    """Класс для мониторинга состояния бота"""
    
    def __init__(self, config: Config, chat_manager: ChatManager, 
                 connection_manager: ConnectionManager):
        self.config = config
        self.chat_manager = chat_manager
        self.connection_manager = connection_manager
        self.start_time = datetime.now()
        self.logger = logging.getLogger(__name__)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Получение информации о системе"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'uptime': str(datetime.now() - self.start_time)
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о системе: {e}")
            return {}
    
    def get_bot_status(self) -> Dict[str, Any]:
        """Получение статуса бота"""
        return {
            'queue_size': self.chat_manager.count_chats(),
            'queue_empty': self.chat_manager.is_empty(),
            'internet_connection': self.connection_manager.check_internet_connection(),
            'start_time': self.start_time.isoformat(),
            'config': self.config.to_dict()
        }
    
    def get_full_status(self) -> Dict[str, Any]:
        """Получение полного статуса"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system': self.get_system_info(),
            'bot': self.get_bot_status()
        }
    
    def log_status(self) -> None:
        """Логирование текущего статуса"""
        status = self.get_full_status()
        self.logger.info(f"Статус бота: {status}")
    
    def monitor_loop(self, interval: int = 300) -> None:
        """Основной цикл мониторинга"""
        while True:
            try:
                self.log_status()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.logger.info("Мониторинг остановлен")
                break
            except Exception as e:
                self.logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(60)  # Пауза при ошибке
