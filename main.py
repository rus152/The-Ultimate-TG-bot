"""
Точка входа приложения
"""

from config import Config
from utils import setup_logging
from voice_bot import VoiceBot

def main():
    """Основная функция запуска бота"""
    try:
        # Загружаем конфигурацию
        config = Config.from_env()
        
        # Настраиваем логирование
        setup_logging('bot.log', config.log_level)
        
        # Создаем и запускаем бота
        voice_bot = VoiceBot(config)
        voice_bot.start()
        
    except Exception as e:
        print(f"Критическая ошибка при запуске бота: {e}")
        exit(1)


if __name__ == "__main__":
    main()
