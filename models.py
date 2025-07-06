"""
Модели данных для бота
"""

from dataclasses import dataclass


@dataclass
class ChatData:
    """Данные чата для обработки"""
    chat_id: int
    message_id: int
    path: str
