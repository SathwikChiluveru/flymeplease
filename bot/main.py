from telegram import BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os

from conversation import (
    search, set_trip_type, set_origin, set_destination, set_budget, set_currency, cancel,handle_date_selection, handle_manual_date, handle_return_date, handle_return_date_selection,
    TRIP_TYPE, ORIGIN, DESTINATION, BUDGET, CURRENCY, TRAVEL_DATES, RETURN_DATE, RETURN_DATE_SELECTION
)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

commands = [
    BotCommand("start", "Start the bot"),
    BotCommand("search", "Search for flight alerts"),
    BotCommand("cancel", "Cancel the current operation"),
]

async def start(update, context):
    await update.message.reply_text("👋 Welcome to FlyMePlease! Use /search to get started.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Set Bot Commands
    # app.bot.set_my_commands(commands)

    # Command handlers
    app.add_handler(CommandHandler("start", start))

    # Setup flow handler
    setup_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={
            TRIP_TYPE: [CallbackQueryHandler(set_trip_type)],
            ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_origin)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_destination)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_budget)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_currency)],
            TRAVEL_DATES: [
                CallbackQueryHandler(handle_date_selection),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_date),
                CommandHandler("cancel", cancel)
            ],
            RETURN_DATE_SELECTION: [
                CallbackQueryHandler(handle_return_date_selection),
                CommandHandler("cancel", cancel)
            ],
            RETURN_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_return_date),
                CommandHandler("cancel", cancel)
            ],

        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(setup_handler)

    print("Bot is running...")
    app.run_polling()
