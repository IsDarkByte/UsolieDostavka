from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Оформить заказ")],
            [KeyboardButton(text="📊 Статус заказа")]
        ],
        resize_keyboard=True
    )

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить заказ")]],
        resize_keyboard=True
    )