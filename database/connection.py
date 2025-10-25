import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.models import Base

logger = logging.getLogger(__name__)

async def init_db():
    """Инициализация базы данных"""
    try:
        # Определяем окружение (локальная разработка или Amvera)
        is_production = os.getenv("AMVERA_ENVIRONMENT", "false").lower() == "true"
        
        # Создаем необходимые папки
        if is_production:
            # На Amvera Cloud - используем /data (постоянное хранилище)
            os.makedirs('/data', exist_ok=True)
            DATABASE_URL = "sqlite+aiosqlite:////data/delivery_bot.db"
            logger.info("🚀 Запуск в production режиме (Amvera)")
        else:
            # Локально - используем database/
            os.makedirs('database', exist_ok=True)
            DATABASE_URL = "sqlite+aiosqlite:///database/delivery_bot.db"
            logger.info("💻 Запуск в локальном режиме")
        
        # Папка для логов (всегда создаём)
        os.makedirs('logs', exist_ok=True)
        
        # Создание движка базы данных
        engine = create_async_engine(
            DATABASE_URL, 
            echo=False,
            pool_pre_ping=True,  # Проверка соединения перед использованием
        )
        
        # Создание всех таблиц
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(f"✅ База данных успешно инициализирована: {DATABASE_URL}")
        return engine
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise
    