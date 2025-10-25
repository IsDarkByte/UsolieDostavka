import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, setup_logging
from database.connection import init_db
from handlers import start_router, order_router, manager_router
from middlewares import DatabaseMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker
from utils.monitoring import get_monitor

# Настройка логирования
logger = setup_logging()

async def main():
    """Основная функция запуска бота"""
    logger.info("🤖 Запуск бота доставки еды...")
    
    bot = None
    monitoring_task = None
    monitor = None
    
    try:
        # Инициализация базы данных
        engine = await init_db()
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        
        # Создание бота и диспетчера
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Инициализация мониторинга
        monitor = get_monitor(bot)
        
        # Регистрируем middleware для базы данных
        database_middleware = DatabaseMiddleware(session_maker)
        dp.message.middleware.register(database_middleware)
        dp.callback_query.middleware.register(database_middleware)
        
        # Регистрация роутеров
        dp.include_router(start_router)
        dp.include_router(order_router)
        dp.include_router(manager_router)
        
        # Отправляем уведомление о запуске
        await monitor.send_startup_notification()
        
        # Запускаем периодический мониторинг в фоне
        monitoring_task = asyncio.create_task(monitor.periodic_monitoring())
        
        logger.info("✅ Бот успешно инициализирован, начинаем polling...")
        
        # Обработка ошибок в polling
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Ошибка в polling: {e}")
            await monitor.send_error_alert(e, "Polling")
            raise
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при запуске бота: {e}")
        if monitor:
            await monitor.send_error_alert(e, "Критическая ошибка запуска")
    finally:
        # Останавливаем мониторинг
        if monitoring_task:
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Отправляем уведомление об остановке
        if monitor:
            await monitor.send_shutdown_notification()
        
        # Закрываем соединения
        if bot:
            await bot.session.close()
        
        logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.critical(f"💥 Непредвиденная ошибка: {e}")
        