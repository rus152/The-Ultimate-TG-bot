# Этап 1: Сборка (build stage)
FROM alpine:latest AS build

ARG PYTHON_VERSION=3.11.9

# install build dependencies and needed tools
RUN apk add \
    wget \
    gcc \
    make \
    zlib-dev \
    libffi-dev \
    openssl-dev \
    musl-dev

# download and extract python sources
RUN cd /opt \
    && wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz \                                              
    && tar xzf Python-${PYTHON_VERSION}.tgz

# build python and remove left-over sources
RUN cd /opt/Python-${PYTHON_VERSION} \ 
    && ./configure --prefix=/usr --enable-optimizations --with-ensurepip=install \
    && make install \
    && rm /opt/Python-${PYTHON_VERSION}.tgz /opt/Python-${PYTHON_VERSION} -rf

# Создаем рабочую директорию
WORKDIR /app

# Копируем файл requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы в контейнер
COPY main.py .
COPY .env .

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
