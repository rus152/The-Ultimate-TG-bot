# main.py

import os
import logging
import time
import contextlib
from threading import Thread, Lock
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from logging.handlers import RotatingFileHandler
import socket
import requests
from urllib3.exceptions import ProtocolError
from http.client import RemoteDisconnected

import telebot
from telebot.formatting import hcite
from pydub import AudioSegment

# Импорт ASR модуля
from asr import ASRFactory, ASRProviderType


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


@dataclass
class ChatData:
    chat_id: int
    message_id: int
    path: str


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


class VoiceBot:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        self.setup()

        self.bot = telebot.TeleBot(self.config.telegram_bot_token)
        self.connection_manager = ConnectionManager(self.config.telegram_bot_token)
        logging.info('API Token obtained')

        self.chat_manager = ChatManager()

        # Инициализация ASR провайдера
        self._setup_asr_provider()

    def _setup_asr_provider(self):
        """Настройка ASR провайдера"""
        try:
            logging.info(f'Setting up ASR provider: {self.config.asr_provider}')
            
            # Создание провайдера с использованием конфигурации
            self.asr_provider = ASRFactory.create_from_string(
                self.config.asr_provider, 
                self.config.get_asr_config()
            )
            
            # Загрузка модели
            self.asr_provider.load_model()
            logging.info(f'ASR provider loaded: {self.asr_provider.provider_name}')
            
        except Exception as e:
            logging.error(f'Error setting up ASR provider: {e}')
            exit(1)

    def setup(self):
        os.makedirs(self.config.voice_folder, exist_ok=True)
        logging.info('Voice messages folder is ready')

        os.makedirs(self.config.video_note_folder, exist_ok=True)
        logging.info('Video notes folder is ready')

    def start(self):
        """Запуск бота с автоматическим переподключением"""
        logging.info('Bot started')
        
        threading_list = [
            Thread(target=self.voice_handler, daemon=True),
            #Thread(target=self.queue_manager, daemon=True)
        ]

        for thread in threading_list:
            thread.start()
            
        self.register_handlers()
        
        # Запуск polling с автоматическим переподключением
        self.start_polling_with_retry()
    
    def start_polling_with_retry(self):
        """Запуск polling с автоматическим переподключением при сбоях"""
        while True:
            try:
                logging.info("Запуск polling...")
                self.bot.polling(none_stop=True, interval=0, timeout=20)
            except Exception as e:
                logging.error(f"Ошибка polling: {e}")
                
                # Проверяем интернет-соединение
                if not self.connection_manager.check_internet_connection():
                    logging.warning("Отсутствует интернет-соединение")
                    self.connection_manager.wait_for_connection()
                
                # Пауза перед перезапуском
                retry_delay = 10
                logging.info(f"Перезапуск через {retry_delay} секунд...")
                time.sleep(retry_delay)
                
                # Создаем новый экземпляр бота
                try:
                    self.bot.stop_polling()
                    self.bot = telebot.TeleBot(self.config.telegram_bot_token)
                    self.register_handlers()
                    logging.info("Бот переинициализирован")
                except Exception as reinit_error:
                    logging.error(f"Ошибка при переинициализации бота: {reinit_error}")
                    time.sleep(5)

    def register_handlers(self):
        @self.bot.message_handler(content_types=['voice'])
        def handle_voice(message):
            if self.config.debug_mode and self.config.debug_chat_id and message.chat.id != self.config.debug_chat_id:
                self.connection_manager.execute_with_retry(
                    self.bot.reply_to, message, 'В данный момент бот находится на обслуживании, приносим извинения'
                )
                return
            self.process_voice_message(message)

        @self.bot.message_handler(content_types=['video_note'])
        def handle_video_note(message):
            if self.config.debug_mode and self.config.debug_chat_id and message.chat.id != self.config.debug_chat_id:
                self.connection_manager.execute_with_retry(
                    self.bot.reply_to, message, 'В данный момент бот находится на обслуживании, приносим извинения'
                )
                return
            self.process_video_note_message(message)

        @self.bot.message_handler(commands=['check'])
        def check_queue(message):
            if self.config.debug_mode and self.config.debug_chat_id and message.chat.id != self.config.debug_chat_id:
                self.connection_manager.execute_with_retry(
                    self.bot.reply_to, message, 'В данный момент бот находится на обслуживании, приносим извинения'
                )
                return
            chat_data = self.chat_manager.display_chats()
            self.connection_manager.execute_with_retry(
                self.bot.reply_to, message, chat_data
            )

        @self.bot.message_handler(commands=['everyone'])
        def ping_all(message):
            if self.config.debug_mode and self.config.debug_chat_id and message.chat.id != self.config.debug_chat_id:
                self.connection_manager.execute_with_retry(
                    self.bot.reply_to, message, 'В данный момент бот находится на обслуживании, приносим извинения'
                )
                return
            self.process_ping_all(message)

        @self.bot.message_handler(commands=['asr_status'])
        def asr_status(message):
            if self.config.debug_mode and self.config.debug_chat_id and message.chat.id != self.config.debug_chat_id:
                self.connection_manager.execute_with_retry(
                    self.bot.reply_to, message, 'В данный момент бот находится на обслуживании, приносим извинения'
                )
                return
            self.process_asr_status(message)

    def process_voice_message(self, message):
        try:
            sent_message = self.connection_manager.execute_with_retry(
                self.bot.reply_to, message, 'В очереди...'
            )
            if not sent_message:
                logging.error("Не удалось отправить сообщение в очередь")
                return
                
            file_info = self.connection_manager.execute_with_retry(
                self.bot.get_file, message.voice.file_id
            )
            
            if not file_info or not file_info.file_path:
                logging.error("Не удалось получить информацию о файле")
                return
                
            downloaded_file = self.connection_manager.execute_with_retry(
                self.bot.download_file, file_info.file_path
            )
            
            if not downloaded_file:
                logging.error("Не удалось скачать файл")
                return

            file_name = os.path.join(
                self.config.voice_folder, f"voice_{message.from_user.id}_{message.message_id}.ogg")

            with open(file_name, 'wb') as voice_file:
                voice_file.write(downloaded_file)

            self.chat_manager.add_chat(message.chat.id, sent_message.message_id, file_name)
        except Exception as e:
            logging.error(f'Error processing voice message: {e}')

    def process_video_note_message(self, message):
        try:
            sent_message = self.connection_manager.execute_with_retry(
                self.bot.reply_to, message, 'В очереди...'
            )
            if not sent_message:
                logging.error("Не удалось отправить сообщение в очередь")
                return
                
            file_info = self.connection_manager.execute_with_retry(
                self.bot.get_file, message.video_note.file_id
            )
            
            if not file_info or not file_info.file_path:
                logging.error("Не удалось получить информацию о файле")
                return
                
            downloaded_file = self.connection_manager.execute_with_retry(
                self.bot.download_file, file_info.file_path
            )
            
            if not downloaded_file:
                logging.error("Не удалось скачать файл")
                return

            file_name_video = os.path.join(
                self.config.video_note_folder, f"video_{message.from_user.id}_{message.message_id}.mp4")
            file_name_audio = os.path.join(
                self.config.video_note_folder, f"video_{message.from_user.id}_{message.message_id}.ogg")

            with open(file_name_video, 'wb') as video_file:
                video_file.write(downloaded_file)

            audio = AudioSegment.from_file(file_name_video, format="mp4")
            audio.export(file_name_audio, format="mp3")

            os.remove(file_name_video)
            
            self.chat_manager.add_chat(message.chat.id, sent_message.message_id, file_name_audio)
        except Exception as e:
            logging.error(f'Error processing video note: {e}')

    def voice_handler(self):
        """Обработчик очереди голосовых сообщений"""
        while True:
            try:
                if not self.chat_manager.is_empty():
                    first_chat = self.chat_manager.get_first_chat()
                    if first_chat:
                        self._process_transcription(first_chat)
                    else:
                        time.sleep(1)
                else:
                    time.sleep(1)
            except Exception as e:
                logging.error(f'Critical error in voice_handler: {e}')
                time.sleep(5)  # Больше времени при критической ошибке

    def _process_transcription(self, chat_data: ChatData) -> None:
        """Обработка транскрипции для одного чата"""
        file_path = Path(chat_data.path)
        
        try:
            self.connection_manager.execute_with_retry(
                self.bot.edit_message_text,
                chat_id=chat_data.chat_id,
                message_id=chat_data.message_id,
                text="Распознавание...",
                parse_mode='HTML'
            )

            start_time = time.time()
            transcription = self.asr_provider.transcribe(file_path)
            duration = time.time() - start_time

            if not transcription or not str(transcription).strip():
                self.connection_manager.execute_with_retry(
                    self.bot.edit_message_text,
                    chat_id=chat_data.chat_id,
                    message_id=chat_data.message_id,
                    text="Не удалось распознать речь в аудиозаписи",
                    parse_mode='HTML'
                )
                return

            self._send_transcription_messages(chat_data, str(transcription), duration)

        except Exception as e:
            logging.error(f'Error during transcription: {e}')
            with contextlib.suppress(Exception):
                self.connection_manager.execute_with_retry(
                    self.bot.edit_message_text,
                    chat_id=chat_data.chat_id,
                    message_id=chat_data.message_id,
                    text="Ошибка во время распознавания",
                    parse_mode='HTML'
                )
        finally:
            if file_path.exists():
                file_path.unlink()
            self.chat_manager.remove_chat()

    def _send_transcription_messages(self, chat_data: ChatData, transcription: str, duration: float) -> None:
        """Отправка сообщений с транскрипцией"""
        messages = self.split_text(transcription, self.config.max_message_length)
        
        if not messages:
            return
            
        # Отправка первого сообщения
        first_message_text = (
            f"Распознанный текст:\n\n"
            f"<blockquote expandable>{messages[0]}</blockquote>\n\n"
            f"Время распознавания: {duration:.2f} секунд"
        )
        
        self.connection_manager.execute_with_retry(
            self.bot.edit_message_text,
            chat_id=chat_data.chat_id,
            message_id=chat_data.message_id,
            text=first_message_text,
            parse_mode='HTML'
        )
        
        # Отправка остальных сообщений
        if len(messages) > 1:
            previous_message_id = chat_data.message_id
            for msg in messages[1:]:
                try:
                    time.sleep(2)  # Соблюдение лимитов API
                    sent_message = self.connection_manager.execute_with_retry(
                        self.bot.send_message,
                        chat_id=chat_data.chat_id,
                        text=f"<blockquote expandable>{msg}</blockquote>",
                        parse_mode='HTML',
                        reply_to_message_id=previous_message_id
                    )
                    if sent_message:
                        previous_message_id = sent_message.message_id
                except Exception as e:
                    logging.error(f'Error sending continuation message: {e}')
                    break

    def split_text(self, text: str, max_length: int) -> List[str]:
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

    def queue_manager(self):
        """Менеджер очереди с обновлением статуса сообщений"""
        previous_queue_states = {}
        while True:
            try:
                current_queue_length = self.chat_manager.count_chats()
                # Получаем копию данных для безопасной итерации
                with self.chat_manager._lock:
                    chat_data_copy = self.chat_manager._chat_data.copy()
                
                for index, chat in enumerate(chat_data_copy):
                    chat_id = chat.chat_id
                    message_id = chat.message_id
                    # Обновляем сообщение только если статус изменился
                    if (chat_id, message_id) not in previous_queue_states or previous_queue_states[
                        (chat_id, message_id)] != index:
                        try:
                            if index > 0:
                                self.connection_manager.execute_with_retry(
                                    self.bot.edit_message_text,
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    text="В очереди",
                                )
                            previous_queue_states[(chat_id, message_id)] = index
                        except Exception as e:
                            logging.error(f'Failed to edit message: {e}')
                time.sleep(1)
            except Exception as e:
                logging.error(f'Error in queue manager: {e}')
                time.sleep(1)

    def process_ping_all(self, message):
        chat_id = message.chat.id
        all_members = []

        try:
            # Получаем информацию о чате
            chat = self.connection_manager.execute_with_retry(
                self.bot.get_chat, chat_id
            )

            # Проверяем, является ли бот администратором
            bot_member = self.connection_manager.execute_with_retry(
                self.bot.get_chat_member, chat_id, self.bot.get_me().id
            )
            
            if not bot_member or bot_member.status not in ['administrator', 'creator']:
                self.connection_manager.execute_with_retry(
                    self.bot.send_message, chat_id, "Бот должен быть администратором, чтобы упоминать участников."
                )
                return

            # Получаем всех участников чата (может быть ограничено)
            members = self.connection_manager.execute_with_retry(
                self.bot.get_chat_administrators, chat_id
            )
            
            if not members:
                self.connection_manager.execute_with_retry(
                    self.bot.send_message, chat_id, "Не удалось получить список участников."
                )
                return

            # Формируем упоминания участников
            for member in members:
                user = member.user
                if user.is_bot:
                    continue
                if user.username:
                    mention = f'@{user.username}'
                else:
                    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
                all_members.append(mention)

            # Отправляем сообщение, если есть упоминания
            ping_message = ' '.join(all_members)

            if ping_message:
                self.connection_manager.execute_with_retry(
                    self.bot.send_message, chat_id, ping_message, parse_mode='HTML'
                )
            else:
                self.connection_manager.execute_with_retry(
                    self.bot.send_message, chat_id, "Не удалось получить список участников для упоминания."
                )
        except Exception as e:
            logging.error(f'Error in ping_all: {e}')
            self.connection_manager.execute_with_retry(
                self.bot.send_message, chat_id, f"Не удалось получить список участников: {e}"
            )

    def process_asr_status(self, message):
        """Обработка команды проверки статуса ASR"""
        try:
            # Получаем информацию о провайдере
            asr_info = self.asr_provider.get_model_info()
            
            # Формируем сообщение
            status_message = f"🤖 <b>Статус ASR</b>\n\n"
            status_message += f"📡 <b>Провайдер:</b> {asr_info.get('provider', 'Неизвестно')}\n"
            status_message += f"🧠 <b>Модель:</b> {asr_info.get('model_name', 'Неизвестно')}\n"
            status_message += f"💻 <b>Устройство:</b> {asr_info.get('device', 'Неизвестно')}\n"
            status_message += f"🔄 <b>Статус:</b> {'✅ Загружена' if asr_info.get('is_loaded', False) else '❌ Не загружена'}\n"
            
            if asr_info.get('language'):
                status_message += f"🌐 <b>Язык:</b> {asr_info['language']}\n"
            
            # Поддерживаемые форматы
            formats = asr_info.get('supported_formats', [])
            if formats:
                status_message += f"📁 <b>Форматы:</b> {', '.join(formats)}\n"
            
            # Дополнительные возможности
            if asr_info.get('supports_batch'):
                status_message += f"⚡ <b>Пакетная обработка:</b> ✅\n"
            
            if 'cuda_available' in asr_info:
                cuda_status = "✅ Доступна" if asr_info['cuda_available'] else "❌ Недоступна"
                status_message += f"🎮 <b>CUDA:</b> {cuda_status}\n"
            
            # Статистика очереди
            queue_count = self.chat_manager.count_chats()
            status_message += f"\n📊 <b>Очередь:</b> {queue_count} задач"
            
            self.connection_manager.execute_with_retry(
                self.bot.reply_to, message, status_message, parse_mode='HTML'
            )
            
        except Exception as e:
            logging.error(f"Ошибка при получении статуса ASR: {e}")
            self.connection_manager.execute_with_retry(
                self.bot.reply_to, message, "Ошибка при получении статуса ASR"
            )


if __name__ == "__main__":
    # Загружаем конфигурацию для получения уровня логирования
    config = Config.from_env()
    setup_logging('bot.log', config.log_level)
    
    voice_bot = VoiceBot(config)
    voice_bot.start()
