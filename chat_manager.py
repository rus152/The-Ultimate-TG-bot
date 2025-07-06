"""
Менеджер очереди чатов
"""

import logging
from threading import Lock
from typing import List, Optional

from models import ChatData


class ChatManager:
    """Менеджер очереди чатов с поддержкой многопоточности"""
    
    def __init__(self):
        logging.info('Initializing chat manager')
        self._chat_data: List[ChatData] = []
        self._lock = Lock()

    def add_chat(self, chat_id: int, message_id: int, path: str) -> None:
        """Добавляет чат в очередь"""
        logging.info('Adding new chat to queue')
        with self._lock:
            self._chat_data.append(ChatData(chat_id, message_id, path))

    def remove_chat(self) -> None:
        """Удаляет первый чат из очереди"""
        logging.info('Removing first chat from queue')
        with self._lock:
            if self._chat_data:
                self._chat_data.pop(0)

    def display_chats(self) -> str:
        """Возвращает строковое представление всех чатов в очереди"""
        logging.info('Displaying all chats in queue')
        with self._lock:
            if not self._chat_data:
                return "No chats in queue"
            
            result = []
            for item in self._chat_data:
                result.append(f"Chat: {item.chat_id}, Message: {item.message_id}, Path: {item.path}")
            return "\n".join(result)

    def get_first_chat(self) -> Optional[ChatData]:
        """Возвращает первый чат в очереди без удаления"""
        logging.info('Getting first chat in queue')
        with self._lock:
            return self._chat_data[0] if self._chat_data else None

    def count_chats(self) -> int:
        """Возвращает количество чатов в очереди"""
        with self._lock:
            return len(self._chat_data)

    def is_empty(self) -> bool:
        """Проверяет, пуста ли очередь"""
        with self._lock:
            return len(self._chat_data) == 0
