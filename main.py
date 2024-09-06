import telebot
import os
from dotenv import load_dotenv
import logging
import whisper
from threading import Thread

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
        logging.info('Вывод количества чатов')
        return f"Количество чатов: {len(self.chat_data)}"

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


    logging.info('Начало логирования')

    chat_manager = ChatManager()

    load_dotenv()
    API_TOKEN = os.getenv('TOKEN')
    logging.info('Токен получен')

    VOICE_FOLDER = 'voice_messages'
    VIDEO_NOTE = 'video_notes'

    if not os.path.exists(VOICE_FOLDER):
        os.makedirs(VOICE_FOLDER)
        logging.info('Папка для видео сообщений создана')
    if not os.path.exists(VIDEO_NOTE):
        os.makedirs(VIDEO_NOTE)
        logging.info('Папка для голосовых сообщений создана')

    Thread(target=Voice_Handler, daemon=True).start()

    logging.info('Инициализация закончена')


def queue():
    pass

def Voice_Handler():
    while True:
        if chat_manager.checker() == "Пусто":
            pass
        if chat_manager.checker() == "Не пусто":
            logging.info('Запуск расшифровки')
            # Load the model
            model = whisper.load_model("small")

            # Open and read the audio file correctly
            audio_file = chat_manager.first_path()

            # Load audio using whisper's built-in function
            audio = whisper.load_audio(audio_file)

            # Transcribe the audio
            result = model.transcribe(audio)

            bot.edit_message_text(chat_id=chat_manager.first_chat_id(), message_id=chat_manager.first_message_id(),
                                  text=f"Распознанный текст:\n\n<i>{result['text']}</i>", parse_mode='HTML')

            chat_manager.remove_chat()




def main():
    global bot
    logging.info('Запуск бота')
    bot = telebot.TeleBot(API_TOKEN)

    @bot.message_handler(content_types=['voice'])
    def handle_voice(message):

        message_id = bot.reply_to(message, 'Распознавание')

        logging.info("Получаем файл голосового сообщения")

        file_info = bot.get_file(message.voice.file_id)

        logging.info("Загружаем голосовое сообщение")

        downloaded_file = bot.download_file(file_info.file_path)

        logging.info("Определяем имя файла для сохранения")

        file_name = f"{VOICE_FOLDER}/voice_{message.from_user.id}_{message.message_id}.ogg"

        logging.info('Сохраняем файл на диск')

        with open(file_name, 'wb') as voice_file:
            voice_file.write(downloaded_file)

        chat_manager.add_chat(message.chat.id, message_id.id, file_name)

    @bot.message_handler(content_types=['video_note'])
    def handle_video_note(message):
        pass

    @bot.message_handler(commands=['add'])
    def data_to_massive(message):
        bot.reply_to(message, chat_manager.add_chat(message.chat.id, "empty", "test"))

    @bot.message_handler(commands=['check'])
    def check_massive(message):
        print(chat_manager.display_chats())
        bot.reply_to(message, chat_manager.display_chats())



    bot.polling()



if __name__ == "__main__":
    setup_logging('UTGB.log')
    init()
    main()
