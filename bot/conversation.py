from telegram import Update 
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

# States for the conversation
ORIGIN, DESTINATION, BUDGET, CURRENCY, TRAVEL_DATES = range(5)

user_data_temp = {}

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✈️ Where are you flying from? (e.g., SIN, JHB)")
    return ORIGIN

async def set_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    airports = [code.strip().upper() for code in text.split(",")]
    user_data_temp["origin"] = airports
    await update.message.reply_text(
        "🛬 Where do you want to go? (you can enter multiple codes, e.g., KUL, DXB, LHR)"
    )
    return DESTINATION

async def set_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    airports = [code.strip().upper() for code in text.split(",")]
    user_data_temp["destination"] = airports
    await update.message.reply_text("💰 What’s your budget?")
    return BUDGET

async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp["budget"] = update.message.text
    await update.message.reply_text("💱 What currency? (e.g., SGD, USD, EUR)")
    return CURRENCY

async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp["currency"] = update.message.text.strip().upper()
    await update.message.reply_text(
        "📅 Travel dates? (optional, e.g., 2025-06-01 or type 'any')"
    )
    return TRAVEL_DATES


async def set_travel_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp["dates"] = update.message.text
    summary = (
        f"✅ All set! Here's what I got:\n\n"
        f"From: {', '.join(user_data_temp['origin'])}\n"
        f"To: {', '.join(user_data_temp['destination'])}\n"
        f"Max Budget: {user_data_temp['currency']} {user_data_temp['budget']}\n"
        f"Travel Date(s): {user_data_temp['dates']}"
    )
    await update.message.reply_text(summary)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Search canceled.")
    return ConversationHandler.END
