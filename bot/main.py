from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
from dotenv import load_dotenv
import os

from bot.conversation import (
    search, set_origin, set_destination, set_budget, set_currency, set_travel_dates, cancel,
    ORIGIN, DESTINATION, BUDGET, CURRENCY, TRAVEL_DATES
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("👋 Welcome to FlyMePlease! Use /search to get started.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))

    # Setup flow handler
    setup_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={
            ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_origin)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_destination)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_budget)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_currency)],
            TRAVEL_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_travel_dates)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(setup_handler)

    print("Bot is running...")
    app.run_polling()
