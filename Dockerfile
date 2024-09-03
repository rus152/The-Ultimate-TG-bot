# Этап 1: Сборка (build stage)
FROM alpine:latest AS build

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

# Этап 2: Выполнение (run stage)
FROM alpine:latest

# Устанавливаем Python и FFmpeg
RUN apk update && \
    apk add --no-cache python3 ffmpeg

# Копируем файлы и зависимости из предыдущего этапа сборки
WORKDIR /app
COPY --from=build /app /app

# Указываем команду для запуска вашего Python скрипта
CMD ["python3", "your_script.py"]
