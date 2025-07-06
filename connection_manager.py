"""
Менеджер соединений с автоматическим переподключением
"""

import time
import socket
import logging
import requests
import telebot
from urllib3.exceptions import ProtocolError
from http.client import RemoteDisconnected


class ConnectionManager:
    """Менеджер соединений с автоматическим переподключением"""
    
    def __init__(self, bot_token: str, max_retries: int = 5, retry_delay: int = 5):
        self.bot_token = bot_token
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connection_errors = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
            ProtocolError,
            RemoteDisconnected,
            socket.error,
            OSError,
            telebot.apihelper.ApiTelegramException
        )
    
    def check_internet_connection(self) -> bool:
        """Проверяет наличие интернет-соединения"""
        try:
            # Проверяем доступность DNS Google
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except (socket.error, OSError):
            return False
    
    def wait_for_connection(self) -> None:
        """Ждет восстановления интернет-соединения"""
        while not self.check_internet_connection():
            logging.warning("Нет интернет-соединения. Повторная попытка через 10 секунд...")
            time.sleep(10)
        logging.info("Интернет-соединение восстановлено")
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Выполняет функцию с автоматическими повторными попытками"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except self._connection_errors as e:
                logging.error(f"Ошибка соединения (попытка {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    # Проверяем интернет-соединение
                    if not self.check_internet_connection():
                        self.wait_for_connection()
                    
                    delay = self.retry_delay * (2 ** attempt)  # Экспоненциальная задержка
                    logging.info(f"Повторная попытка через {delay} секунд...")
                    time.sleep(delay)
                else:
                    logging.error("Все попытки переподключения исчерпаны")
                    raise
        
        return None
