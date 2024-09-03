# Используем базовый образ Alpine Linux
FROM alpine:latest

# Обновляем индекс пакетов и устанавливаем Python и FFmpeg
RUN apk update && \
    apk add --no-cache python3 py3-pip ffmpeg

# Создаем рабочую директорию
WORKDIR /app

# Копируем файл requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы в контейнер
COPY . .

# Указываем команду для запуска вашего Python скрипта
CMD ["python3", "main.py"]
