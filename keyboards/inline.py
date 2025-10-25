from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def flight_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Утренний (11:00)", callback_data="flight_morning"))
    builder.add(InlineKeyboardButton(text="Дневной (15:00)", callback_data="flight_day"))
    builder.add(InlineKeyboardButton(text="Вечерний (20:30)", callback_data="flight_evening"))
    return builder.as_markup()

def manager_order_kb(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"manager_verify_payment_{order_id}"))
    builder.add(InlineKeyboardButton(text="❌ Отклонить оплату", callback_data=f"manager_reject_payment_{order_id}"))
    builder.add(InlineKeyboardButton(text="🚗 Принять в доставку", callback_data=f"manager_accept_{order_id}"))
    return builder.as_markup()

def manager_delivery_kb(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚗 В доставке", callback_data=f"manager_delivery_{order_id}"))
    builder.add(InlineKeyboardButton(text="✅ Доставлен", callback_data=f"manager_delivered_{order_id}"))
    return builder.as_markup()