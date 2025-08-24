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

## Переменные окружения

Скопируйте `example.env` в `.env` и заполните значения.

- `TELEGRAM_BOT_TOKEN` — токен Telegram-бота.
- `DEBUG_CHAT_ID` — id чата для тестирования debug-режима (например, `-1001234567890`).
- `DEBUG_MODE` — `True` или `False`. Если `True`, бот будет отвечать только в `DEBUG_CHAT_ID`.
- `USE_CUDA` — `True`/`False` или `1`/`0`. Управляет выбором устройства для модели (если `True`, код попытается использовать CUDA; по умолчанию `False`).

## Установка зависимостей

Рекомендуется использовать виртуальное окружение.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

Можно запустить напрямую или через Docker Compose (если настроено):

```bash
# Запуск напрямую
export $(cat .env | xargs)
python main.py

# Или с Docker Compose
docker compose up -d
```
