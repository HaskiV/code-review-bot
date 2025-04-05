"""
Конфигурация логирования для Code Review Bot.
"""
import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Создаем директорию для логов, если она не существует
os.makedirs(LOGS_DIR, exist_ok=True)

def configure_logging(app_name="code_review_bot", level=logging.INFO):
    """
    Настройка логирования для приложения
    
    Аргументы:
        app_name (str): Название приложения
        level: Уровень логирования
        
    Возвращает:
        Экземпляр логгера
    """
    # Создаем логгер
    logger = logging.getLogger(app_name)
    logger.setLevel(level)
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Создаем обработчик для файла
    file_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, f"{app_name}.log"),
        maxBytes=10485760,  # 10МБ
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Создаем логгер по умолчанию
logger = configure_logging()