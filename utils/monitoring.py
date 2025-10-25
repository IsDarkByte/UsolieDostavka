import asyncio
import logging
import psutil
import traceback
from datetime import datetime
from aiogram import Bot
from config import MANAGER_CHAT_ID, bot

logger = logging.getLogger(__name__)


class ServerMonitor:
    """Мониторинг состояния сервера и бота"""
    
    def __init__(self, bot_instance: Bot):
        self.bot = bot_instance
        self.start_time = datetime.now()
        self.error_count = 0
        self.last_error = None
        
    def get_uptime(self) -> str:
        """Получить время работы бота"""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        return f"{days}д {hours}ч {minutes}м"
    
    def get_system_stats(self) -> dict:
        """Получить статистику системы"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu': f"{cpu_percent}%",
                'memory_used': f"{memory.percent}%",
                'memory_available': f"{memory.available / (1024**2):.0f} МБ",
                'disk_used': f"{disk.percent}%",
                'disk_free': f"{disk.free / (1024**3):.1f} ГБ"
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    async def send_status_report(self):
        """Отправить отчёт о состоянии в Telegram"""
        try:
            stats = self.get_system_stats()
            uptime = self.get_uptime()
            
            message = f"""
🤖 <b>Статус бота доставки еды</b>

⏱ <b>Время работы:</b> {uptime}
🔄 <b>Статус:</b> ✅ Работает

📊 <b>Система:</b>
├ CPU: {stats.get('cpu', 'N/A')}
├ RAM: {stats.get('memory_used', 'N/A')} (свободно: {stats.get('memory_available', 'N/A')})
└ Диск: {stats.get('disk_used', 'N/A')} (свободно: {stats.get('disk_free', 'N/A')})

❌ <b>Ошибки:</b> {self.error_count}
{f"└ Последняя: {self.last_error}" if self.last_error else "└ Ошибок нет"}

📅 <b>Время отчёта:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
            """
            
            await self.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=message.strip(),
                parse_mode="HTML"
            )
            logger.info("✅ Статус-отчёт отправлен менеджеру")
            
        except Exception as e:
            logger.error(f"Ошибка отправки статус-отчёта: {e}")
    
    async def send_error_alert(self, error: Exception, context: str = ""):
        """Отправить уведомление об ошибке"""
        try:
            self.error_count += 1
            self.last_error = f"{context}: {str(error)[:100]}"
            
            error_trace = ''.join(traceback.format_exception(
                type(error), error, error.__traceback__
            ))[-1000:]  # Последние 1000 символов трейсбека
            
            message = f"""
🚨 <b>ОШИБКА В БОТЕ</b>

📍 <b>Контекст:</b> {context or 'Неизвестно'}
❌ <b>Ошибка:</b> {type(error).__name__}
💬 <b>Сообщение:</b> {str(error)[:200]}

📊 <b>Статистика ошибок:</b> {self.error_count}

🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

<code>{error_trace[:500]}</code>
            """
            
            await self.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=message.strip(),
                parse_mode="HTML"
            )
            logger.warning(f"⚠️ Отправлено уведомление об ошибке: {error}")
            
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление об ошибке: {e}")
    
    async def send_startup_notification(self):
        """Отправить уведомление о запуске бота"""
        try:
            message = f"""
✅ <b>БОТ ЗАПУЩЕН</b>

🤖 Бот доставки еды успешно запущен и готов к работе!

🕐 <b>Время запуска:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
💻 <b>Сервер:</b> Amvera Cloud
            """
            
            await self.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=message.strip(),
                parse_mode="HTML"
            )
            logger.info("✅ Уведомление о запуске отправлено")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о запуске: {e}")
    
    async def send_shutdown_notification(self):
        """Отправить уведомление об остановке бота"""
        try:
            uptime = self.get_uptime()
            message = f"""
⛔️ <b>БОТ ОСТАНОВЛЕН</b>

⏱ <b>Проработал:</b> {uptime}
❌ <b>Всего ошибок:</b> {self.error_count}

🕐 <b>Время остановки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
            """
            
            await self.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=message.strip(),
                parse_mode="HTML"
            )
            logger.info("🛑 Уведомление об остановке отправлено")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об остановке: {e}")
    
    async def periodic_monitoring(self):
        """Периодический мониторинг (каждые 24 часа)"""
        while True:
            try:
                await asyncio.sleep(24 * 60 * 60)  # 24 часа
                await self.send_status_report()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в периодическом мониторинге: {e}")


# Глобальный экземпляр монитора
monitor = None


def get_monitor(bot_instance: Bot = None) -> ServerMonitor:
    """Получить экземпляр монитора"""
    global monitor
    if monitor is None and bot_instance:
        monitor = ServerMonitor(bot_instance)
    return monitor
