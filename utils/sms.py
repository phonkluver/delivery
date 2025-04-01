"""
SMS notification utilities.
Этот модуль отключен, так как все уведомления отправляются через Telegram.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def send_sms_notification(to_phone: str, message_text: str) -> Dict[str, Any]:
    """
    Заглушка функции отправки SMS-уведомлений.
    В этой версии приложения все уведомления отправляются через Telegram.
    
    Args:
        to_phone: Recipient phone number (must be in E.164 format)
        message_text: SMS message text
        
    Returns:
        Dictionary with status information:
        {
            "success": bool,
            "message": str,
            "sid": Optional[str]
        }
    """
    logger.info(f"SMS notification not sent (disabled): To: {to_phone}, Message: {message_text}")
    
    # Return a success status since this is intentionally disabled
    return {
        "success": True,
        "message": "SMS notifications are disabled. Notification sent via Telegram instead.",
        "sid": None
    }

async def format_delivery_notification(order_data: Dict[str, Any]) -> str:
    """
    Заглушка функции форматирования SMS-уведомления о доставке.
    В этой версии приложения все уведомления отправляются через Telegram.
    
    Args:
        order_data: Order data dictionary
        
    Returns:
        Formatted SMS message
    """
    # Формирование сообщения о назначении заказа
    shop_name = order_data.get("shop_name", "")
    order_id = order_data.get("order_id", "")
    address = order_data.get("delivery_address", "")
    city = order_data.get("city", "")
    
    message = (
        f"TUKTUK Доставка: Заказ #{order_id} от {shop_name} "
        f"назначен для доставки по адресу: {city}, {address}. "
        f"Посмотрите детали в боте."
    )
    
    return message

async def format_delivery_confirmation(order_data: Dict[str, Any]) -> str:
    """
    Заглушка функции форматирования SMS-уведомления о подтверждении доставки.
    В этой версии приложения все уведомления отправляются через Telegram.
    
    Args:
        order_data: Order data dictionary
        
    Returns:
        Formatted SMS message
    """
    # Формирование сообщения о подтверждении доставки
    order_id = order_data.get("order_id", "")
    delivered_at = order_data.get("delivered_at", "неизвестное время")
    courier_name = order_data.get("courier_name", "")
    
    message = (
        f"TUKTUK Доставка: Заказ #{order_id} доставлен в {delivered_at} "
        f"курьером {courier_name}. Спасибо!"
    )
    
    return message