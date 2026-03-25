#!/usr/bin/env python3
# Telegram Order Query Bot - Main Program
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import BOT_TOKEN, LOG_LEVEL
from database import init_database
from handlers import (
    start_command,
    check_command,
    help_command,
    add_test_order_command,
    process_order_message,
    forward_reply_message,
    set_forward_rule_command,
    list_forward_rules_command
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Error handler"""
    logger.error(f"Update {update} caused error: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred while processing the message. Please try again later or contact admin."
        )


def main():
    """Main function"""
    # Check Token
    if not BOT_TOKEN or BOT_TOKEN == 'your_bot_token_here':
        print("❌ Error: Please set BOT_TOKEN in .env file first")
        print("How to get: Search @BotFather in Telegram, send /newbot to create a bot")
        sys.exit(1)
    
    # Initialize database
    print("🔄 Initializing database...")
    init_database()
    
    # Create application
    print("🤖 Starting bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addtest", add_test_order_command))
    
    # Register forwarding management commands
    application.add_handler(CommandHandler("setforward", set_forward_rule_command))
    application.add_handler(CommandHandler("listforward", list_forward_rules_command))
    
    # Register message handlers - Listen for messages containing order keywords
    # Text messages
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            process_order_message
        )
    )
    
    # Messages with photos
    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            process_order_message
        )
    )
    
    # Register forwarding handler - Listen for reply messages (lower priority)
    # This handler catches all reply messages and checks if forwarding is needed
    application.add_handler(
        MessageHandler(
            filters.REPLY & (filters.TEXT | filters.PHOTO | filters.Document.ALL | filters.VIDEO | filters.VOICE),
            forward_reply_message
        )
    )
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    print("✅ Bot started!")
    print("📌 Press Ctrl+C to stop")
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
