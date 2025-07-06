#!/usr/bin/env python3
"""
Скрипт для мониторинга состояния Telegram бота
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)

class BotMonitor:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    def get_bot_info(self) -> Dict[str, Any]:
        """Получить информацию о боте"""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Ошибка при получении информации о боте: {e}")
            return {}
    
    def get_updates_count(self) -> int:
        """Получить количество обновлений"""
        try:
            response = requests.get(f"{self.base_url}/getUpdates", timeout=10)
            response.raise_for_status()
            data = response.json()
            return len(data.get('result', []))
        except requests.RequestException as e:
            logging.error(f"Ошибка при получении обновлений: {e}")
            return -1
    
    def check_webhook(self) -> Dict[str, Any]:
        """Проверить статус webhook"""
        try:
            response = requests.get(f"{self.base_url}/getWebhookInfo", timeout=10)
            response.raise_for_status()
            return response.json().get('result', {})
        except requests.RequestException as e:
            logging.error(f"Ошибка при проверке webhook: {e}")
            return {}
    
    def check_bot_health(self) -> bool:
        """Проверить здоровье бота"""
        bot_info = self.get_bot_info()
        if not bot_info.get('ok', False):
            logging.error("Бот недоступен")
            return False
        
        bot_data = bot_info.get('result', {})
        logging.info(f"Бот активен: {bot_data.get('username', 'Unknown')}")
        return True
    
    def monitor_loop(self, interval: int = 60):
        """Основной цикл мониторинга"""
        logging.info("Запуск мониторинга бота...")
        
        while True:
            try:
                start_time = time.time()
                
                # Проверка здоровья бота
                is_healthy = self.check_bot_health()
                
                # Получение статистики
                updates_count = self.get_updates_count()
                webhook_info = self.check_webhook()
                
                # Вывод статистики
                logging.info(f"Статус: {'OK' if is_healthy else 'ERROR'}")
                logging.info(f"Обновлений в очереди: {updates_count}")
                
                if webhook_info:
                    logging.info(f"Webhook URL: {webhook_info.get('url', 'Не установлен')}")
                
                # Проверка логов бота
                if os.path.exists('bot.log'):
                    stat = os.stat('bot.log')
                    logging.info(f"Размер лога: {stat.st_size} байт")
                
                # Проверка использования диска
                disk_usage = self.check_disk_usage()
                if disk_usage > 80:
                    logging.warning(f"Высокое использование диска: {disk_usage}%")
                
                elapsed_time = time.time() - start_time
                logging.info(f"Проверка завершена за {elapsed_time:.2f} секунд")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logging.info("Мониторинг остановлен пользователем")
                break
            except Exception as e:
                logging.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(interval)
    
    def check_disk_usage(self) -> float:
        """Проверить использование диска"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('.')
            return (used / total) * 100
        except Exception as e:
            logging.error(f"Ошибка при проверке диска: {e}")
            return 0

def main():
    """Главная функция"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        logging.error("Не найден TELEGRAM_BOT_TOKEN в переменных окружения")
        sys.exit(1)
    
    monitor = BotMonitor(bot_token)
    
    # Разовая проверка или мониторинг
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        monitor.check_bot_health()
    else:
        interval = int(os.getenv('MONITOR_INTERVAL', '60'))
        monitor.monitor_loop(interval)

if __name__ == '__main__':
    main()
