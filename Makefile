# Makefile для The Ultimate Telegram Bot

.PHONY: help install run docker-build docker-run docker-stop docker-logs clean test

# Переменные
PYTHON := python3
PIP := pip3
DOCKER_IMAGE := the80hz/utgb
DOCKER_TAG := latest
CONTAINER_NAME := whisper_voice_bot

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)The Ultimate Telegram Bot - Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Установить зависимости
	@echo "$(YELLOW)Установка зависимостей...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Зависимости установлены!$(NC)"

setup: ## Настроить окружение
	@echo "$(YELLOW)Настройка окружения...$(NC)"
	@if [ ! -f .env ]; then \
		cp example.env .env; \
		echo "$(GREEN)Файл .env создан из example.env$(NC)"; \
		echo "$(RED)Не забудьте отредактировать .env файл!$(NC)"; \
	else \
		echo "$(YELLOW)Файл .env уже существует$(NC)"; \
	fi
	@mkdir -p voice_messages video_notes logs
	@echo "$(GREEN)Папки созданы!$(NC)"

run: ## Запустить бота локально
	@echo "$(YELLOW)Запуск бота...$(NC)"
	$(PYTHON) main.py

run-dev: ## Запустить бота в режиме разработки
	@echo "$(YELLOW)Запуск бота в режиме разработки...$(NC)"
	DEBUG_MODE=True LOG_LEVEL=DEBUG $(PYTHON) main.py

docker-build: ## Собрать Docker образ
	@echo "$(YELLOW)Сборка Docker образа...$(NC)"
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)Docker образ собран!$(NC)"

docker-run: ## Запустить Docker контейнер
	@echo "$(YELLOW)Запуск Docker контейнера...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Docker контейнер запущен!$(NC)"

docker-stop: ## Остановить Docker контейнер
	@echo "$(YELLOW)Остановка Docker контейнера...$(NC)"
	docker-compose down
	@echo "$(GREEN)Docker контейнер остановлен!$(NC)"

docker-logs: ## Показать логи Docker контейнера
	@echo "$(YELLOW)Логи Docker контейнера:$(NC)"
	docker-compose logs -f

docker-shell: ## Открыть shell в Docker контейнере
	@echo "$(YELLOW)Открытие shell в контейнере...$(NC)"
	docker exec -it $(CONTAINER_NAME) /bin/bash

docker-restart: ## Перезапустить Docker контейнер
	@echo "$(YELLOW)Перезапуск Docker контейнера...$(NC)"
	docker-compose restart
	@echo "$(GREEN)Docker контейнер перезапущен!$(NC)"

clean: ## Очистить временные файлы
	@echo "$(YELLOW)Очистка временных файлов...$(NC)"
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf *.pyc
	rm -rf voice_messages/*
	rm -rf video_notes/*
	rm -rf logs/*
	@echo "$(GREEN)Временные файлы очищены!$(NC)"

test: ## Запустить тесты
	@echo "$(YELLOW)Запуск тестов...$(NC)"
	$(PYTHON) -m pytest tests/ -v

lint: ## Проверить код с помощью flake8
	@echo "$(YELLOW)Проверка кода...$(NC)"
	flake8 main.py --max-line-length=120

format: ## Форматировать код с помощью black
	@echo "$(YELLOW)Форматирование кода...$(NC)"
	black main.py --line-length=120

check: lint format ## Проверить и отформатировать код

status: ## Показать статус контейнера
	@echo "$(YELLOW)Статус контейнера:$(NC)"
	docker-compose ps

health: ## Проверить здоровье контейнера
	@echo "$(YELLOW)Проверка здоровья контейнера:$(NC)"
	docker inspect --format='{{json .State.Health}}' $(CONTAINER_NAME) | jq

backup: ## Создать резервную копию логов
	@echo "$(YELLOW)Создание резервной копии...$(NC)"
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz logs/ voice_messages/ video_notes/
	@echo "$(GREEN)Резервная копия создана!$(NC)"

update: ## Обновить зависимости
	@echo "$(YELLOW)Обновление зависимостей...$(NC)"
	$(PIP) install -r requirements.txt --upgrade
	@echo "$(GREEN)Зависимости обновлены!$(NC)"

all: setup install docker-build ## Полная настройка проекта

.DEFAULT_GOAL := help
