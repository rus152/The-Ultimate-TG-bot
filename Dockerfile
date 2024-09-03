# Этап 1: Сборка (build stage)
FROM debian:latest AS build

# Обновляем индекс пакетов и устанавливаем Python и FFmpeg
RUN apt update && \
    apt upgrade -y && \
    apt install -y python3 python3-pip python3.11-venv ffmpeg

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы requirements.txt в контейнер
COPY requirements.txt .

# Создаем виртуальное окружение и активируем его
RUN python3 -m venv venv && . venv/bin/activate

# Устанавливаем зависимости из requirements.txt
RUN venv/bin/pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы в контейнер
COPY main.py .
COPY .env .

# Этап 2: Выполнение (run stage)
FROM debian:latest

# Обновляем индекс пакетов и устанавливаем Python и FFmpeg
RUN apt update && \
    apt upgrade -y && \
    apt install -y python3 python3.11-venv ffmpeg

# Копируем файлы и зависимости из предыдущего этапа сборки
WORKDIR /app
COPY --from=build /app /app

# Указываем команду для запуска вашего Python скрипта
CMD ["./venv/bin/python", "main.py"]
