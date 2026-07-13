# The Ultimate TG Bot

Короткая инструкция по запуску и настройке бота распознавания голосовых сообщений.

## Что делает

- Загружает голосовые сообщения и видео-ноты из чата.
- Отправляет аудио и видео в whisper-server без перекодирования и публикует результат распознавания в чате.
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
- `WHISPER_SERVER_URL` — адрес запущенного whisper-server (по умолчанию `http://localhost:3373`).
- `WHISPER_SERVER_URLS` — несколько адресов через запятую в порядке приоритета. Если задано, заменяет `WHISPER_SERVER_URL`; fallback срабатывает при сетевых ошибках, таймаутах, HTTP `429` и `5xx`.
- `WHISPER_SERVER_TIMEOUT` — максимальное время распознавания в секундах (по умолчанию `180`).
- `WHISPER_HEALTH_INTERVAL` — интервал фоновой проверки `/health` в секундах (по умолчанию `60`).
- `WHISPER_HEALTH_TIMEOUT` — таймаут одной фоновой проверки в секундах (по умолчанию `10`).
- `WHISPER_LANGUAGE` — подсказка языка (`ru`, `en` и т. п.). Если не задана или пуста, Whisper определяет язык автоматически.

Перед запуском бота поднимите [whisper-server](https://github.com/the80hz/whisper-server) и укажите доступный боту URL. Если бот работает в Docker, `localhost` указывает на сам контейнер, поэтому используйте DNS-имя сервиса или адрес хоста.

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
