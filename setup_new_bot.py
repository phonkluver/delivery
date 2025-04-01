"""
Скрипт для настройки нового экземпляра бота TUKTUK.
Этот скрипт настраивает необходимую структуру файлов и базы данных,
добавляет администратора в белый список и проверяет конфигурацию.
"""
import json
import os
import logging
import asyncio
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def setup_config():
    """Проверка и настройка конфигурации бота"""
    try:
        # Импортируем только после проверки наличия config.py
        from config import BOT_TOKEN, ADMIN_CHAT_IDS, DATABASE_FILE, WHITELIST_FILE
        
        if not BOT_TOKEN or BOT_TOKEN == "YOUR_TOKEN_HERE":
            logger.error("Токен бота не настроен в config.py")
            return False
        
        if not ADMIN_CHAT_IDS:
            logger.error("Не указаны ID администраторов в config.py")
            return False
        
        logger.info(f"Конфигурация проверена. Найдены ID администраторов: {ADMIN_CHAT_IDS}")
        return True
        
    except ImportError:
        logger.error("Файл config.py не найден. Пожалуйста, создайте его на основе шаблона.")
        return False
    except AttributeError as e:
        logger.error(f"Ошибка в конфигурации бота: {e}")
        return False

async def create_database_structure():
    """Создание структуры базы данных"""
    from config import DATABASE_FILE
    
    # Создаем директорию для базы данных, если она не существует
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    
    # Проверяем, существует ли файл базы данных
    if os.path.exists(DATABASE_FILE):
        logger.info(f"Файл базы данных уже существует: {DATABASE_FILE}")
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                logger.info(f"Структура базы данных: {list(data.keys())}")
            except json.JSONDecodeError:
                logger.error("Файл базы данных поврежден. Создаем новый.")
                await create_new_database()
    else:
        await create_new_database()
    
    return True

async def create_new_database():
    """Создание новой базы данных с пустой структурой"""
    from config import DATABASE_FILE
    
    # Создаем пустую структуру базы данных
    initial_data = {
        "users": [],
        "orders": [],
        "next_order_id": 1
    }
    
    # Записываем структуру в файл
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Создана новая база данных: {DATABASE_FILE}")

async def setup_whitelist():
    """Настройка белого списка пользователей"""
    from config import WHITELIST_FILE, ADMIN_CHAT_IDS
    
    # Создаем директорию для файла белого списка, если она не существует
    os.makedirs(os.path.dirname(WHITELIST_FILE), exist_ok=True)
    
    # Проверяем, существует ли файл белого списка
    if os.path.exists(WHITELIST_FILE):
        logger.info(f"Файл белого списка уже существует: {WHITELIST_FILE}")
        
        # Проверяем содержимое белого списка
        with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if "authorized_users" not in data:
                    raise ValueError("Неверная структура белого списка")
                
                # Проверяем, что все администраторы в белом списке
                admin_ids_in_whitelist = all(admin_id in data["authorized_users"] for admin_id in ADMIN_CHAT_IDS)
                
                if not admin_ids_in_whitelist:
                    logger.info("Не все администраторы в белом списке. Добавляем...")
                    await update_whitelist()
                else:
                    logger.info("Все администраторы уже в белом списке.")
            
            except (json.JSONDecodeError, ValueError):
                logger.error("Файл белого списка поврежден. Создаем новый.")
                await create_new_whitelist()
    else:
        await create_new_whitelist()
    
    return True

async def create_new_whitelist():
    """Создание нового белого списка с администраторами"""
    from config import WHITELIST_FILE, ADMIN_CHAT_IDS
    
    # Создаем белый список с администраторами
    whitelist_data = {
        "authorized_users": list(ADMIN_CHAT_IDS)
    }
    
    # Записываем белый список в файл
    with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(whitelist_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Создан новый белый список с администраторами: {ADMIN_CHAT_IDS}")

async def update_whitelist():
    """Обновление белого списка с добавлением всех администраторов"""
    from config import WHITELIST_FILE, ADMIN_CHAT_IDS
    
    # Читаем текущий белый список
    with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Добавляем всех администраторов
    for admin_id in ADMIN_CHAT_IDS:
        if admin_id not in data["authorized_users"]:
            data["authorized_users"].append(admin_id)
    
    # Записываем обновленный белый список
    with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Белый список обновлен. Администраторы: {ADMIN_CHAT_IDS}")

async def main():
    """Основная функция скрипта"""
    print("\n" + "=" * 60)
    print("НАСТРОЙКА НОВОГО ЭКЗЕМПЛЯРА БОТА TUKTUK")
    print("=" * 60 + "\n")
    
    try:
        # Проверяем конфигурацию
        if not await setup_config():
            print("\nНастройка не выполнена из-за ошибок в конфигурации.")
            return
        
        # Создаем структуру базы данных
        await create_database_structure()
        
        # Настраиваем белый список
        await setup_whitelist()
        
        print("\n" + "=" * 60)
        print("НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
        print("Теперь вы можете запустить бота с помощью команды:")
        print("python main.py")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Произошла ошибка при настройке бота: {e}")
        print(f"\nОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())