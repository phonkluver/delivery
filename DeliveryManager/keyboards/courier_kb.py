"""
Keyboard layouts for courier users.
This module contains functions to create courier keyboard layouts.
"""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def get_courier_main_keyboard():
    """Create main keyboard for couriers"""
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚚 Мои доставки")],
        [KeyboardButton(text="❓ Помощь")]
    ], resize_keyboard=True)
    return keyboard


async def get_delivery_confirmation_keyboard(order_id):
    """Create inline keyboard for delivery confirmation"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Доставлено", 
            callback_data=f"delivery:confirm:{order_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💬 Добавить комментарий", 
            callback_data=f"delivery:comment:{order_id}"
        )
    )
    return builder.as_markup()
