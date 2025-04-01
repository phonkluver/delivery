"""
Configuration settings for the Telegram bot.
This module contains all the configuration settings for the bot.
"""
import os

# Bot token from BotFather (Required)
BOT_TOKEN = "7733149772:AAGxMVIpiTgGO0TzdbBDiciCX7fsCAu5Q-A"  # Replace with your actual token

# Admin chat IDs (Required)
ADMIN_CHAT_IDS = [
    123456789,  # Replace with your actual admin IDs
    # 987654321,  # Uncomment and add more admin IDs as needed
]

# User roles
ROLE_ADMIN = "admin"
ROLE_SHOP = "shop"
ROLE_COURIER = "courier"

# Database file path
DATABASE_FILE = "storage/data.json"

# Whitelist configuration
USE_WHITELIST = True  # Set to False to disable whitelist
WHITELIST_FILE = "storage/whitelist.json"

# Default whitelisted users (always allowed, even if whitelist is enabled)
WHITELISTED_USERS = list(ADMIN_CHAT_IDS)  # Admin IDs are always whitelisted

# Report export directory
REPORT_EXPORT_DIR = "reports"