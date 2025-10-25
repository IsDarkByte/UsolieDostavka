from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards import main_kb
from utils.logger import get_logger, log_command
from database.crud import get_orders_by_user_id, get_order_by_id
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
router = Router()

@router.message(Command("start"))
@log_command
async def cmd_start(message: types.Message):
    await message.answer(
        "🍔 Добро пожаловать в сервис доставки еды!\n\n"
        "Вы можете:\n"
        "• 🛍 Оформить новый заказ\n"
        "• 📊 Посмотреть статус последних заказов\n"
        "• 🔍 Написать #123 для просмотра конкретного заказа\n\n"
        "Выберите действие:",
        reply_markup=main_kb()
    )

@router.message(F.text == "📊 Статус заказа")
@log_command
async def check_order_status(message: types.Message, session: AsyncSession):
    logger.info(f"📊 Пользователь {message.from_user.id} запросил статус заказа")
    
    try:
        # Получаем последние заказы пользователя
        orders = await get_orders_by_user_id(session, message.from_user.id, limit=5)
        
        if not orders:
            await message.answer(
                "📭 У вас еще нет заказов.\n"
                "Нажмите «🛍 Оформить заказ», чтобы сделать первый заказ!",
                reply_markup=main_kb()
            )
            return
        
        # Показываем последний заказ подробно, а предыдущие - списком
        latest_order = orders[0]
        
        # Тексты статусов для пользователя
        status_texts = {
            'waiting_manager': '⏳ Ожидает подтверждения менеджером',
            'accepted': '✅ Подтвержден, готовится к отправке',
            'rejected': '❌ Отклонен менеджером',
            'in_delivery': '🚗 В пути к вам',
            'delivered': '🎉 Заказ доставлен'
        }
        
        payment_status_texts = {
            'pending': '⏳ Ожидает проверки',
            'verified': '✅ Подтверждена',
            'rejected': '❌ Отклонена'
        }
        
        # Формируем сообщение о последнем заказе
        order_info = (
            f"📦 **Ваш последний заказ**\n\n"
            f"🆔 Номер заказа: #{latest_order.id}\n"
            f"🛵 Рейс доставки: {latest_order.flight}\n"
            f"🏠 Адрес: {latest_order.address}\n"
            f"👤 Имя: {latest_order.first_name}\n"
            f"📞 Телефон: {latest_order.phone_number}\n"
            f"📊 Статус: {status_texts.get(latest_order.order_status, latest_order.order_status)}\n"
            f"💰 Статус оплаты: {payment_status_texts.get(latest_order.payment_status, latest_order.payment_status)}\n"
            f"📅 Создан: {latest_order.created_at.strftime('%d.%m.%Y в %H:%M')}\n"
        )
        
        # Если есть предыдущие заказы, покажем их кратко
        if len(orders) > 1:
            order_info += f"\n📋 **Предыдущие заказы ({len(orders)-1}):**\n"
            for i, order in enumerate(orders[1:], 1):
                status_icon = {
                    'waiting_manager': '⏳',
                    'accepted': '✅',
                    'rejected': '❌',
                    'in_delivery': '🚗',
                    'delivered': '🎉'
                }.get(order.order_status, '📦')
                
                order_info += f"{status_icon} Заказ #{order.id} - {order.created_at.strftime('%d.%m.%Y')}\n"
        
        await message.answer(order_info, reply_markup=main_kb())
        logger.info(f"📊 Отправлен статус заказа пользователю {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статуса заказа для пользователя {message.from_user.id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении статуса заказа.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой."
        )

@router.message(F.text.regexp(r'^#(\d+)$'))
async def check_specific_order(message: types.Message, session: AsyncSession):
    """Обработчик для просмотра конкретного заказа по ID (формат #123)"""
    try:
        order_id = int(message.text[1:])  # Убираем # и преобразуем в число
        logger.info(f"🔍 Пользователь {message.from_user.id} запросил заказ #{order_id}")
        
        order = await get_order_by_id(session, order_id)
        
        if not order:
            await message.answer("❌ Заказ с таким номером не найден.")
            return
            
        # Проверяем, что заказ принадлежит пользователю
        if order.user_id != message.from_user.id:
            await message.answer("❌ У вас нет доступа к этому заказу.")
            return
        
        # Тексты статусов
        status_texts = {
            'waiting_manager': '⏳ Ожидает подтверждения менеджером',
            'accepted': '✅ Подтвержден, готовится к отправке',
            'rejected': '❌ Отклонен менеджером',
            'in_delivery': '🚗 В пути к вам',
            'delivered': '🎉 Заказ доставлен'
        }
        
        payment_status_texts = {
            'pending': '⏳ Ожидает проверки',
            'verified': '✅ Подтверждена',
            'rejected': '❌ Отклонена'
        }
        
        order_info = (
            f"📦 **Заказ #{order.id}**\n\n"
            f"🛵 Рейс доставки: {order.flight}\n"
            f"🏠 Адрес: {order.address}\n"
            f"👤 Имя: {order.first_name}\n"
            f"📞 Телефон: {order.phone_number}\n"
            f"📊 Статус: {status_texts.get(order.order_status, order.order_status)}\n"
            f"💰 Статус оплаты: {payment_status_texts.get(order.payment_status, order.payment_status)}\n"
            f"📅 Создан: {order.created_at.strftime('%d.%m.%Y в %H:%M')}\n"
            f"🔄 Обновлен: {order.updated_at.strftime('%d.%m.%Y в %H:%M')}\n"
        )
        
        await message.answer(order_info, reply_markup=main_kb())
        logger.info(f"🔍 Отправлена информация о заказе #{order_id} пользователю {message.from_user.id}")
        
    except ValueError:
        await message.answer("❌ Неверный формат номера заказа. Используйте: #123")
    except Exception as e:
        logger.error(f"❌ Ошибка при получении заказа: {e}")
        await message.answer("❌ Произошла ошибка при получении информации о заказе.")
        