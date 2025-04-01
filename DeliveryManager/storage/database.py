"""
Database operations for the bot.
This module handles all data storage and retrieval operations.
"""
import json
import logging
import os
import asyncio
from typing import List, Dict, Any, Optional, Union
from utils.timezone import format_datetime_dushanbe, get_date_dushanbe
import pandas as pd

from config import (
    DATABASE_FILE, ROLE_ADMIN, ROLE_SHOP, ROLE_COURIER,
    WHITELIST_FILE, WHITELISTED_USERS
)

logger = logging.getLogger(__name__)

# Lock for thread-safe database operations
db_lock = asyncio.Lock()


async def init_database():
    """Initialize the database file if it doesn't exist"""
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    
    if not os.path.exists(DATABASE_FILE):
        # Create empty database structure
        initial_data = {
            "users": [],
            "orders": [],
            "next_order_id": 1
        }
        async with db_lock:
            with open(DATABASE_FILE, 'w') as f:
                json.dump(initial_data, f, indent=2)
        
        logger.info(f"Created new database file at {DATABASE_FILE}")


async def _read_database() -> Dict[str, Any]:
    """Read the database file and return its contents"""
    try:
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error reading database: {e}")
        # Return empty database structure
        return {"users": [], "orders": [], "next_order_id": 1}


