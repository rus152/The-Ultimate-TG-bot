#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы ASR провайдеров
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

from asr import ASRFactory, ASRProviderType

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_provider(provider_name: str, test_file: str = None):
    """Тестирование провайдера ASR"""
    print(f"\n=== Тестирование провайдера: {provider_name} ===")
    
    try:
        # Создание провайдера
        provider = ASRFactory.create_from_string(provider_name)
        print(f"✅ Провайдер {provider_name} создан успешно")
        
        # Получение информации о провайдере
        info = provider.get_model_info()
        print(f"📡 Провайдер: {info['provider']}")
        print(f"🔄 Статус: {'Загружен' if info['is_loaded'] else 'Не загружен'}")
        print(f"📁 Поддерживаемые форматы: {', '.join(info['supported_formats'])}")
        
        # Загрузка модели
        if not provider.is_model_loaded():
            print("🔄 Загрузка модели...")
            provider.load_model()
            print("✅ Модель загружена успешно")
        
        # Тест транскрипции (если есть тестовый файл)
        if test_file and os.path.exists(test_file):
            print(f"🎵 Тестирование транскрипции файла: {test_file}")
            try:
                transcription = provider.transcribe(test_file)
                print(f"📝 Результат: {transcription}")
            except Exception as e:
                print(f"❌ Ошибка транскрипции: {e}")
        
        # Очистка ресурсов
        provider.cleanup()
        print("🧹 Ресурсы очищены")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании провайдера {provider_name}: {e}")

def test_factory():
    """Тестирование фабрики ASR"""
    print("\n=== Тестирование фабрики ASR ===")
    
    try:
        # Получение доступных провайдеров
        available = ASRFactory.get_available_providers()
        print("🔍 Доступные провайдеры:")
        for name, status in available.items():
            print(f"  - {name}: {status}")
        
        # Тестирование конфигураций по умолчанию
        print("\n📋 Конфигурации по умолчанию:")
        for provider_type in ASRProviderType:
            try:
                config = ASRFactory.get_default_config(provider_type)
                print(f"  - {provider_type.value}: {config}")
            except Exception as e:
                print(f"  - {provider_type.value}: Ошибка - {e}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании фабрики: {e}")

def main():
    """Главная функция"""
    print("🚀 Запуск тестов ASR модуля")
    
    # Тестирование фабрики
    test_factory()
    
    # Тестирование провайдеров
    providers_to_test = ['whisper', 'nemo']
    
    for provider_name in providers_to_test:
        test_provider(provider_name)
    
    # Поиск тестового аудиофайла
    test_files = [
        'test.wav',
        'test.mp3',
        'voice_messages/*.ogg',
        'voice_messages/*.oga'
    ]
    
    test_file = None
    for pattern in test_files:
        if '*' in pattern:
            from glob import glob
            files = glob(pattern)
            if files:
                test_file = files[0]
                break
        elif os.path.exists(pattern):
            test_file = pattern
            break
    
    if test_file:
        print(f"\n🎵 Найден тестовый файл: {test_file}")
        for provider_name in providers_to_test:
            try:
                print(f"\n=== Тест транскрипции с {provider_name} ===")
                provider = ASRFactory.create_from_string(provider_name)
                provider.load_model()
                result = provider.transcribe(test_file)
                print(f"📝 Результат ({provider_name}): {result}")
                provider.cleanup()
            except Exception as e:
                print(f"❌ Ошибка тестирования {provider_name}: {e}")
    else:
        print("\n⚠️  Тестовый аудиофайл не найден. Поместите файл test.wav или test.mp3 в директорию")
    
    print("\n🏁 Тестирование завершено")

if __name__ == "__main__":
    main()
