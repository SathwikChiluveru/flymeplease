from telegram import Update
from telegram.ext import ContextTypes

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation canceled.")
    return