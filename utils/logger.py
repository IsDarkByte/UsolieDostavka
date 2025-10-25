import logging
import functools
from typing import Callable, Any

def get_logger(name: str) -> logging.Logger:
    """Получить логгер с заданным именем"""
    return logging.getLogger(name)

def log_command(func: Callable) -> Callable:
    """Декоратор для логирования команд"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        try:
            message = args[0] if args else None
            if hasattr(message, 'from_user'):
                user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
                logger.info(f"🔄 Команда {func.__name__} от пользователя {user_info}")
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Ошибка в команде {func.__name__}: {e}")
            raise
    return wrapper

def log_callback(func: Callable) -> Callable:
    """Декоратор для логирования callback'ов"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        try:
            callback = args[0] if args else None
            if hasattr(callback, 'data'):
                logger.info(f"🔘 Callback {callback.data} от пользователя @{callback.from_user.username}")
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Ошибка в callback {func.__name__}: {e}")
            raise
    return wrapper

def log_database_operation(func: Callable) -> Callable:
    """Декоратор для логирования операций с БД"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"📊 Операция БД {func.__name__} выполнена успешно")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка БД в {func.__name__}: {e}")
            raise
    return wrapper
