# ASR Модуль для Telegram Бота

Модульная система распознавания речи (ASR) с поддержкой нескольких провайдеров.

## 🎯 Основные возможности

- **Модульная архитектура** - легко добавлять новые провайдеры
- **Поддержка нескольких провайдеров** - Whisper, NeMo
- **Автоматическое переключение** - через конфигурацию
- **Единый интерфейс** - для всех провайдеров
- **Обработка ошибок** - с подробным логированием

## 🏗️ Архитектура

```
asr/
├── __init__.py          # Главный модуль
├── base.py              # Базовый абстрактный класс
├── whisper_provider.py  # Провайдер OpenAI Whisper
├── nemo_provider.py     # Провайдер NVIDIA NeMo
└── factory.py           # Фабрика провайдеров
```

## 🚀 Использование

### Создание провайдера

```python
from asr import ASRFactory

# Создание Whisper провайдера
config = {
    'model_name': 'turbo',
    'device': 'auto',
    'language': 'ru'
}
provider = ASRFactory.create_from_string('whisper', config)

# Загрузка модели
provider.load_model()

# Транскрипция
result = provider.transcribe('audio.wav')
print(result)
```

### Использование в боте

```python
from asr import ASRFactory

class VoiceBot:
    def __init__(self, config):
        # Создание ASR провайдера
        self.asr_provider = ASRFactory.create_from_string(
            config.asr_provider,
            {
                'model_name': config.asr_model_name,
                'device': config.asr_device,
                'language': config.asr_language
            }
        )
        self.asr_provider.load_model()
    
    def transcribe_audio(self, audio_path):
        return self.asr_provider.transcribe(audio_path)
```

## ⚙️ Конфигурация

### Через переменные окружения

```env
ASR_PROVIDER=whisper
ASR_MODEL_NAME=turbo
ASR_DEVICE=auto
ASR_LANGUAGE=ru
```

### Доступные провайдеры

#### Whisper
- **Модели**: `tiny`, `base`, `small`, `medium`, `large`, `turbo`
- **Устройства**: `auto`, `cpu`, `cuda`
- **Языки**: 99+ языков или `auto`

#### NeMo
- **Модели**: `nvidia/parakeet-tdt-0.6b-v2`, `nvidia/parakeet-tdt-1.1b`
- **Устройства**: `cuda` (обязательно)
- **Дополнительно**: Поддержка пакетной обработки

## 🧪 Тестирование

```bash
# Запуск тестов
python test_asr.py

# Проверка статуса в боте
/asr_status
```

## 📋 Требования

### Базовые
- Python 3.8+
- PyTorch 2.0+
- openai-whisper

### Для NeMo
- CUDA-совместимая GPU
- nemo_toolkit[asr]

## 🔧 Расширение

### Добавление нового провайдера

1. Создайте класс, наследующий от `ASRProvider`
2. Реализуйте абстрактные методы
3. Зарегистрируйте в фабрике

```python
from asr.base import ASRProvider
from asr.factory import ASRFactory, ASRProviderType

class CustomProvider(ASRProvider):
    @property
    def provider_name(self):
        return "Custom ASR"
    
    def load_model(self):
        # Загрузка модели
        pass
    
    def transcribe(self, audio_path):
        # Транскрипция
        return "transcribed text"

# Регистрация
ASRFactory.register_provider(ASRProviderType.CUSTOM, CustomProvider)
```

## 🎯 Следующие шаги

1. ✅ Базовая архитектура
2. ✅ Whisper провайдер
3. ✅ NeMo провайдер (базовая поддержка)
4. ✅ Фабрика провайдеров
5. ✅ Интеграция в бот
6. 🔄 Оптимизация производительности
7. 🔄 Дополнительные провайдеры
8. 🔄 Пакетная обработка
9. 🔄 Кэширование моделей
10. 🔄 Метрики и мониторинг
