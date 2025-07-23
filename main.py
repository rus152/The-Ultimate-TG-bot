# main.py

import os
import logging
import time
from threading import Thread

import telebot
from telebot.formatting import hcite
from pydub import AudioSegment
from faster_whisper import WhisperModel
from torch import cuda


def setup_logging(filename: str) -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(filename, 'a')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


class ChatManager:
    def __init__(self):
        logging.info('Initializing chat manager')
        self.chat_data = []

    def add_chat(self, chat_id, message_id, path):
        logging.info('Adding new chat to queue')
        self.chat_data.append({
            "chat_id": chat_id,
            "message_id": message_id,
            "path": path
        })

    def remove_chat(self):
        logging.info('Removing first chat from queue')
        if self.chat_data:
            self.chat_data.pop(0)

    def display_chats(self):
        logging.info('Displaying all chats in queue')
        if not self.chat_data:
            return "No chats in queue"
        else:
            result = ""
            for item in self.chat_data:
                result += f"Chat: {item['chat_id']}, Message: {item['message_id']}, Path: {item['path']}\n"
            return result.strip()

    def get_first_chat(self):
        logging.info('Getting first chat in queue')
        if self.chat_data:
            return self.chat_data[0]
        else:
            return None

    def count_chats(self):
        return len(self.chat_data)

    def is_empty(self):
        return len(self.chat_data) == 0


