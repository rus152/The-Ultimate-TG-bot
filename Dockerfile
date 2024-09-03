# Этап 1: Сборка (build stage)
FROM debian:latest AS build

# Обновляем индекс пакетов, устанавливаем Python, venv и FFmpeg в одном RUN
RUN apt update && apt upgrade -y && apt install -y \
    python3 python3-pip python3.11-venv ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы requirements.txt и создаем виртуальное окружение в одном RUN
COPY requirements.txt .
RUN python3 -m venv venv && venv/bin/pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы
COPY main.py .
COPY .env .

# Этап 2: Выполнение (run stage)
FROM debian:latest

# Устанавливаем необходимые пакеты
RUN apt update && apt upgrade -y && apt install -y \
    python3 python3.11-venv ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Копируем файлы из этапа сборки
WORKDIR /app
COPY --from=build /app /app

# Запуск приложения
CMD ["./venv/bin/python", "main.py"]
