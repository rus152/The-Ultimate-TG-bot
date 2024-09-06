import telebot
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from threading import Thread

class ChatManager:
    def __init__(self):
        logger.info(f'{datetime.now().strftime("%H:%M:%S")} Инициализируем пустой массив для хранения чатов')
        self.chat_data = []

    def add_chat(self, chat, message, path):
        logger.info(f'{datetime.now().strftime("%H:%M:%S")} Добавляем новый элемент в массив')
        self.chat_data.append({
            "chat_id": chat,
            "message_id": message,
            "path": path
        })
        return f"Добавлено: {chat}, {message}, {path}"

    def remove_chat(self, chat):
        logger.info(f'{datetime.now().strftime("%H:%M:%S")} Удаляем элемент по имени чата')
        self.chat_data = [item for item in self.chat_data if item["chat_id"] != chat]
        return f"Удалено все сообщения из чата: {chat}"

    def display_chats(self):
        logger.info(f'{datetime.now().strftime("%H:%M:%S")} Вывод всех данных в массиве')
        if not self.chat_data:
            return "Чаты отсутствуют"
        else:
            for item in self.chat_data:
                return f"Чат: {item['chat_id']}, Сообщение: {item['message_id']}, Путь: {item['path']}"

    def get_first_chat(self):
        logger.info(f'{datetime.now().strftime("%H:%M:%S")} Вывод первого чата в массиве')
        if self.chat_data:
            first_chat = self.chat_data[0]
            return f"Первый чат: {first_chat['chat_id']}, Сообщение: {first_chat['message_id']}, Путь: {first_chat['path']}"
        else:
            return "Массив пуст"

    def count_chats(self):
        logger.info(f'{datetime.now().strftime("%H:%M:%S")} Вывод количества чатов')
        return f"Количество чатов: {len(self.chat_data)}"

def init():
    global VOICE_FOLDER
    global VIDEO_NOTE
    global API_TOKEN
    global logger
    global chat_manager

    logger = logging.getLogger(__name__)

    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    logger.info(f'{datetime.now().strftime("%H:%M:%S")} Начало логирования')

    chat_manager = ChatManager()

    load_dotenv()
    API_TOKEN = os.getenv('TOKEN')
    logger.info(f'{datetime.now().strftime("%H:%M:%S")} Токен получен')

    VOICE_FOLDER = 'voice_messages'
    VIDEO_NOTE = 'video_notes'

    if not os.path.exists(VOICE_FOLDER):
        os.makedirs(VOICE_FOLDER)
        logger.info(f'{datetime.now().strftime("%H:%M:%S")} Папка для видео сообщений создана')
    if not os.path.exists(VIDEO_NOTE):
        os.makedirs(VIDEO_NOTE)
        logger.info('Папка для голосовых сообщений создана')
    logger.info(f'{datetime.now().strftime("%H:%M:%S")} Инициализация закончена')

def main():
    logger.info(f'{datetime.now().strftime("%H:%M:%S")} Запуск бота')
    bot = telebot.TeleBot(API_TOKEN)

    @bot.message_handler(content_types=['voice'])
    def handle_voice(message):
        logger.info(f'{datetime.now().strftime("%H:%M:%S")} Получено голосовое сообщение')
        pass

    @bot.message_handler(commands=['add'])
    def data_to_massive(message):
        bot.reply_to(message, chat_manager.add_chat(message.chat.id, "empty", "test"))

    @bot.message_handler(commands=['check'])
    def check_massive(message):
        chat_manager.display_chats()
        bot.reply_to(message, chat_manager.display_chats())



    bot.polling()



if __name__ == "__main__":
    init()
    main()
