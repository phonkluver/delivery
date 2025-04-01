"""
Скрипт для полной очистки данных бота.
Удаляет все существующие заказы и пользователей и создает новую пустую структуру базы данных.
"""
import json
import os
import logging
import asyncio
import sys

from config import DATABASE_FILE, WHITELIST_FILE, ADMIN_CHAT_IDS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def clear_database():
    """Очистить базу данных и создать новую структуру"""
    logger.info("Начинаем очистку базы данных...")
    
    # Создаем директорию для файлов базы данных, если она не существует
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    
    # Создаем новую пустую структуру базы данных
    initial_data = {
        "users": [],
        "orders": [],
        "next_order_id": 1
    }
    
    # Записываем новую структуру в файл
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"База данных очищена. Создана новая структура в {DATABASE_FILE}")

async def reset_whitelist():
    """Сбросить белый список, оставив только администраторов"""
    logger.info("Начинаем сброс белого списка...")
    
    # Создаем директорию для файлов базы данных, если она не существует
    os.makedirs(os.path.dirname(WHITELIST_FILE), exist_ok=True)
    
    # Сохраняем только администраторов в белом списке
    whitelist_data = {
        "authorized_users": list(ADMIN_CHAT_IDS)
    }
    
    # Записываем новый белый список в файл
    with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(whitelist_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Белый список сброшен. В нем остались только администраторы: {ADMIN_CHAT_IDS}")

async def main():
    """Основная функция скрипта"""
    print("\n" + "=" * 60)
    print("ОЧИСТКА ДАННЫХ БОТА TUKTUK")
    print("=" * 60 + "\n")
    
    confirmation = input("Вы уверены, что хотите удалить ВСЕ данные бота? (y/n): ")
    
    if confirmation.lower() != 'y':
        print("Операция отменена.")
        return
    
    try:
        await clear_database()
        await reset_whitelist()
        
        print("\n" + "=" * 60)
        print("ОЧИСТКА ДАННЫХ ЗАВЕРШЕНА УСПЕШНО!")
        print(f"- База данных сброшена: {DATABASE_FILE}")
        print(f"- Белый список сброшен: {WHITELIST_FILE}")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Произошла ошибка при очистке данных: {e}")
        print(f"\nОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())