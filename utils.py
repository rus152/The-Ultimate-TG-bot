"""
Утилитарные функции
"""

import logging
from logging.handlers import RotatingFileHandler
from typing import List


def setup_logging(filename: str, level: str = 'INFO') -> None:
    """Улучшенная настройка логирования с ротацией файлов"""
    logger = logging.getLogger()
    
    # Очистка существующих обработчиков
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        filename, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def split_text(text: str, max_length: int) -> List[str]:
    """Улучшенное разделение текста с учетом предложений"""
    if len(text) <= max_length:
        return [text]
    
    # Попытка разделить по предложениям
    sentences = text.split('. ')
    messages = []
    current_message = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Добавляем точку обратно, если она была удалена
        if not sentence.endswith('.') and sentence != sentences[-1]:
            sentence += '.'
        
        if len(current_message) + len(sentence) + 1 <= max_length:
            current_message += (" " if current_message else "") + sentence
        else:
            if current_message:
                messages.append(current_message)
            
            # Если предложение слишком длинное, разделяем по словам
            if len(sentence) > max_length:
                words = sentence.split()
                word_message = ""
                for word in words:
                    if len(word_message) + len(word) + 1 <= max_length:
                        word_message += (" " if word_message else "") + word
                    else:
                        if word_message:
                            messages.append(word_message)
                        word_message = word
                if word_message:
                    current_message = word_message
            else:
                current_message = sentence
    
    if current_message:
        messages.append(current_message)
    
    return messages
