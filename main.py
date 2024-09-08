import telebot
import os
from dotenv import load_dotenv
import logging
import whisper
from threading import Thread
import time
from pydub import AudioSegment


class ChatManager:
    def __init__(self):
        logging.info('Инициализируем пустой массив для хранения чатов')
        self.chat_data = []

    def add_chat(self, chat, message, path):
        logging.info('Добавляем новый элемент в массив')
        self.chat_data.append({
            "chat_id": chat,
            "message_id": message,
            "path": path
        })
        return f"Добавлено: {chat}, {message}, {path}"

    def remove_chat(self):
        logging.info('Удаляем первую строку')
        removed_chat = self.chat_data.pop(0)
        return

    def display_chats(self):
        logging.info('Вывод всех данных в массиве')
        if not self.chat_data:
            return "Чаты отсутствуют"
        else:
            for item in self.chat_data:
                return f"Чат: {item['chat_id']}, Сообщение: {item['message_id']}, Путь: {item['path']}"

    def get_first_chat(self):
        logging.info('Вывод первого чата в массиве')
        if self.chat_data:
            first_chat = self.chat_data[0]
            return f"Первый чат: {first_chat['chat_id']}, Сообщение: {first_chat['message_id']}, Путь: {first_chat['path']}"
        else:
            return "Массив пуст"

    def count_chats(self):
        return f"{len(self.chat_data)}"

    def first_path(self):
        logging.info('Запрос пути первого чата в массиве')
        first_chat = self.chat_data[0]
        return f"{first_chat['path']}"

    def first_chat_id(self):
        logging.info('Запрос chat_id первого чата в массиве')
        first_chat = self.chat_data[0]
        return f"{first_chat['chat_id']}"

    def first_message_id(self):
        logging.info('Запрос message_id первого чата в массиве')
        first_chat = self.chat_data[0]
        return f"{first_chat['message_id']}"

    def i_chat_id(self, i):
        try:
            first_chat = self.chat_data[i]
            return f"{first_chat['chat_id']}"
        except IndexError:
            pass


    def i_message_id(self, i):
        try:
            first_chat = self.chat_data[i]
            return f"{first_chat['message_id']}"
        except IndexError:
            pass

    def checker(self):
        if not self.chat_data:
            return "Пусто"
        else:
            return "Не пусто"


