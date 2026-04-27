# 📊 Система мониторинга бота

## 🎯 Что умеет система мониторинга

### Автоматический мониторинг
- ✅ **Отправка статуса каждые 24 часа** в Telegram менеджеру
- ✅ **Уведомление при запуске бота**
- ✅ **Уведомление при остановке бота**
- ✅ **Автоматическая отправка критических ошибок**

### Отслеживаемые метрики
- 🖥 **CPU** — загрузка процессора
- 💾 **RAM** — использование памяти
- 💿 **Disk** — использование диска
- ⏱ **Uptime** — время работы бота
- ❌ **Errors** — количество и последняя ошибка

## 🚀 Установка

### Шаг 1: Обновите файлы

Замените следующие файлы в вашем проекте:

```bash
utils/monitoring.py     # Новый файл
main.py                 # Обновлённый
requirements.txt        # Добавлен psutil
handlers/manager.py     # Добавлены команды /status и /ping
```

### Шаг 2: Установите зависимости

```bash
pip install psutil
```

Или обновите через requirements:
```bash
pip install -r requirements.txt
```

### Шаг 3: Деплой на Amvera

```bash
git add .
git commit -m "Add monitoring system"
git push amvera master
```

## 📱 Команды для менеджера

| Команда | Описание |
|---------|----------|
| `/status` | Полный отчёт о состоянии сервера и бота |
| `/ping` | Быстрая проверка "бот жив?" |
| `/orders` | Список последних заказов (уже было) |

## 📊 Примеры уведомлений

### 1. Уведомление при запуске
```
✅ БОТ ЗАПУЩЕН

🤖 Бот доставки еды успешно запущен и готов к работе!

🕐 Время запуска: 25.10.2025 14:30:15
💻 Сервер: Amvera Cloud
```

### 2. Периодический статус (каждые 6 часов)
```
🤖 Статус бота доставки еды

⏱ Время работы: 0д 6ч 15м
🔄 Статус: ✅ Работает

📊 Система:
├ CPU: 12.5%
├ RAM: 45% (свободно: 55 МБ)
└ Диск: 8% (свободно: 1.8 ГБ)

❌ Ошибки: 2
└ Последняя: Order processing: Database timeout

📅 Время отчёта: 25.10.2025 20:45:30
```

### 3. Критическая ошибка
```
🚨 ОШИБКА В БОТЕ

📍 Контекст: Order processing
❌ Ошибка: OperationalError
💬 Сообщение: database is locked

📊 Статистика ошибок: 3

🕐 Время: 25.10.2025 15:22:45

Traceback (most recent call last):
  File "handlers/order.py", line 45
  ...
```

### 4. Уведомление при остановке
```
⛔️ БОТ ОСТАНОВЛЕН

⏱ Проработал: 2д 14ч 32м
❌ Всего ошибок: 5

🕐 Время остановки: 27.10.2025 05:02:18
```

## ⚙️ Настройка частоты отчётов

В файле `utils/monitoring.py` измените интервал:

```python
async def periodic_monitoring(self):
    """Периодический мониторинг"""
    while True:
        try:
            # Измените на нужный интервал:
            await asyncio.sleep(6 * 60 * 60)  # 6 часов (по умолчанию)
            # await asyncio.sleep(1 * 60 * 60)  # 1 час
            # await asyncio.sleep(12 * 60 * 60)  # 12 часов
            # await asyncio.sleep(24 * 60 * 60)  # 24 часа
            
            await self.send_status_report()
        except asyncio.CancelledError:
            break
```

## 🔧 Расширенные возможности

### Мониторинг конкретных ошибок

Добавьте в ваши хендлеры:

```python
from utils.monitoring import get_monitor

async def process_order(message: Message):
    try:
        # Ваш код обработки заказа
        pass
    except Exception as e:
        # Отправить уведомление об ошибке
        monitor = get_monitor()
        await monitor.send_error_alert(e, "Обработка заказа")
        raise
```

### Мониторинг базы данных

```python
from utils.monitoring import get_monitor
from sqlalchemy import text

async def check_database_health():
    """Проверка здоровья БД"""
    try:
        async with session_maker() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM orders"))
            count = result.scalar()
            logger.info(f"✅ БД работает, заказов: {count}")
    except Exception as e:
        monitor = get_monitor()
        await monitor.send_error_alert(e, "Проверка БД")
```

## 📈 Дополнительные метрики

### Добавить отслеживание количества заказов

В `utils/monitoring.py` добавьте:

```python
from database.crud import get_orders_count

async def send_status_report(self):
    # ... существующий код ...
    
    # Добавить статистику заказов
    total_orders = await get_orders_count()
    
    message = f"""
    # ... существующее сообщение ...
    
📦 <b>Заказы:</b> {total_orders} всего
    """
```

## 🆘 Решение проблем

### Мониторинг не отправляет сообщения

**Проверьте:**
1. `MANAGER_CHAT_ID` правильно настроен
2. Бот не заблокирован менеджером
3. Логи показывают отправку сообщений

### Ошибка "psutil not found"

```bash
pip install psutil
# Затем
git add requirements.txt
git commit -m "Add psutil"
git push amvera master
```

### Слишком много уведомлений

Увеличьте интервал отчётов:
```python
await asyncio.sleep(12 * 60 * 60)  # 12 часов вместо 6
```

Или отключите периодические отчёты:
```python
# В main.py закомментируйте:
# monitoring_task = asyncio.create_task(monitor.periodic_monitoring())
```

## 💡 Советы по использованию

### 1. Настройте уведомления в Telegram
- Включите звук для чата с ботом
- Закрепите чат для быстрого доступа

### 2. Регулярно проверяйте статус
```bash
# Отправьте боту в Telegram:
/status
```

### 3. Следите за трендами
- Если ошибок становится больше → проверьте код
- Если RAM растёт → возможна утечка памяти
- Если CPU высокий → оптимизируйте запросы

### 4. Настройте алерты для критических ошибок
Можно добавить интеграцию с другими сервисами:
- Email уведомления
- SMS алерты
- Webhook в Slack/Discord

## 🎓 Альтернативные решения мониторинга

Если хотите более продвинутый мониторинг:

### 1. **UptimeRobot** (бесплатно)
- Проверка доступности бота
- Email/SMS уведомления
- https://uptimerobot.com

### 2. **Healthchecks.io** (бесплатно)
- Ping-мониторинг
- Интеграция с Telegram
- https://healthchecks.io

### 3. **Grafana Cloud Free Tier**
- Графики метрик
- Дашборды
- https://grafana.com/products/cloud/

---

<div align="center">

**Теперь у вас полный контроль над ботом! 🎉**

Следите за состоянием прямо в Telegram без платных тарифов мониторинга!

</div>
