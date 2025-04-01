"""
Main entry point for the Telegram delivery bot.
This script initializes the bot and starts polling for updates.
"""
import asyncio
import logging

from bot import start_bot


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Start the bot
    asyncio.run(start_bot())
