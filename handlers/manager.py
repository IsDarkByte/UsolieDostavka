from aiogram import Router, types, F
from aiogram.filters import Command
from database.crud import get_order_by_id, update_order_status, get_recent_orders
from keyboards import manager_delivery_kb
from config import MANAGER_CHAT_ID, bot
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import get_logger
from utils.monitoring import get_monitor

logger = get_logger(__name__)
router = Router()

@router.message(Command("orders"))
async def view_orders(message: types.Message, session: AsyncSession):
    # Проверяем, что команда отправлена из чата менеджера
    if str(message.chat.id) != MANAGER_CHAT_ID:
        await message.answer("Эта команда только для менеджера")
        return
    
    try:
        orders = await get_recent_orders(session, limit=10)
        
        if not orders:
            await message.answer("Нет заказов")
            return
        
        text = "📋 Последние 10 заказов:\n\n"
        for order in orders:
            status_icons = {
                'waiting_manager': '⏳',
                'accepted': '✅',
                'rejected': '❌',
                'in_delivery': '🚗',
                'delivered': '🎉'
            }
            
            text += (
                f"{status_icons.get(order.order_status, '📦')} Заказ #{order.id}\n"
                f"Клиент: {order.first_name}\n"
                f"Телефон: {order.phone_number}\n"
                f"Рейс: {order.flight}\n"
                f"Статус: {order.order_status}\n"
                f"Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка заказов: {e}")
        await message.answer("Произошла ошибка при получении списка заказов")


@router.message(Command("status"))
async def cmd_status(message: types.Message):
    """Команда /status - показать статус бота и сервера"""
    # Проверка, что команду отправил менеджер
    if str(message.chat.id) != MANAGER_CHAT_ID:
        return
    
    monitor = get_monitor()
    if monitor:
        await monitor.send_status_report()
    else:
        await message.answer("⚠️ Мониторинг не инициализирован")


@router.message(Command("ping"))
async def cmd_ping(message: types.Message):
    """Команда /ping - быстрая проверка работоспособности"""
    if str(message.chat.id) != MANAGER_CHAT_ID:
        return
    
    monitor = get_monitor()
    uptime = monitor.get_uptime() if monitor else "N/A"
    
    await message.answer(
        f"🟢 <b>Бот работает!</b>\n"
        f"⏱ Uptime: {uptime}",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("manager_verify_payment_"))
async def manager_verify_payment(callback: types.CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split("_")[3])
    manager_id = callback.from_user.id
    
    logger.info(f"Менеджер {manager_id} подтверждает оплату заказа {order_id}")
    
    order = await update_order_status(
        session, 
        order_id, 
        payment_status='verified', 
        order_status='accepted', 
        manager_id=manager_id
    )
    
    if order:
        try:
            await bot.send_message(
                chat_id=order.user_id,
                text=f"✅ Ваш заказ #{order.id} подтвержден!\n"
                     f"Ожидайте доставку в {order.flight}."
            )
            logger.info(f"📢 Пользователь {order.user_id} уведомлен о подтверждении заказа {order_id}")
        except Exception as e:
            logger.error(f"❌ Не удалось уведомить пользователя {order.user_id}: {e}")
        
        await callback.message.edit_text(
            f"✅ Заказ #{order.id} подтвержден\n"
            f"Клиент: {order.first_name}\n"
            f"Телефон: {order.phone_number}\n"
            f"Адрес: {order.address}\n"
            f"Рейс: {order.flight}",
            reply_markup=manager_delivery_kb(order.id)
        )
        
        await callback.answer("Заказ подтвержден")
    else:
        logger.warning(f"⚠️ Заказ {order_id} не найден при подтверждении менеджером {manager_id}")
        await callback.answer("Заказ не найден")

@router.callback_query(F.data.startswith("manager_reject_payment_"))
async def manager_reject_payment(callback: types.CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split("_")[3])
    manager_id = callback.from_user.id
    
    logger.info(f"Менеджер {manager_id} отклоняет заказ {order_id}")
    
    order = await update_order_status(
        session, 
        order_id, 
        payment_status='rejected', 
        order_status='rejected', 
        manager_id=manager_id
    )
    
    if order:
        try:
            await bot.send_message(
                chat_id=order.user_id,
                text=f"❌ Ваш заказ #{order.id} отклонен.\n"
                     f"Пожалуйста, свяжитесь с поддержкой для уточнения деталей."
            )
            logger.info(f"📢 Пользователь {order.user_id} уведомлен об отклонении заказа {order_id}")
        except Exception as e:
            logger.error(f"❌ Не удалось уведомить пользователя {order.user_id}: {e}")
        
        await callback.message.edit_text(f"❌ Заказ #{order.id} отклонен")
        await callback.answer("Заказ отклонен")
    else:
        logger.warning(f"⚠️ Заказ {order_id} не найден при отклонении менеджером {manager_id}")
        await callback.answer("Заказ не найден")

