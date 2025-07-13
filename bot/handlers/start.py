from telegram import Update
from telegram.ext import ContextTypes

async def start(update, context):
    # Send welcome message with a list of commands

    welcome_text = (
        "Hello! 👋 Welcome to FlyMePlease.\n\n"
        "I'm here to help you find the best flight deals quickly and easily.\n\n"
        "Here’s what I can do:\n"
        "• /search – Find cheap flights between two cities\n"
        "• /subscribe – Get alerts for price drops on routes you care about\n"
        "• /my_routes – View and manage your saved routes\n"
        "• /help – View all available commands anytime\n\n"
        "Let’s get started! Type /search to begin your journey. ✈️"
    )

    await update.message.reply_text(welcome_text)