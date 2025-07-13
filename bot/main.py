from telegram.ext import ApplicationBuilder
import os
from dotenv import load_dotenv
from dispatcher import setup_dispatcher

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Setup all handlers
    setup_dispatcher(app)

    print("Bot is running...")
    app.run_polling()
