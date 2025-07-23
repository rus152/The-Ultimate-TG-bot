# Dockerfile

# Stage 1: Build
# Используем базовый образ CUDA от NVIDIA для совместимости с GPU
# Выбираем Ubuntu 22.04 как в исходном, и CUDA 12.3 с cuDNN 9
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04 AS build

# Установка системных зависимостей
# - python3: Интерпретатор Python (предпочтительно 3.10+ для uv по умолчанию, но можно указать точнее)
# - curl: Для загрузки установщика uv
# - build-essential: Иногда требуется для компиляции нативных расширений (может понадобиться для некоторых пакетов)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    python3 python3-pip curl build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /root/.cache

# Установка uv и добавление его в PATH для этой команды
# Также сразу создаем venv в стандартной директории (.venv)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    # PATH модифицируется только для этой подкоманды в RUN
    # /root/.local/bin - стандартный путь установки для скрипта uv
    PATH="/root/.local/bin:$PATH" uv venv

# Делаем PATH с uv и venv/bin постоянным для всех последующих команд
# Это критически важно: сначала путь к uv (если нужно будет использовать снова),
# затем путь к venv, чтобы python/pip указывали туда.
ENV PATH="/root/.local/bin:/app/.venv/bin:$PATH"

# Установка рабочей директории
WORKDIR /app

# Копирование файла зависимостей
COPY requirements.txt .

# Создание виртуального окружения и установка зависимостей с помощью uv
# uv автоматически создаст venv в .venv внутри WORKDIR, если не указано иное
# --system тут НЕ нужен, так как мы хотим изолированное окружение
RUN uv venv && \
    # Активируем venv (необязательно для RUN, но делает команды ниже чище)
    # Устанавливаем зависимости в созданное виртуальное окружение
    # uv pip install автоматически использует активированное или созданное venv
    uv pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY main.py ./

# Stage 2: Run
# Используем тот же базовый образ для согласованности и минимального размера
FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

# Установка минимальных системных зависимостей для выполнения
# - python3: Интерпретатор (для запуска скриптов вне venv, если PATH настроен правильно)
# - ffmpeg: Для pydub
# - libsndfile1: Для pydub
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    ffmpeg \
    libsndfile1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /root/.cache

# Установка рабочей директории
WORKDIR /app

# Копирование виртуального окружения из этапа сборки
# Копируем всё виртуальное окружение (.venv), созданное uv
COPY --from=build /app/.venv ./.venv

# Копирование исходного кода
COPY --from=build /app/main.py ./

# Настройка среды:
# - PATH: Указываем путь к Python и pip из виртуального окружения в начале,
#         чтобы они использовались по умолчанию.
# - PYTHONUNBUFFERED=1: Для немедленного вывода логов в stdout/stderr.
# - PYTHONIOENCODING=UTF-8: Установка кодировки ввода-вывода (менее критично в Python 3.7+,
#                           но не повредит).
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

# Команда запуска
# Поскольку PATH настроен на venv/bin, `python` будет указывать на интерпретатор из venv.
CMD ["python", "main.py"]