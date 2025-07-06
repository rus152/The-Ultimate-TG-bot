"""
Основной класс бота для обработки голосовых сообщений
"""

import os
import time
import logging
import contextlib
from threading import Thread
from typing import Optional, List
from pathlib import Path

import telebot
from pydub import AudioSegment

from config import Config
from models import ChatData
from chat_manager import ChatManager
from connection_manager import ConnectionManager
from utils import split_text
from asr import ASRFactory


class VoiceBot:
    """Главный класс бота для обработки голосовых сообщений"""
    
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
        """Настройка папок для файлов"""
        os.makedirs(self.config.voice_folder, exist_ok=True)
        logging.info('Voice messages folder is ready')

        os.makedirs(self.config.video_note_folder, exist_ok=True)
        logging.info('Video notes folder is ready')

    def start(self):
        """Запуск бота с автоматическим переподключением"""
        logging.info('Bot started')
        
        # Запуск рабочих потоков
        threading_list = [
            Thread(target=self.voice_handler, daemon=True),
            # Thread(target=self.queue_manager, daemon=True)
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
        """Регистрация обработчиков сообщений"""
        @self.bot.message_handler(content_types=['voice'])
        def handle_voice(message):
            if self._is_debug_mode_restricted(message):
                return
            self.process_voice_message(message)

        @self.bot.message_handler(content_types=['video_note'])
        def handle_video_note(message):
            if self._is_debug_mode_restricted(message):
                return
            self.process_video_note_message(message)

        @self.bot.message_handler(commands=['check'])
        def check_queue(message):
            if self._is_debug_mode_restricted(message):
                return
            chat_data = self.chat_manager.display_chats()
            self.connection_manager.execute_with_retry(
                self.bot.reply_to, message, chat_data
            )

        @self.bot.message_handler(commands=['everyone'])
        def ping_all(message):
            if self._is_debug_mode_restricted(message):
                return
            self.process_ping_all(message)

        @self.bot.message_handler(commands=['asr_status'])
        def asr_status(message):
            if self._is_debug_mode_restricted(message):
                return
            self.process_asr_status(message)

    def _is_debug_mode_restricted(self, message) -> bool:
        """Проверяет, ограничен ли доступ в режиме отладки"""
        if self.config.debug_mode and self.config.debug_chat_id and message.chat.id != self.config.debug_chat_id:
            self.connection_manager.execute_with_retry(
                self.bot.reply_to, message, 'В данный момент бот находится на обслуживании, приносим извинения'
            )
            return True
        return False

    def process_voice_message(self, message):
        """Обработка голосового сообщения"""
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
        """Обработка видео-заметки"""
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
        messages = split_text(transcription, self.config.max_message_length)
        
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
        """Обработка команды упоминания всех участников"""
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
