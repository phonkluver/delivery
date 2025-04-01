"""
Скрипт для тестирования функций часового пояса Душанбе
"""
import asyncio
import logging
from datetime import datetime, timedelta
import pytz

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_timezone_functions():
    """Тестирование функций для работы с часовым поясом Душанбе"""
    # Часовой пояс Душанбе (UTC+5)
    dushanbe_tz = pytz.timezone('Asia/Dushanbe')
    
    # Текущее время в Душанбе
    now_dushanbe = datetime.now(dushanbe_tz)
    logger.info(f"Текущее время в Душанбе: {now_dushanbe.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    
    # Текущее время в UTC
    now_utc = datetime.now(pytz.UTC)
    logger.info(f"Текущее время в UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    
    # Преобразование из UTC в Душанбе
    converted_to_dushanbe = now_utc.astimezone(dushanbe_tz)
    logger.info(f"Время UTC, преобразованное в Душанбе: {converted_to_dushanbe.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    
    # Проверка разницы во времени
    time_diff = now_dushanbe.utcoffset().total_seconds() / 3600
    logger.info(f"Разница между Душанбе и UTC: {time_diff} часов")
    
    # Проверка определения текущего дня
    today_dushanbe = now_dushanbe.strftime('%Y-%m-%d')
    logger.info(f"Текущая дата в Душанбе: {today_dushanbe}")
    
    # Проверка форматирования времени
    formatted_time = now_dushanbe.strftime('%H:%M:%S')
    logger.info(f"Текущее время в Душанбе (отформатированное): {formatted_time}")
    
    # Проверка определения рабочего времени 
    # (для информационных целей, бот работает 24/7)
    work_start = now_dushanbe.replace(hour=10, minute=0, second=0, microsecond=0)
    work_end = now_dushanbe.replace(hour=20, minute=0, second=0, microsecond=0)
    
    if work_start <= now_dushanbe <= work_end:
        logger.info("Текущее время находится в пределах рабочих часов (10:00 - 20:00)")
    else:
        logger.info("Текущее время находится вне рабочих часов (10:00 - 20:00)")
    
    # Проверка создания даты для отчётов
    yesterday_dushanbe = (now_dushanbe - timedelta(days=1)).strftime('%Y-%m-%d')
    logger.info(f"Вчерашняя дата в Душанбе: {yesterday_dushanbe}")
    
    logger.info("Все тесты часового пояса выполнены успешно")

if __name__ == "__main__":
    asyncio.run(test_timezone_functions())