async def _write_database(data: Dict[str, Any]):
    """Write data to the database file"""
    try:
        with open(DATABASE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error writing to database: {e}")
        raise


async def get_user_role(user_id: int) -> Optional[str]:
    """Get the role of a user by ID"""
    db = await _read_database()
    
    for user in db["users"]:
        if user["id"] == user_id:
            return user["role"]
    
    return None


async def register_user(user_id: int, username: str, role: str) -> bool:
    """Register a new user or update an existing user"""
    if role not in [ROLE_ADMIN, ROLE_SHOP, ROLE_COURIER]:
        logger.error(f"Invalid role: {role}")
        return False
    
    async with db_lock:
        db = await _read_database()
        
        # Check if user already exists
        for user in db["users"]:
            if user["id"] == user_id:
                # Update existing user
                user["username"] = username
                user["role"] = role
                await _write_database(db)
                return True
        
        # Add new user
        db["users"].append({
            "id": user_id,
            "username": username,
            "role": role,
            "registered_at": format_datetime_dushanbe()
        })
        
        await _write_database(db)
        return True


async def create_order(
    shop_id: int, 
    customer_phone: str, 
    city: str, 
    shop_name: str, 
    delivery_address: str,
    payment_amount: float = 0
) -> int:
    """Create a new order and return its ID"""
    async with db_lock:
        db = await _read_database()
        
        order_id = db["next_order_id"]
        db["next_order_id"] += 1
        
        # Create new order
        db["orders"].append({
            "id": order_id,
            "shop_id": shop_id,
            "shop_name": shop_name,
            "customer_phone": customer_phone,
            "city": city,
            "delivery_address": delivery_address,
            "payment_amount": payment_amount,
            "status": "pending",
            "created_at": format_datetime_dushanbe()
        })
        
        await _write_database(db)
        return order_id


async def get_pending_orders() -> List[Dict[str, Any]]:
    """Get all pending orders"""
    db = await _read_database()
    return [order for order in db["orders"] if order["status"] == "pending"]


async def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
    """Get an order by its ID"""
    db = await _read_database()
    
    for order in db["orders"]:
        if order["id"] == order_id:
            return order
    
    return None


async def get_couriers() -> List[Dict[str, Any]]:
    """Get all registered couriers"""
    db = await _read_database()
    return [user for user in db["users"] if user["role"] == ROLE_COURIER]


async def assign_order_to_courier(order_id: int, courier_id: int, courier_name: str) -> bool:
    """Assign an order to a courier"""
    async with db_lock:
        db = await _read_database()
        
        # Find the order
        for order in db["orders"]:
            if order["id"] == order_id:
                # Update order status and courier info
                order["status"] = "assigned"
                order["courier_id"] = courier_id
                order["courier_name"] = courier_name
                order["assigned_at"] = format_datetime_dushanbe()
                
                await _write_database(db)
                return True
        
        return False


async def mark_order_as_delivered(order_id: int, delivered_at: str = None) -> bool:
    """Mark an order as delivered"""
    if not delivered_at:
        delivered_at = format_datetime_dushanbe()
    
    async with db_lock:
        db = await _read_database()
        
        # Find the order
        for order in db["orders"]:
            if order["id"] == order_id:
                # Update order status
                order["status"] = "delivered"
                order["delivered_at"] = delivered_at
                
                await _write_database(db)
                return True
        
        return False


async def get_shop_orders(shop_id: int) -> List[Dict[str, Any]]:
    """Get all orders for a shop"""
    db = await _read_database()
    return [order for order in db["orders"] if order["shop_id"] == shop_id]


async def get_courier_orders(courier_id: int) -> List[Dict[str, Any]]:
    """Get all orders assigned to a courier"""
    db = await _read_database()
    return [
        order for order in db["orders"] 
        if order.get("courier_id") == courier_id and order["status"] in ["assigned", "delivered"]
    ]


async def get_all_orders() -> List[Dict[str, Any]]:
    """Get all orders in the database"""
    db = await _read_database()
    return db["orders"]


async def get_delivered_orders_in_timeframe(date_str: str) -> List[Dict[str, Any]]:
    """Get all orders delivered on a specific date"""
    db = await _read_database()
    
    # Filter orders by delivery date
    return [
        order for order in db["orders"]
        if (order["status"] == "delivered" and 
            order.get("delivered_at", "").startswith(date_str))
    ]


async def get_all_users() -> List[Dict[str, Any]]:
    """Get all registered users"""
    db = await _read_database()
    return db["users"]


async def get_all_shops() -> List[Dict[str, Any]]:
    """Get all registered shops"""
    db = await _read_database()
    return [user for user in db["users"] if user["role"] == ROLE_SHOP]


async def get_all_couriers() -> List[Dict[str, Any]]:
    """Get all registered couriers"""
    db = await _read_database()
    return [user for user in db["users"] if user["role"] == ROLE_COURIER]


async def delete_user(user_id: int) -> bool:
    """Delete a user"""
    async with db_lock:
        db = await _read_database()
        
        # Ищем пользователя в списке
        for i, user in enumerate(db["users"]):
            if user["id"] == user_id:
                # Удаляем пользователя
                del db["users"][i]
                await _write_database(db)
                return True
                
        return False


async def check_user_has_orders(user_id: int) -> bool:
    """Check if a user has any orders (as shop or courier)"""
    db = await _read_database()
    
    # Проверяем заказы, где пользователь выступает как магазин
    for order in db["orders"]:
        if order["shop_id"] == user_id:
            return True
            
        # Проверяем заказы, где пользователь выступает как курьер
        if order.get("courier_id") == user_id:
            return True
            
    return False


# Функции для работы с белым списком
async def init_whitelist():
    """Инициализация файла белого списка, если он не существует"""
    os.makedirs(os.path.dirname(WHITELIST_FILE), exist_ok=True)
    
    if not os.path.exists(WHITELIST_FILE):
        # Создаем начальный белый список, включающий администраторов
        whitelist_data = {
            "users": [{"id": user_id, "added_at": format_datetime_dushanbe()} 
                      for user_id in WHITELISTED_USERS]
        }
        with open(WHITELIST_FILE, 'w') as f:
            json.dump(whitelist_data, f, indent=2)
        
        logger.info(f"Создан новый файл белого списка: {WHITELIST_FILE}")


async def get_authorized_users() -> List[int]:
    """Получение списка авторизованных пользователей из файла"""
    try:
        # Проверяем существование файла
        if not os.path.exists(WHITELIST_FILE):
            await init_whitelist()
            
        with open(WHITELIST_FILE, 'r') as f:
            data = json.load(f)
            return [user["id"] for user in data.get("users", [])]
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Ошибка чтения файла белого списка: {e}")
        # Возвращаем только администраторов в случае ошибки
        return WHITELISTED_USERS.copy()


async def add_authorized_user(user_id: int) -> bool:
    """Добавление пользователя в белый список"""
    try:
        # Убеждаемся, что ID пользователя целочисленный
        user_id = int(user_id)
        
        # Проверяем существование файла
        if not os.path.exists(WHITELIST_FILE):
            await init_whitelist()
        
        # Читаем текущий белый список
        with open(WHITELIST_FILE, 'r') as f:
            data = json.load(f)
        
        # Проверяем, есть ли пользователь уже в списке
        user_ids = [user["id"] for user in data.get("users", [])]
        if user_id in user_ids:
            return True  # Пользователь уже в списке
        
        # Добавляем пользователя в список
        data.setdefault("users", []).append({
            "id": user_id,
            "added_at": format_datetime_dushanbe()
        })
        
        # Записываем обновленный список
        with open(WHITELIST_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Обновляем глобальный список в памяти
        if user_id not in WHITELISTED_USERS:
            WHITELISTED_USERS.append(user_id)
            
        return True
    except Exception as e:
        logger.error(f"Ошибка добавления пользователя в белый список: {e}")
        return False


async def remove_authorized_user(user_id: int) -> bool:
    """Удаление пользователя из белого списка"""
    try:
        # Убеждаемся, что ID пользователя целочисленный
        user_id = int(user_id)
        
        # Проверяем существование файла
        if not os.path.exists(WHITELIST_FILE):
            await init_whitelist()
            return False  # Если файл не существовал, значит пользователя в нем нет
        
        # Читаем текущий белый список
        with open(WHITELIST_FILE, 'r') as f:
            data = json.load(f)
        
        # Ищем пользователя в списке
        users = data.get("users", [])
        for i, user in enumerate(users):
            if user["id"] == user_id:
                # Удаляем пользователя из списка
                del users[i]
                # Записываем обновленный список
                with open(WHITELIST_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                
                # Удаляем из глобального списка в памяти
                if user_id in WHITELISTED_USERS:
                    WHITELISTED_USERS.remove(user_id)
                
                return True
        
        return False  # Пользователь не найден
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя из белого списка: {e}")
        return False


# Функции для экспорта заказов в Excel
async def export_orders_to_excel(orders: List[Dict], filename: str = None) -> str:
    """
    Экспорт заказов в Excel файл
    
    Args:
        orders: Список заказов для экспорта
        filename: Имя файла (если не указано, генерируется автоматически)
        
    Returns:
        Путь к созданному файлу
    """
    try:
        # Если имя файла не указано, генерируем его с текущей датой
        if not filename:
            current_date = get_date_dushanbe()
            filename = f"orders_report_{current_date}.xlsx"
        
        # Создаем директорию reports, если она не существует
        os.makedirs("reports", exist_ok=True)
        
        # Полный путь к файлу
        filepath = os.path.join("reports", filename)
        
        # Готовим данные для DataFrame
        # Преобразуем и упрощаем структуру для экспорта
        export_data = []
        for order in orders:
            export_order = {
                "№ заказа": order["id"],
                "Статус": order["status"],
                "Магазин": order.get("shop_name", "Н/Д"),
                "Город": order.get("city", "Н/Д"),
                "Адрес доставки": order.get("delivery_address", "Н/Д"),
                "Телефон клиента": order.get("customer_phone", "Н/Д"),
                "Сумма оплаты": order.get("payment_amount", 0),
                "Курьер": order.get("courier_name", "Не назначен"),
                "Создан": order.get("created_at", "Н/Д"),
                "Назначен": order.get("assigned_at", "Н/Д"),
                "Доставлен": order.get("delivered_at", "Н/Д")
            }
            export_data.append(export_order)
        
        # Создаем DataFrame
        df = pd.DataFrame(export_data)
        
        # Экспортируем в Excel
        df.to_excel(filepath, index=False, engine="openpyxl")
        
        logger.info(f"Отчет успешно экспортирован в {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Ошибка экспорта отчета в Excel: {e}")
        raise
