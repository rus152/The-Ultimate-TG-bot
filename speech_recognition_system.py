import whisper
from pydub import AudioSegment
import warnings


def convert_audio_to_wav(file_path):
    audio = AudioSegment.from_file(file_path)
    wav_path = file_path.rsplit('.', 1)[0] + '.wav'
    audio.export(wav_path, format="wav")
    return wav_path


def recognize_speech_from_audio(file_path):
    # Подавляем предупреждения
    warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

    # Загружаем модель Whisper
    model = whisper.load_model("base")

    # Распознаем речь с помощью Whisper
    result = model.transcribe(file_path)

    return result["text"]


if __name__ == "__main__":
    audio_file_path = "Oh Hai Mark!.mp3"  # Укажите путь к вашему аудио файлу
    result_text = recognize_speech_from_audio(audio_file_path)
    print("Распознанный текст:")
    print(result_text)
