import speech_recognition as sr
from pydub import AudioSegment

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

if __name__ == "__main__":
    audio_file_path = "Hi.wav" # Укажите путь к вашему аудио файлу
    result_text = recognize_speech_from_audio(audio_file_path, ["ru-RU", "en-US"])
    print(result_text)
