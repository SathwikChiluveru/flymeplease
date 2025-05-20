from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup 
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime, timedelta


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

    keyboard = [
        [
            InlineKeyboardButton("Today", callback_data="date_today"),
            InlineKeyboardButton("Tomorrow", callback_data="date_tomorrow")
        ],
        [
            InlineKeyboardButton("This Weekend", callback_data="date_weekend"),
            InlineKeyboardButton("Next Week", callback_data="date_next_week")
        ],
        [
            InlineKeyboardButton("Manual Date Entry", callback_data="date_manual")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("📅 Choose your travel date:", reply_markup=reply_markup)
    return TRAVEL_DATES

async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    today = datetime.today()

    if choice == "date_today":
        selected_date = today.strftime("%Y-%m-%d")
    elif choice == "date_tomorrow":
        selected_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif choice == "date_weekend":
        # Find next Saturday
        days_until_sat = (5 - today.weekday()) % 7
        selected_date = (today + timedelta(days=days_until_sat)).strftime("%Y-%m-%d")
    elif choice == "date_next_week":
        selected_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    elif choice == "date_manual":
        await query.edit_message_text("📆 Please type your travel date (YYYY-MM-DD):")
        return "WAITING_FOR_MANUAL_DATE"

    if choice != "date_manual":
        user_data_temp["dates"] = selected_date
        summary = (
            f"✅ Preferences saved!\n\n"
            f"From: {', '.join(user_data_temp['origin'])}\n"
            f"To: {', '.join(user_data_temp['destination'])}\n"
            f"Max Budget: {user_data_temp['currency']} {user_data_temp['budget']}\n"
            f"Travel Date: {user_data_temp['dates']}"
        )
        await query.edit_message_text(summary)
        return ConversationHandler.END

async def handle_manual_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
        user_data_temp["dates"] = text
        summary = (
            f"✅ Preferences saved!\n\n"
            f"From: {', '.join(user_data_temp['origin'])}\n"
            f"To: {', '.join(user_data_temp['destination'])}\n"
            f"Max Budget: {user_data_temp['currency']} {user_data_temp['budget']}\n"
            f"Travel Date: {user_data_temp['dates']}"
        )
        await update.message.reply_text(summary)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid date in YYYY-MM-DD format:")
        return "WAITING_FOR_MANUAL_DATE"


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
