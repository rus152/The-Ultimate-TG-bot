#!/bin/bash
# deploy.sh - Скрипт для развертывания бота

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода цветных сообщений
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Проверка системы
check_system() {
    log "Проверка системы..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен. Установите Docker и повторите попытку."
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен. Установите Docker Compose и повторите попытку."
        exit 1
    fi
    
    # Проверка прав Docker
    if ! docker ps &> /dev/null; then
        error "Нет прав для работы с Docker. Добавьте пользователя в группу docker."
        exit 1
    fi
    
    log "Система проверена успешно!"
}

# Настройка окружения
setup_env() {
    log "Настройка окружения..."
    
    if [ ! -f .env ]; then
        cp example.env .env
        warn "Файл .env создан из example.env"
        warn "Не забудьте отредактировать .env файл с вашими настройками!"
        echo
        info "Откройте .env файл и установите:"
        info "- TELEGRAM_BOT_TOKEN (обязательно)"
        info "- DEBUG_CHAT_ID (опционально)"
        info "- Другие настройки по необходимости"
        echo
        read -p "Нажмите Enter после редактирования .env файла..."
    else
        log "Файл .env уже существует"
    fi
    
    # Создание папок
    mkdir -p voice_messages video_notes logs
    log "Папки созданы"
}

# Сборка Docker образа
build_image() {
    log "Сборка Docker образа..."
    docker-compose build
    log "Docker образ собран успешно!"
}

# Запуск сервисов
start_services() {
    log "Запуск сервисов..."
    docker-compose up -d
    log "Сервисы запущены!"
    
    # Ожидание запуска
    sleep 5
    
    # Проверка статуса
    if docker-compose ps | grep -q "Up"; then
        log "Бот успешно запущен!"
        info "Используйте 'docker-compose logs -f' для просмотра логов"
        info "Используйте 'docker-compose down' для остановки"
    else
        error "Ошибка запуска бота. Проверьте логи: docker-compose logs"
        exit 1
    fi
}

# Проверка конфигурации
check_config() {
    log "Проверка конфигурации..."
    
    if [ ! -f .env ]; then
        error "Файл .env не найден!"
        exit 1
    fi
    
    # Проверка обязательных переменных
    if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep -q "TELEGRAM_BOT_TOKEN=your_telegram_bot_token" .env; then
        error "TELEGRAM_BOT_TOKEN не настроен в .env файле!"
        exit 1
    fi
    
    log "Конфигурация корректна"
}

# Остановка сервисов
stop_services() {
    log "Остановка сервисов..."
    docker-compose down
    log "Сервисы остановлены"
}

# Показать статус
show_status() {
    info "Статус сервисов:"
    docker-compose ps
    echo
    info "Логи (последние 20 строк):"
    docker-compose logs --tail=20
}

# Обновление
update() {
    log "Обновление бота..."
    
    # Остановка
    docker-compose down
    
    # Сборка
    docker-compose build --no-cache
    
    # Запуск
    docker-compose up -d
    
    log "Обновление завершено!"
}

# Помощь
show_help() {
    echo "Скрипт развертывания The Ultimate Telegram Bot"
    echo
    echo "Использование: $0 [команда]"
    echo
    echo "Команды:"
    echo "  deploy    - Полное развертывание (по умолчанию)"
    echo "  start     - Запустить сервисы"
    echo "  stop      - Остановить сервисы"
    echo "  restart   - Перезапустить сервисы"
    echo "  status    - Показать статус"
    echo "  logs      - Показать логи"
    echo "  update    - Обновить бот"
    echo "  help      - Показать эту справку"
    echo
}

# Основная функция
main() {
    case "${1:-deploy}" in
        deploy)
            info "Начинаем развертывание The Ultimate Telegram Bot..."
            check_system
            setup_env
            check_config
            build_image
            start_services
            info "Развертывание завершено успешно!"
            ;;
        start)
            check_config
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 2
            start_services
            ;;
        status)
            show_status
            ;;
        logs)
            docker-compose logs -f
            ;;
        update)
            update
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

# Обработка сигналов
trap 'echo -e "\n${YELLOW}Операция прервана пользователем${NC}"; exit 130' INT

# Запуск
main "$@"
