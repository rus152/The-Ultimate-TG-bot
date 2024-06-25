import telebot
import os
import speech_recognition as sr
from pydub import AudioSegment

# Чтение токена из файла
with open('token.txt') as f:
    API_TOKEN = f.read().strip()

bot = telebot.TeleBot(API_TOKEN)

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

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    # Скачивание голосового сообщения
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохранение файла
    file_name = f"voice_messages/{message.voice.file_id}.ogg"
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    recognized_text = recognize_speech_from_audio(file_name)
    bot.send_message(message.chat.id, recognized_text)

@bot.message_handler(content_types=['video_note'])
def handle_video_note(message):
    # Скачивание видео кружка
    file_info = bot.get_file(message.video_note.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Сохранение файла
    file_name = f"video_notes/{message.video_note.file_id}.mp4"
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    recognized_text = recognize_speech_from_audio(file_name)
    bot.send_message(message.chat.id, recognized_text)

bot.polling()
