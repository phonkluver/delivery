"""
Скрипт для очистки белого списка, оставляя только администраторов.
"""
import json
import os
import logging
import asyncio
import sys

from config import WHITELIST_FILE, ADMIN_CHAT_IDS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def clear_whitelist():
    """Очистить белый список, оставив только администраторов"""
    logger.info("Начинаем очистку белого списка...")
    
    if not os.path.exists(WHITELIST_FILE):
        logger.error(f"Файл белого списка не найден: {WHITELIST_FILE}")
        return False
    
    try:
        # Чтение текущего белого списка
        with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Сохраняем количество пользователей до очистки
        users_before = len(data.get("authorized_users", []))
        
        # Создаем новый белый список только с администраторами
        data["authorized_users"] = list(ADMIN_CHAT_IDS)
        
        # Записываем обновленный белый список
        with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Сохраняем количество пользователей после очистки
        users_after = len(data["authorized_users"])
        
        logger.info(f"Очищено {users_before - users_after} пользователей из белого списка. Оставлено {users_after} администраторов.")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при очистке белого списка: {e}")
        return False

async def main():
    """Основная функция скрипта"""
    print("\n" + "=" * 60)
    print("ОЧИСТКА БЕЛОГО СПИСКА БОТА TUKTUK")
    print("=" * 60 + "\n")
    
    confirmation = input("Вы уверены, что хотите очистить белый список, оставив только администраторов? (y/n): ")
    
    if confirmation.lower() != 'y':
        print("Операция отменена.")
        return
    
    try:
        result = await clear_whitelist()
        
        if result:
            print("\n" + "=" * 60)
            print("ОЧИСТКА БЕЛОГО СПИСКА ЗАВЕРШЕНА УСПЕШНО!")
            print(f"В белом списке остались только администраторы: {ADMIN_CHAT_IDS}")
            print("=" * 60 + "\n")
        else:
            print("\nПроизошла ошибка при очистке белого списка.")
        
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        print(f"\nОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())