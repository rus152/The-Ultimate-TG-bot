# The Ultimate TG Bot

Короткая инструкция по запуску и настройке бота распознавания голосовых сообщений.

## Что делает

- Загружает голосовые сообщения и видео-ноты из чата.
- Распознаёт речь с помощью faster-whisper и отправляет результат в чат.
- Поддерживает debug-режим и очередь обработки.

## Файлы

- `main.py` — основной код бота.
- `requirements.txt` — зависимости.
- `example.env` — шаблон переменных окружения.
- `voice_messages/`, `video_notes/` — папки для временных файлов.
- `model_cache/` — кэш моделей faster-whisper (можно монтировать в Docker).

## Переменные окружения

Скопируйте `example.env` в `.env` и заполните значения.

- `TELEGRAM_BOT_TOKEN` — токен Telegram-бота.
- `DEBUG_CHAT_ID` — id чата для тестирования debug-режима (например, `-1001234567890`).
- `DEBUG_MODE` — `True` или `False`. Если `True`, бот будет отвечать только в `DEBUG_CHAT_ID`.
- `USE_CUDA` — `True`/`False` или `1`/`0`. Управляет выбором устройства для модели (если `True`, код попытается использовать CUDA; по умолчанию `False`).
- `WHISPER_MODEL_CACHE` — путь к кэшу моделей (по умолчанию `./model_cache`).

## Установка зависимостей

Рекомендуется использовать uv (быстрый менеджер окружений и зависимостей).

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
uv pip install -r requirements.txt
```

## Запуск

Можно запустить напрямую или через Docker Compose (если настроено):

```bash
# Запуск напрямую (через uv)
export $(cat .env | xargs)
uv run python main.py

# Или с Docker Compose
docker compose up -d
```
