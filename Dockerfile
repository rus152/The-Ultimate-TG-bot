# Этап 1: Сборка (build stage)
FROM python:3.11-slim AS build

# Обновляем индекс пакетов, устанавливаем зависимости
RUN apt update && apt install -y --no-install-recommends \
    ffmpeg && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы requirements.txt и создаем виртуальное окружение
COPY requirements.txt ./
RUN python3 -m venv venv && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы
COPY main.py ./
COPY .env ./

# Финальный этап: создаём минимальный образ
FROM python:3.11-slim

# Устанавливаем только FFmpeg
RUN apt update && apt install -y --no-install-recommends \
    ffmpeg && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем виртуальное окружение и остальные файлы из этапа сборки
COPY --from=build /app/venv ./venv
COPY --from=build /app/main.py ./
COPY --from=build /app/.env ./

# Запуск приложения
CMD ["./venv/bin/python", "main.py"]