@router.callback_query(F.data.startswith("manager_accept_"))
async def manager_accept_order(callback: types.CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split("_")[2])
    manager_id = callback.from_user.id
    
    logger.info(f"Менеджер {manager_id} принимает заказ {order_id} в доставку")
    
    order = await get_order_by_id(session, order_id)
    
    if order:
        order = await update_order_status(session, order_id, order_status='accepted')
        
        try:
            await bot.send_message(
                chat_id=order.user_id,
                text=f"🎉 Ваш заказ #{order.id} принят в доставку!\n"
                     f"Ожидайте доставку в {order.flight}."
            )
            logger.info(f"📢 Пользователь {order.user_id} уведомлен о принятии заказа {order_id}")
        except Exception as e:
            logger.error(f"❌ Не удалось уведомить пользователя {order.user_id}: {e}")
        
        await callback.message.edit_text(
            f"✅ Заказ #{order.id} принят в доставку\n"
            f"Клиент: {order.first_name}\n"
            f"Телефон: {order.phone_number}\n"
            f"Адрес: {order.address}\n"
            f"Рейс: {order.flight}",
            reply_markup=manager_delivery_kb(order.id)
        )
        
        await callback.answer("Заказ принят в доставку")
    else:
        logger.warning(f"⚠️ Заказ {order_id} не найден")
        await callback.answer("Заказ не найден")

@router.callback_query(F.data.startswith("manager_delivery_"))
async def manager_start_delivery(callback: types.CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split("_")[2])
    manager_id = callback.from_user.id
    
    logger.info(f"Менеджер {manager_id} отмечает заказ {order_id} как 'в доставке'")
    
    order = await update_order_status(session, order_id, order_status='in_delivery')
    
    if order:
        try:
            await bot.send_message(
                chat_id=order.user_id,
                text=f"🚗 Ваш заказ #{order.id} в пути!\n"
                     f"Курьер уже едет к вам по адресу: {order.address}"
            )
            logger.info(f"📢 Пользователь {order.user_id} уведомлен о начале доставки заказа {order_id}")
        except Exception as e:
            logger.error(f"❌ Не удалось уведомить пользователя {order.user_id}: {e}")
        
        # Обновляем сообщение, убирая кнопку "В доставке"
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="✅ Доставлен", callback_data=f"manager_delivered_{order.id}"))
        
        await callback.message.edit_text(
            f"🚗 Заказ #{order.id} в доставке\n"
            f"Клиент: {order.first_name}\n"
            f"Телефон: {order.phone_number}\n"
            f"Адрес: {order.address}\n"
            f"Рейс: {order.flight}",
            reply_markup=builder.as_markup()
        )
        
        await callback.answer("Статус обновлен: в доставке")
    else:
        logger.warning(f"⚠️ Заказ {order_id} не найден при попытке изменения статуса менеджером {manager_id}")
        await callback.answer("Заказ не найден")

@router.callback_query(F.data.startswith("manager_delivered_"))
async def manager_complete_delivery(callback: types.CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split("_")[2])
    manager_id = callback.from_user.id
    
    logger.info(f"Менеджер {manager_id} отмечает заказ {order_id} как 'доставлен'")
    
    order = await update_order_status(session, order_id, order_status='delivered')
    
    if order:
        try:
            await bot.send_message(
                chat_id=order.user_id,
                text=f"🎉 Ваш заказ #{order.id} доставлен!\n"
                     f"Приятного аппетита! 🍔\n"
                     f"Спасибо, что выбрали наш сервис!"
            )
            logger.info(f"📢 Пользователь {order.user_id} уведомлен о доставке заказа {order_id}")
        except Exception as e:
            logger.error(f"❌ Не удалось уведомить пользователя {order.user_id}: {e}")
        
        await callback.message.edit_text(f"✅ Заказ #{order.id} доставлен")
        await callback.answer("Заказ доставлен")
    else:
        logger.warning(f"⚠️ Заказ {order_id} не найден при попытке завершения менеджером {manager_id}")
        await callback.answer("Заказ не найден")
        