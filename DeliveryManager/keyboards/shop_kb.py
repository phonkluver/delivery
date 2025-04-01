"""
Keyboard layouts for shop users.
This module contains functions to create shop keyboard layouts.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def get_shop_main_keyboard():
    """Create main keyboard for shops"""
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📦 Новый заказ"), KeyboardButton(text="📋 Мои заказы")],
        [KeyboardButton(text="❓ Помощь")]
    ], resize_keyboard=True)
    return keyboard
