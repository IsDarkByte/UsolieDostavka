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
        
        # Всегда используем папку /data для всего
        data_dir = "/data"
        os.makedirs(data_dir, exist_ok=True)
        
        # Пути для базы данных и логов внутри /data
        database_path = f"{data_dir}/delivery_bot.db"
        logs_dir = f"{data_dir}/logs"
        
        # Создаем подпапку для логов
        os.makedirs(logs_dir, exist_ok=True)
        
        # URL для базы данных
        DATABASE_URL = f"sqlite+aiosqlite:///{database_path}"
        
        if is_production:
            logger.info("🚀 Запуск в production режиме (Amvera)")
            logger.info(f"📁 База данных: {database_path}")
            logger.info(f"📁 Логи: {logs_dir}/")
        else:
            logger.info("💻 Запуск в локальном режиме")
            logger.info(f"📁 База данных: {database_path}")
            logger.info(f"📁 Логи: {logs_dir}/")
        
        # Создание движка базы данных
        engine = create_async_engine(
            DATABASE_URL, 
            echo=False,
            pool_pre_ping=True,  # Проверка соединения перед использованием
        )
        
        # Создание всех таблиц
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(f"✅ База данных успешно инициализирована: {database_path}")
        return engine
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации базы данных: {e}")
        raise
    
