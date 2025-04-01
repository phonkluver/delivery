"""
Keyboard layouts for admin users.
This module contains functions to create admin keyboard layouts.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


async def get_admin_main_keyboard():
    """Create main keyboard for administrators"""
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Список заказов"), KeyboardButton(text="📮 Назначить заказ")],
        [KeyboardButton(text="👥 Управление курьерами"), KeyboardButton(text="🏪 Управление магазинами")],
        [KeyboardButton(text="📊 Отчет"), KeyboardButton(text="❓ Помощь")]
    ], resize_keyboard=True)
    return keyboard


async def get_couriers_keyboard(couriers):
    """Create keyboard with courier selection options"""
    buttons = []
    
    # Add buttons for each courier
    for courier in couriers:
        courier_id = courier['id']
        courier_full_info = courier['username']
        
        # Разделяем имя и телефон курьера (формат: "Имя | Телефон")
        courier_info = courier_full_info.split(" | ")
        courier_name = courier_info[0] if len(courier_info) > 0 else "Неизвестно"
        courier_phone = courier_info[1] if len(courier_info) > 1 else ""
        
        # Формируем текст кнопки
        button_text = f"{courier_name}"
        if courier_phone:
            button_text += f" ({courier_phone})"
        button_text += f": {courier_id}"
        
        buttons.append([KeyboardButton(text=button_text)])
    
    # Add cancel button
    buttons.append([KeyboardButton(text="❌ Отмена")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


async def get_courier_management_keyboard():
    """Create keyboard for courier management"""
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Список курьеров"), KeyboardButton(text="🗑️ Удалить курьера")],
        [KeyboardButton(text="⬅️ Назад в главное меню")]
    ], resize_keyboard=True)
    return keyboard


async def get_shop_management_keyboard():
    """Create keyboard for shop management"""
    keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Список магазинов"), KeyboardButton(text="🗑️ Удалить магазин")],
        [KeyboardButton(text="⬅️ Назад в главное меню")]
    ], resize_keyboard=True)
    return keyboard


async def get_couriers_list_keyboard(couriers):
    """Create keyboard with courier list for deletion"""
    buttons = []
    
    # Add buttons for each courier
    for courier in couriers:
        courier_id = courier['id']
        courier_full_info = courier['username']
        
        # Разделяем имя и телефон курьера (формат: "Имя | Телефон")
        courier_info = courier_full_info.split(" | ")
        courier_name = courier_info[0] if len(courier_info) > 0 else "Неизвестно"
        courier_phone = courier_info[1] if len(courier_info) > 1 else ""
        
        # Формируем текст кнопки
        button_text = f"❌ {courier_name}"
        if courier_phone:
            button_text += f" ({courier_phone})"
        button_text += f" (ID: {courier_id})"
        
        buttons.append([KeyboardButton(text=button_text)])
    
    # Add back button
    buttons.append([KeyboardButton(text="⬅️ Назад")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


async def get_shops_list_keyboard(shops):
    """Create keyboard with shop list for deletion"""
    buttons = []
    
    # Add buttons for each shop
    for shop in shops:
        shop_id = shop['id']
        shop_full_info = shop['username']
        
        # Разделяем название и телефон магазина (формат: "Название | Телефон")
        shop_info = shop_full_info.split(" | ")
        shop_name = shop_info[0] if len(shop_info) > 0 else "Неизвестно"
        shop_phone = shop_info[1] if len(shop_info) > 1 else ""
        
        # Формируем текст кнопки
        button_text = f"❌ {shop_name}"
        if shop_phone:
            button_text += f" ({shop_phone})"
        button_text += f" (ID: {shop_id})"
        
        buttons.append([KeyboardButton(text=button_text)])
    
    # Add back button
    buttons.append([KeyboardButton(text="⬅️ Назад")])
    
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard
