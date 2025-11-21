from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.states import OrderStates
from keyboards import flight_kb, cancel_kb, main_kb, manager_order_kb
from utils.logger import get_logger, log_command, log_callback
from database.crud import create_order
from config import bot, MANAGER_CHAT_ID
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
router = Router()

# Клавиатура для запроса номера телефона
def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
            [KeyboardButton(text="❌ Отменить заказ")]
        ],
        resize_keyboard=True
    )

@router.message(F.text == "🛍 Оформить заказ")
@log_command
async def start_order(message: types.Message, state: FSMContext):
    await state.set_state(OrderStates.waiting_for_flight)
    await message.answer(
        "Выберите рейс доставки:",
        reply_markup=flight_kb()
    )

@router.callback_query(F.data.startswith("flight_"))
@log_callback
async def process_flight(callback: types.CallbackQuery, state: FSMContext):
    flight_map = {
        "flight_morning": "Утренний (11:00)",
        "flight_day": "Дневной (15:00)", 
        "flight_evening": "Вечерний (20:30)"
    }
    flight_type = flight_map[callback.data]
    
    await state.update_data(flight=flight_type)
    await state.set_state(OrderStates.waiting_for_address)
    
    logger.info(f"✈️ Выбран рейс: {flight_type}")
    await callback.message.edit_text(
        f"🛵 Выбран {flight_type} рейс\n"
        "📦 Теперь введите адрес доставки:"
    )
    await callback.answer()

@router.message(OrderStates.waiting_for_address)
@log_command
async def process_address(message: types.Message, state: FSMContext):
    logger.info(f"🏠 Введен адрес: {message.text}")
    await state.update_data(address=message.text)
    await state.set_state(OrderStates.waiting_for_name)
    await message.answer(
        "👤 Введите ваше имя:",
        reply_markup=cancel_kb()
    )

@router.message(OrderStates.waiting_for_name)
@log_command
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заказ":
        await state.clear()
        logger.warning("❌ Заказ отменен пользователем")
        await message.answer("Заказ отменен.", reply_markup=main_kb())
        return
        
    first_name = message.text.strip()
    if len(first_name) < 2:
        await message.answer("❌ Пожалуйста, введите корректное имя (минимум 2 символа):")
        return
    
    logger.info(f"👤 Введено имя: {first_name}")
    
    await state.update_data(first_name=first_name)
    await state.set_state(OrderStates.waiting_for_phone)
    
    await message.answer(
        "📱 Теперь введите ваш номер телефона или нажмите кнопку ниже, чтобы отправить номер из Telegram:",
        reply_markup=phone_kb()
    )

