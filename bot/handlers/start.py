from telegram import Update
from telegram.ext import ContextTypes

async def start(update, context):
    # Send welcome message with a list of commands

    welcome_text = (
        "Hello! 👋 Welcome to FlyMePlease! Here are the commands you can use: \n\n"
        "/search - Search for cheap flights between 2 cities. \n"
        "/subscribe - Subscribe to routes you are interested in and get alerts on price drops and changes. \n"
        "/my_routes - Show the subscribed routes \n"
        "/help - Show the list of commands anytime."
    )

    await update.message.reply_text(welcome_text)