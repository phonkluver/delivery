"""
Bot initialization and registration of handlers.
This module sets up the bot instance and registers all the handlers.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ADMIN_CHAT_IDS
from handlers import common, admin, shop, courier
from storage.database import init_database, init_whitelist

logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    """Set bot commands in the menu"""
    # Команды для всех пользователей
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Получить помощь"),
        BotCommand(command="register", description="Зарегистрировать роль"),
        BotCommand(command="cancel", description="Отменить текущую операцию"),
    ]
    await bot.set_my_commands(commands)
    
    # Дополнительные команды для администраторов
    admin_commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Получить помощь"),
        BotCommand(command="register", description="Зарегистрировать роль"),
        BotCommand(command="cancel", description="Отменить текущую операцию"),
        BotCommand(command="whitelist_add", description="Добавить пользователя в белый список"),
        BotCommand(command="whitelist_list", description="Показать пользователей в белом списке"),
        BotCommand(command="whitelist_remove", description="Удалить пользователя из белого списка"),
        BotCommand(command="export_orders", description="Экспортировать заказы в Excel"),
    ]
    
    # Устанавливаем команды для каждого администратора
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await bot.set_my_commands(admin_commands, scope={"type": "chat", "chat_id": admin_id})
        except Exception as e:
            logger.error(f"Failed to set admin commands for {admin_id}: {e}")


async def start_bot():
    """Initialize and start the bot"""
    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Initialize database and whitelist
    await init_database()
    await init_whitelist()
    
    # Register handlers
    common.register_handlers(dp)
    admin.register_handlers(dp)
    shop.register_handlers(dp)
    courier.register_handlers(dp)
    
    # Set default commands
    await set_commands(bot)
    
    try:
        logger.info("Starting bot...")
        # Start polling
        await dp.start_polling(bot, skip_updates=True)
    finally:
        logger.info("Bot stopped!")
