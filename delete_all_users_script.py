"""
Скрипт для принудительного удаления всех пользователей из базы данных, кроме администраторов.
Запускается без подтверждения для использования в автоматическом режиме.
"""
import json
import os
import logging
import asyncio
import sys

from config import DATABASE_FILE, ROLE_ADMIN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def delete_all_users_except_admin():
    """Удалить всех пользователей, кроме администраторов"""
    logger.info("Начинаем удаление пользователей...")
    
    if not os.path.exists(DATABASE_FILE):
        logger.error(f"Файл базы данных не найден: {DATABASE_FILE}")
        return False
    
    try:
        # Чтение базы данных
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Количество пользователей до очистки
        users_before = len(data.get("users", []))
        
        # Фильтрация пользователей, оставляем только администраторов
        data["users"] = [user for user in data.get("users", []) if user.get("role") == ROLE_ADMIN]
        
        # Количество пользователей после очистки
        users_after = len(data["users"])
        
        # Запись обновленных данных
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Удалено {users_before - users_after} пользователей. Оставлено {users_after} администраторов.")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при удалении пользователей: {e}")
        return False

async def clear_orders():
    """Удалить все заказы из базы данных"""
    logger.info("Начинаем удаление заказов...")
    
    if not os.path.exists(DATABASE_FILE):
        logger.error(f"Файл базы данных не найден: {DATABASE_FILE}")
        return False
    
    try:
        # Чтение базы данных
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Количество заказов до очистки
        orders_before = len(data.get("orders", []))
        
        # Очистка списка заказов
        data["orders"] = []
        
        # Запись обновленных данных
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Удалено {orders_before} заказов.")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при удалении заказов: {e}")
        return False

async def main():
    """Основная функция скрипта"""
    print("\n" + "=" * 60)
    print("ПРИНУДИТЕЛЬНОЕ УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ И ЗАКАЗОВ БОТА TUKTUK")
    print("=" * 60 + "\n")
    
    # Удаляем пользователей без запроса подтверждения
    try:
        result_users = await delete_all_users_except_admin()
        result_orders = await clear_orders()
        
        if result_users and result_orders:
            print("\n" + "=" * 60)
            print("УДАЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("Все пользователи (кроме администраторов) и заказы были удалены.")
            print("=" * 60 + "\n")
        else:
            print("\nПроизошла ошибка при удалении данных.")
        
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        print(f"\nОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())