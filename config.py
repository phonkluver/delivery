"""
Configuration settings for the Telegram bot.
This module contains all the configuration settings for the bot.
"""
import os

# Bot token from BotFather
BOT_TOKEN = "7733149772:AAGxMVIpiTgGO0TzdbBDiciCX7fsCAu5Q-A"

# Admin chat IDs - only add admin accounts here
ADMIN_CHAT_IDS = [
    5244740812,
    7387421563
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

def add_user_to_whitelist(user_id):
    """Utility function to add a user ID to the whitelist"""
    import json
    import os
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(WHITELIST_FILE), exist_ok=True)
    
    # Create or load the whitelist file
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
            try:
                whitelist = json.load(f)
            except json.JSONDecodeError:
                whitelist = {"authorized_users": list(ADMIN_CHAT_IDS)}
    else:
        whitelist = {"authorized_users": list(ADMIN_CHAT_IDS)}
    
    # Add the user if not already in the list
    if user_id not in whitelist["authorized_users"]:
        whitelist["authorized_users"].append(user_id)
        
        # Save the updated whitelist
        with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(whitelist, f, indent=2, ensure_ascii=False)
        
        return True
    return False
