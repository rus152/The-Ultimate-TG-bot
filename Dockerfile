# Dockerfile

# Этап 1: Сборка (build stage)
FROM python:3.11-slim AS build

# Установка зависимостей системы и Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN python -m venv venv && \
    ./venv/bin/pip install --upgrade pip && \
    ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода и файлов окружения
COPY main.py ./
COPY .env ./

# Этап 2: Финальный образ
FROM python:3.11-slim

# Установка зависимостей системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование виртуального окружения и исходного кода из этапа сборки
COPY --from=build /app/venv ./venv
COPY --from=build /app/main.py ./
COPY --from=build /app/.env ./

# Установка переменной PATH для использования виртуального окружения
ENV PATH="/app/venv/bin:$PATH"

# Определение команды запуска
CMD ["python", "main.py"]