class VoiceBot:
    def __init__(self):
        self.setup()

        self.api_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.api_token:
            logging.error('API Token not found. Please set it in the environment variables.')
            exit(1)
        self.bot = telebot.TeleBot(self.api_token)
        logging.info('API Token obtained')

        self.debug_chat_id = os.getenv('DEBUG_CHAT_ID')
        if self.debug_chat_id:
            try:
                self.debug_chat_id = int(self.debug_chat_id)
                logging.info(f'Debug chat ID set to: {self.debug_chat_id}')
            except ValueError:
                logging.error('Invalid DEBUG_CHAT_ID. It should be a numeric value.')
                self.debug_chat_id = None
        
        self.debug_mode = os.getenv('DEBUG_MODE', 'False')
        self.debug_mode = self.debug_mode.lower() == 'true'

        self.chat_manager = ChatManager()

        # Загрузка модели с обработкой исключений
        try:
            logging.info('Loading Faster-Whisper model...')

            # Определение cuda
            device = "cuda" if cuda.is_available() else "cpu"
            compute_type = "int8" # Устанавливаем тип вычислений в int8
            model_size = "turbo"

            # Инициализация модели Faster-Whisper
            # num_workers=1 рекомендуется для стабильности в многопоточных приложениях,
            # download_root позволяет указать путь для кэширования моделей.
            self.model = WhisperModel(
                model_size_or_path=model_size,
                device=device,
                compute_type=compute_type,
                num_workers=1, # Важно для стабильности с потоками
                download_root="./model_cache" # Опционально, папка для кэша моделей внутри контейнера
            )
            logging.info('Faster-Whisper Model loaded')
        except Exception as e:
            logging.error(f'Error loading Faster-Whisper model: {e}')
            exit(1)

    def setup(self):
        self.voice_folder = 'voice_messages'
        self.video_note_folder = 'video_notes'

        os.makedirs(self.voice_folder, exist_ok=True)
        logging.info('Voice messages folder is ready')

        os.makedirs(self.video_note_folder, exist_ok=True)
        logging.info('Video notes folder is ready')

    def start(self):
        logging.info('Bot started')
        threading_list = [
            Thread(target=self.voice_handler, daemon=True),
            #Thread(target=self.queue_manager, daemon=True)
        ]

        for thread in threading_list:
            thread.start()

        self.register_handlers()
        self.bot.polling()

    def register_handlers(self):
        @self.bot.message_handler(content_types=['voice'])
        def handle_voice(message):
            if self.debug_mode and self.debug_chat_id and message.chat.id != self.debug_chat_id:
                self.bot.reply_to(message, 'В данный момент бот находится на обслуживании, приносим извинения')
                return
            self.process_voice_message(message)

        @self.bot.message_handler(content_types=['video_note'])
        def handle_video_note(message):
            if self.debug_mode and self.debug_chat_id and message.chat.id != self.debug_chat_id:
                self.bot.reply_to(message, 'В данный момент бот находится на обслуживании, приносим извинения')
                return
            self.process_video_note_message(message)

        @self.bot.message_handler(commands=['check'])
        def check_queue(message):
            if self.debug_mode and self.debug_chat_id and message.chat.id != self.debug_chat_id:
                self.bot.reply_to(message, 'В данный момент бот находится на обслуживании, приносим извинения')
                return
            chat_data = self.chat_manager.display_chats()
            self.bot.reply_to(message, chat_data)

        @self.bot.message_handler(commands=['everyone'])
        def ping_all(message):
            if self.debug_mode and self.debug_chat_id and message.chat.id != self.debug_chat_id:
                self.bot.reply_to(message, 'В данный момент бот находится на обслуживании, приносим извинения')
                return
            self.process_ping_all(message)

    def process_voice_message(self, message):
        try:
            sent_message = self.bot.reply_to(message, 'В очереди...')
            file_info = self.bot.get_file(message.voice.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)

            file_name = os.path.join(
                self.voice_folder, f"voice_{message.from_user.id}_{message.message_id}.ogg")

            with open(file_name, 'wb') as voice_file:
                voice_file.write(downloaded_file)

            self.chat_manager.add_chat(message.chat.id, sent_message.message_id, file_name)
        except Exception as e:
            logging.error(f'Error processing voice message: {e}')

    def process_video_note_message(self, message):
        try:
            sent_message = self.bot.reply_to(message, 'В очереди...')
            file_info = self.bot.get_file(message.video_note.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)

            file_name_video = os.path.join(
                self.video_note_folder, f"video_{message.from_user.id}_{message.message_id}.mp4")
            file_name_audio = os.path.join(
                self.video_note_folder, f"video_{message.from_user.id}_{message.message_id}.ogg")

            with open(file_name_video, 'wb') as video_file:
                video_file.write(downloaded_file)

            audio = AudioSegment.from_file(file_name_video, format="mp4")
            audio.export(file_name_audio, format="mp3")

            os.remove(file_name_video)

            self.chat_manager.add_chat(message.chat.id, sent_message.message_id, file_name_audio)
        except Exception as e:
            logging.error(f'Error processing video note: {e}')

    def voice_handler(self):
        while True:
            if not self.chat_manager.is_empty():
                first_chat = self.chat_manager.get_first_chat()
                if first_chat:
                    chat_id = first_chat['chat_id']
                    message_id = first_chat['message_id']
                    path = first_chat['path']
                    try:
                        self.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                   text="Распознавание...", parse_mode='HTML')

                        start_time = time.time()
                        segments, info = self.model.transcribe(
                            path,
                            language='ru',
                            beam_size=5, # Можно настроить для баланса скорости/качества
                            vad_filter=True # Используем встроенный VAD для лучшей обработки пауз
                        )
                        # Собираем весь текст из сегментов
                        transcription = " ".join([segment.text for segment in segments])
                        duration = time.time() - start_time

                        # Разделение текста на части, если он превышает лимит
                        max_length = 3696  # Максимальная длина сообщения
                        messages = self.split_text(transcription, max_length)

                        if messages:
                            # Отправка первого сообщения путем редактирования исходного
                            first_message_text = f"Распознанный текст:\n\n<blockquote expandable>{messages[0]}</blockquote>\n\n" \
                                                 f"Время распознавания: {duration:.2f} секунд"
                            self.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                       text=first_message_text, parse_mode='HTML')

                            # Отправка остальных сообщений с задержкой в 2 секунды
                            previous_message_id = message_id
                            for msg in messages[1:]:
                                time.sleep(2)  # Задержка в 2 секунды
                                sent_message = self.bot.send_message(
                                    chat_id=chat_id,
                                    text=f"<blockquote expandable>{msg}</blockquote>",
                                    parse_mode='HTML',
                                    reply_to_message_id=previous_message_id
                                )
                                previous_message_id = sent_message.message_id

                    except Exception as e:
                        logging.error(f'Error during transcription: {e}')
                        self.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                                   text="Ошибка во время распознавания",
                                                   parse_mode='HTML')
                    finally:
                        os.remove(path)
                        self.chat_manager.remove_chat()
                else:
                    time.sleep(1)
            else:
                time.sleep(1)

    def split_text(self, text, max_length):
        """Разделяет текст на части, не превышающие max_length символов."""
        words = text.split()
        messages = []
        current_message = ""

        for word in words:
            if len(current_message) + len(word) + 1 <= max_length:
                current_message += (" " if current_message else "") + word
            else:
                messages.append(current_message)
                current_message = word

        if current_message:
            messages.append(current_message)

        return messages

    def queue_manager(self):
        previous_queue_states = {}
        while True:
            try:
                current_queue_length = self.chat_manager.count_chats()
                for index, chat in enumerate(self.chat_manager.chat_data):
                    chat_id = chat['chat_id']
                    message_id = chat['message_id']
                    # Only edit the message if the state has changed
                    if (chat_id, message_id) not in previous_queue_states or previous_queue_states[
                        (chat_id, message_id)] != index:
                        try:
                            if index > 0:
                                self.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=message_id,
                                    text="В очереди",
                                )
                            previous_queue_states[(chat_id, message_id)] = index
                        except telebot.apihelper.ApiTelegramException as e:
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
            chat = self.bot.get_chat(chat_id)

            # Проверяем, является ли бот администратором
            bot_member = self.bot.get_chat_member(chat_id, self.bot.get_me().id)
            if bot_member.status not in ['administrator', 'creator']:
                self.bot.send_message(chat_id, "Бот должен быть администратором, чтобы упоминать участников.")
                return

            # Получаем всех участников чата (может быть ограничено)
            members = self.bot.get_chat_administrators(chat_id)

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
                self.bot.send_message(chat_id, ping_message, parse_mode='HTML')
            else:
                self.bot.send_message(chat_id, "Не удалось получить список участников для упоминания.")
        except Exception as e:
            logging.error(f'Error in ping_all: {e}')
            self.bot.send_message(chat_id, f"Не удалось получить список участников: {e}")


if __name__ == "__main__":
    setup_logging('bot.log')
    voice_bot = VoiceBot()
    voice_bot.start()