@router.message(OrderStates.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    """Обработка номера телефона из контакта Telegram"""
    phone_number = message.contact.phone_number
    logger.info(f"📱 Получен номер из контакта: {phone_number}")
    
    await state.update_data(phone_number=phone_number)
    await state.set_state(OrderStates.waiting_for_order_screenshot)
    
    await message.answer(
        "📸 Теперь отправьте скриншот вашего заказа из приложения KFC/Burger King:",
        reply_markup=cancel_kb()
    )

@router.message(OrderStates.waiting_for_phone, F.text)
async def process_phone_text(message: types.Message, state: FSMContext):
    """Обработка номера телефона введенного вручную"""
    if message.text == "❌ Отменить заказ":
        await state.clear()
        logger.warning("❌ Заказ отменен пользователем")
        await message.answer("Заказ отменен.", reply_markup=main_kb())
        return
    
    phone_number = message.text.strip()
    
    # Простая валидация номера телефона
    if not any(char.isdigit() for char in phone_number) or len(phone_number) < 5:
        await message.answer("❌ Пожалуйста, введите корректный номер телефона:")
        return
    
    logger.info(f"📱 Введен номер телефона: {phone_number}")
    
    await state.update_data(phone_number=phone_number)
    await state.set_state(OrderStates.waiting_for_order_screenshot)
    
    await message.answer(
        "📸 Теперь отправьте скриншот вашего заказа из приложения KFC/Вкусно и точка:",
        reply_markup=cancel_kb()
    )

@router.message(OrderStates.waiting_for_order_screenshot, F.photo)
async def process_order_screenshot(message: types.Message, state: FSMContext):
    screenshot_file_id = message.photo[-1].file_id
    
    logger.info(f"📸 Пользователь {message.from_user.id} отправил скриншот заказа")
    
    await state.update_data(order_screenshot=screenshot_file_id)
    await state.set_state(OrderStates.waiting_for_payment_screenshot)
    
    await message.answer(
        "💰 Теперь отправьте скриншот подтверждения оплаты (чека):",
        reply_markup=cancel_kb()
    )

@router.message(OrderStates.waiting_for_order_screenshot)
async def wrong_order_screenshot_input(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заказ":
        await state.clear()
        logger.warning("❌ Заказ отменен пользователем")
        await message.answer("Заказ отменен.", reply_markup=main_kb())
        return
        
    await message.answer("❌ Пожалуйста, отправьте скриншот заказа в виде изображения.")

@router.message(OrderStates.waiting_for_payment_screenshot, F.photo)
async def process_payment_screenshot(message: types.Message, state: FSMContext, session: AsyncSession):
    payment_screenshot_file_id = message.photo[-1].file_id
    
    logger.info(f"💰 Пользователь {message.from_user.id} отправил скриншот оплаты")
    
    await state.update_data(payment_screenshot=payment_screenshot_file_id)
    
    # Получаем все данные заказа
    order_data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Сохраняем заказ в базу данных
    try:
        order = await create_order(session, {
            'user_id': user_id,
            'username': username,
            'first_name': order_data['first_name'],
            'phone_number': order_data['phone_number'],
            'flight': order_data['flight'],
            'address': order_data['address'],
            'order_screenshot': order_data['order_screenshot'],
            'payment_screenshot': order_data['payment_screenshot'],
            'order_status': 'waiting_manager'
        })
        
        # Отправляем заказ менеджеру
        order_text = (
            "🍔 НОВЫЙ ЗАКАЗ!\n\n"
            f"📋 ID заказа: #{order.id}\n"
            f"🛵 Рейс: {order.flight}\n"
            f"🏠 Адрес: {order.address}\n"
            f"👤 Клиент: {order.first_name}\n"
            f"📞 Телефон: {order.phone_number}\n"
            f"📱 Username: @{order.username if order.username else 'не указан'}\n"
            f"🆔 User ID: {order.user_id}\n\n"
            f"📊 Статус заказа: Ожидает подтверждения"
        )
        
        try:
            # Отправляем текст заказа
            manager_message = await bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=order_text,
                reply_markup=manager_order_kb(order.id)
            )
            
            # Отправляем оба скриншота одним сообщением (медиагруппой)
            from aiogram.types import InputMediaPhoto
            
            media_group = [
                InputMediaPhoto(
                    media=order_data['order_screenshot'],
                    caption=f"📸 Скриншот заказа #{order.id}"
                ),
                InputMediaPhoto(
                    media=order_data['payment_screenshot'],
                    caption=f"💰 Скриншот оплаты #{order.id}"
                )
            ]
            
            await bot.send_media_group(
                chat_id=MANAGER_CHAT_ID,
                media=media_group,
                reply_to_message_id=manager_message.message_id
            )
            
            logger.info(f"👨‍💼 Заказ {order.id} отправлен менеджеру {MANAGER_CHAT_ID}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке заказа менеджеру: {e}")
            await bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=f"{order_text}\n\n❌ Ошибка при отправке скриншотов: {e}"
            )
        
        await message.answer(
            "✅ Заказ успешно оформлен!\n"
            "📸 Скриншоты получены и переданы менеджеру.\n"
            "⏳ Ожидайте подтверждения заказа и принятия его в работу.\n\n"
            "Вы можете отслеживать статус заказа через кнопку «📊 Статус заказа»",
            reply_markup=main_kb()
        )
        await state.clear()
        logger.info(f"🎉 Процесс заказа завершен для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении заказа для пользователя {user_id}: {e}")
        await message.answer("Произошла ошибка при сохранении заказа. Свяжитесь с поддержкой.")

@router.message(OrderStates.waiting_for_payment_screenshot)
async def wrong_payment_screenshot_input(message: types.Message, state: FSMContext):
    if message.text == "❌ Отменить заказ":
        await state.clear()
        logger.warning("❌ Заказ отменен пользователем")
        await message.answer("Заказ отменен.", reply_markup=main_kb())
        return
        
    await message.answer("❌ Пожалуйста, отправьте скриншот подтверждения оплаты в виде изображения.")
    