import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, setup_logging
from database.connection import init_db
from handlers import start_router, order_router, manager_router
from middlewares import DatabaseMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker

# Настройка логирования
logger = setup_logging()

async def main():
    """Основная функция запуска бота"""
    logger.info("🤖 Запуск бота доставки еды...")
    
    try:
        # Инициализация базы данных
        engine = await init_db()
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        
        # Создание бота и диспетчера
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Регистрируем middleware для базы данных
        database_middleware = DatabaseMiddleware(session_maker)
        dp.message.middleware.register(database_middleware)
        dp.callback_query.middleware.register(database_middleware)
        
        # Регистрация роутеров
        dp.include_router(start_router)
        dp.include_router(order_router)
        dp.include_router(manager_router)
        
        logger.info("✅ Бот успешно инициализирован, начинаем polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при запуске бота: {e}")
    finally:
        if 'bot' in locals():
            await bot.session.close()
        logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"💥 Непредвиденная ошибка: {e}")