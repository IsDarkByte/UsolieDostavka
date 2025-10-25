import os
import logging
from dotenv import load_dotenv
from aiogram import Bot

# Загрузка переменных окружения
load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

if not MANAGER_CHAT_ID:
    raise ValueError("MANAGER_CHAT_ID не найден в переменных окружения")

# Создаем экземпляр бота
bot = Bot(token=BOT_TOKEN)

# Всегда используем /data/logs для логов
LOG_DIR = "/data/logs"
os.makedirs(LOG_DIR, exist_ok=True)

class CustomFormatter(logging.Formatter):
    """Кастомный форматтер для цветного вывода в консоль"""
    
    # Цветовые коды
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[34;20m"
    magenta = "\x1b[35;20m"
    cyan = "\x1b[36;20m"
    reset = "\x1b[0m"
    
    # Формат логов
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Форматы для разных уровней
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logging():
    """Настройка логирования с цветным выводом"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Хендлер для консоли с цветами
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CustomFormatter())
    
    # Хендлер для файла в /data/logs
    log_file = f"{LOG_DIR}/delivery_bot.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Добавляем хендлеры к логгеру
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)
