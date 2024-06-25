import telebot
import os
import speech_recognition as sr
from pydub import AudioSegment
from queue import Queue
from threading import Thread

# Чтение токена из файла
with open('token.txt') as f:
    API_TOKEN = f.read().strip()

bot = telebot.TeleBot(API_TOKEN, parse_mode='MARKDOWN')
processing_queue = Queue()

# Создание папок для сохранения файлов, если они не существуют
if not os.path.exists('voice_messages'):
    os.makedirs('voice_messages')

if not os.path.exists('video_notes'):
    os.makedirs('video_notes')


def convert_audio_to_wav(file_path):
    audio = AudioSegment.from_file(file_path)
    wav_path = file_path.rsplit('.', 1)[0] + '.wav'
    audio.export(wav_path, format="wav")
    return wav_path


def recognize_speech_from_audio(file_path, languages=["ru-RU", "en-US"]):
    recognizer = sr.Recognizer()

    # Конвертируем аудио файл в формат WAV
    wav_path = convert_audio_to_wav(file_path)

    try:
        # Открываем аудио файл с помощью SpeechRecognition
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)  # Используем метод record у recognizer
            try:
                # Используем Google Web Speech API для распознавания речи
                text = recognizer.recognize_google(audio_data, language=",".join(languages))
                return text
            except sr.UnknownValueError:
                return "Google Web Speech API не смогла распознать аудио"
            except sr.RequestError as e:
                return f"Could not request results from Google Web Speech API; {e}"
    finally:
        # Удаляем временный WAV файл
        os.remove(wav_path)


def process_queue():
    while True:
        chat_id, message_id, file_name = processing_queue.get()

        # Распознавание речи
        recognized_text = recognize_speech_from_audio(file_name)

        # Обновление сообщения
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f'Распознанный текст:\n\n<i>{recognized_text}</i>', parse_mode='HTML')

        # Удаление оригинального файла
        os.remove(file_name)

        processing_queue.task_done()


Thread(target=process_queue, daemon=True).start()


def handle_audio_message(message, file_extension, folder):
    # Скачивание файла
    file_info = bot.get_file(message.voice.file_id if file_extension == 'ogg' else message.video_note.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохранение файла
    file_name = f"{folder}/{message.voice.file_id if file_extension == 'ogg' else message.video_note.file_id}.{file_extension}"
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    queue_position = processing_queue.qsize()

    if queue_position == 0:
        status_message = bot.reply_to(message, "Распознавание")
    else:
        status_message = bot.reply_to(message, f"Очередь ({queue_position + 1})")

    processing_queue.put((message.chat.id, status_message.message_id, file_name))


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    handle_audio_message(message, 'ogg', 'voice_messages')


@bot.message_handler(content_types=['video_note'])
def handle_video_note(message):
    handle_audio_message(message, 'mp4', 'video_notes')


bot.polling()