def setup_logging(filename: str) -> None:
    """
    Настраивает логирование.

    :param filename: Имя файла для записи логов
    :return: None
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Устанавливаем уровень логирования

    # Формат сообщения лога теперь включает идентификатор потока
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Обработчик для записи логов в файл
    file_handler = logging.FileHandler(filename, 'a')
    file_handler.setFormatter(formatter)

    # Обработчик для вывода логов в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def init():
    global VOICE_FOLDER
    global VIDEO_NOTE
    global API_TOKEN
    global chat_manager
    global wait_number


    logging.info('Начало логирования')

    chat_manager = ChatManager()

    load_dotenv()
    API_TOKEN = os.getenv('TOKEN')
    logging.info('Токен получен')

    VOICE_FOLDER = 'voice_messages'
    VIDEO_NOTE = 'video_notes'

    if not os.path.exists(VOICE_FOLDER):
        os.makedirs(VOICE_FOLDER)
        logging.info('Папка для голосовых сообщений создана')
    if not os.path.exists(VIDEO_NOTE):
        os.makedirs(VIDEO_NOTE)
        logging.info('Папка для видео сообщений создана')

    thr1 = Thread(target=Voice_Handler, daemon=True)
    thr2 = Thread(target=queue, daemon=True)

    thr1.start()
    thr2.start()

    logging.info('Инициализация закончена')


def queue():
    wait_number = 0
    while True:
        number_of_queue = int(chat_manager.count_chats())
        if wait_number != number_of_queue:
            for i in range(int(chat_manager.count_chats())):
                if i > 0:
                    try:
                        bot.edit_message_text(
                            chat_id=chat_manager.i_chat_id(i),
                            message_id=chat_manager.i_message_id(i),
                            text=f"Перед вами в очереди на обработку: {i}",
                        )
                        logging.warning('Изменено сообщение об очереди')
                    except telebot.apihelper.ApiTelegramException as e:
                        pass
                else:
                    pass
            wait_number = number_of_queue
            logging.info("Ожидаемое число изменено на " + str(wait_number))
        elif wait_number == int(chat_manager.count_chats()) and wait_number == 0:
            pass
        time.sleep(1)


def Voice_Handler():
    while True:
        if chat_manager.checker() == "Пусто":
            pass
        if chat_manager.checker() == "Не пусто":
            logging.info('Запуск расшифровки')
            bot.edit_message_text(chat_id=chat_manager.first_chat_id(), message_id=chat_manager.first_message_id(),
                                  text=f"Распознавание...", parse_mode='HTML')

            model = whisper.load_model("medium")

            # Open and read the audio file correctly
            audio_file = chat_manager.first_path()

            # Load audio using whisper's built-in function
            audio = whisper.load_audio(audio_file)

            # Transcribe the audio
            result = model.transcribe(audio)

            bot.edit_message_text(chat_id=chat_manager.first_chat_id(), message_id=chat_manager.first_message_id(),
                                  text=f"Распознанный текст:\n\n<i>{result['text']}</i>", parse_mode='HTML')

            os.remove(chat_manager.first_path())

            chat_manager.remove_chat()


def main():
    global bot
    logging.info('Запуск бота')
    bot = telebot.TeleBot(API_TOKEN)

    @bot.message_handler(content_types=['voice'])
    def handle_voice(message):

        message_id = bot.reply_to(message, 'Обработка...')

        file_info = bot.get_file(message.voice.file_id)

        downloaded_file = bot.download_file(file_info.file_path)

        file_name = f"{VOICE_FOLDER}/voice_{message.from_user.id}_{message.message_id}.ogg"

        with open(file_name, 'wb') as voice_file:
            voice_file.write(downloaded_file)

        chat_manager.add_chat(message.chat.id, message_id.id, file_name)

    @bot.message_handler(content_types=['video_note'])
    def handle_video_note(message):

        message_id = bot.reply_to(message, 'Обработка...')

        file_info = bot.get_file(message.video_note.file_id)

        downloaded_file = bot.download_file(file_info.file_path)

        file_name_video = f"{VIDEO_NOTE}/video_{message.from_user.id}_{message.message_id}.mp4"
        file_name_audio = f"{VIDEO_NOTE}/video_{message.from_user.id}_{message.message_id}.ogg"

        with open(file_name_video, 'wb') as video_file:
            video_file.write(downloaded_file)

        audio = AudioSegment.from_file(file_name_video, format="mp4")

        audio.export(file_name_audio, format="ogg")

        os.remove(file_name_video)

        chat_manager.add_chat(message.chat.id, message_id.id, file_name_audio)


    @bot.message_handler(commands=['check'])
    def check_massive(message):
        print(chat_manager.display_chats())
        bot.reply_to(message, chat_manager.display_chats())


    @bot.message_handler(commands=['everyone'])
    def ping_all(message):
        chat_id = message.chat.id
        all_members = []

        try:
            # Получаем информацию о чате
            chat = bot.get_chat(chat_id)

            # Проверяем, является ли бот администратором
            is_bot_admin = any(admin.user.id == bot.get_me().id for admin in bot.get_chat_administrators(chat_id))
            if not is_bot_admin:
                bot.send_message(chat_id, "Бот должен быть администратором, чтобы упоминать всех участников.")
                return

            # Получаем всех администраторов чата
            administrators = bot.get_chat_administrators(chat_id)

            # Формируем упоминания администраторов
            for admin in administrators:
                user = admin.user
                if user.username:
                    mention = f'@{user.username}'
                else:
                    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
                all_members.append(mention)

            # Отправляем сообщение, если есть упоминания
            ping_message = ' '.join(all_members)

            if ping_message:
                bot.send_message(chat_id, ping_message, parse_mode='HTML')
            else:
                bot.send_message(chat_id, "Не удалось получить список участников для упоминания.")
        except Exception as e:
            bot.send_message(chat_id, f"Не удалось получить список участников: {e}")

    bot.polling()

if __name__ == "__main__":
    setup_logging('bot.log')
    init()
    main()
