"""
Time zone utilities for the Dushanbe time zone.
This module handles operations with the Dushanbe time zone (Asia/Dushanbe, UTC+5).
"""
import logging
from datetime import datetime, timezone, timedelta
import pytz

# Настройка логирования
logger = logging.getLogger(__name__)

# Определение часового пояса Душанбе (UTC+5)
DUSHANBE_TIMEZONE = pytz.timezone('Asia/Dushanbe')

# Рабочие часы (только для информационных сообщений)
WORK_HOURS_START = 10  # 10:00
WORK_HOURS_END = 20    # 20:00

def get_datetime_dushanbe():
    """Get current datetime in Dushanbe time zone"""
    return datetime.now(DUSHANBE_TIMEZONE)

def format_datetime_dushanbe(dt=None):
    """Format datetime in Dushanbe time zone as a string"""
    if dt is None:
        dt = get_datetime_dushanbe()
    
    # Format: YYYY-MM-DD HH:MM:SS
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_time_dushanbe():
    """Get current time in Dushanbe time zone (HH:MM:SS)"""
    return get_datetime_dushanbe().strftime('%H:%M:%S')

def get_date_dushanbe():
    """Get current date in Dushanbe time zone (YYYY-MM-DD)"""
    return get_datetime_dushanbe().strftime('%Y-%m-%d')

def is_working_hours():
    """
    Check if current time is within working hours.
    Note: Bot works 24/7, this is only for informational messages.
    """
    now = get_datetime_dushanbe()
    
    # Создаем объекты datetime для начала и конца рабочего дня
    work_start = now.replace(hour=WORK_HOURS_START, minute=0, second=0, microsecond=0)
    work_end = now.replace(hour=WORK_HOURS_END, minute=0, second=0, microsecond=0)
    
    return work_start <= now <= work_end

def get_working_hours_message():
    """Get a message with working hours information"""
    return f"Рабочие часы: с {WORK_HOURS_START}:00 до {WORK_HOURS_END}:00 (UTC+5, Душанбе)"

def get_datetime_from_string(date_str, time_str="00:00:00"):
    """
    Convert date and time strings to datetime in Dushanbe time zone
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        time_str: Time string in HH:MM:SS format, defaults to midnight
        
    Returns:
        Datetime object in Dushanbe time zone
    """
    try:
        # Combine date and time
        datetime_str = f"{date_str} {time_str}"
        
        # Parse the string as a naive datetime
        naive_dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        
        # Localize to Dushanbe timezone
        return DUSHANBE_TIMEZONE.localize(naive_dt)
    
    except ValueError as e:
        logger.error(f"Error parsing date/time: {e}")
        # Return current datetime as fallback
        return get_datetime_dushanbe()

def get_yesterday_date():
    """Get yesterday's date in YYYY-MM-DD format"""
    yesterday = get_datetime_dushanbe() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')

def get_next_working_hours():
    """
    Get a message about next working hours.
    Used for informational purposes when current time is outside working hours.
    """
    now = get_datetime_dushanbe()
    today = now.replace(hour=WORK_HOURS_START, minute=0, second=0, microsecond=0)
    tomorrow = (today + timedelta(days=1))
    
    if now.hour < WORK_HOURS_START:
        # Before working hours today
        next_time = today
        return f"Рабочий день начнется сегодня в {WORK_HOURS_START}:00."
    else:
        # After working hours, next working day
        next_time = tomorrow
        return f"Следующий рабочий день начнется завтра в {WORK_HOURS_START}:00."