from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup 
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, 
    filters, CallbackQueryHandler
)
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from etl_runner import run_etl
from utils.validators import is_valid_airport_code
from utils.date_utils import get_today, get_tomorrow, get_next_saturday, get_next_week
from utils.formatters import format_flights_for_display
from utils.currency import convert_price, get_usd_to_currency_rate
import asyncio

# States for the conversation
TRIP_TYPE, ORIGIN, DESTINATION, BUDGET, CURRENCY, TRAVEL_DATES, RETURN_DATE, RETURN_DATE_SELECTION = range(8)

user_data_temp = {}

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for the search command"""
    keyboard = [
        [
            InlineKeyboardButton("One-way", callback_data="one-way"),
            InlineKeyboardButton("Roundtrip", callback_data="roundtrip"),
        ]
    ]
    await update.message.reply_text("🧭 What type of trip are you planning?", reply_markup=InlineKeyboardMarkup(keyboard))
    return TRIP_TYPE

async def set_trip_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data_temp["trip_type"] = query.data
    await query.edit_message_text("✈️ Where are you flying from? (e.g., SIN, JHB)")
    return ORIGIN

async def set_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    airports = [code.strip().upper() for code in text.split(",")]

    if not all(is_valid_airport_code(code) for code in airports):
        await update.message.reply_text("⚠️ Please enter valid 3-letter airport code(s), e.g., SIN, JHB.")
        return ORIGIN

    user_data_temp["origin"] = airports
    await update.message.reply_text(
        "🛬 Where do you want to go? (you can enter multiple codes, e.g., KUL, DXB, LHR)"
    )
    return DESTINATION

async def set_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    airports = [code.strip().upper() for code in text.split(",")]

    if not all(is_valid_airport_code(code) for code in airports):
        await update.message.reply_text("⚠️ Please enter valid 3-letter airport code(s), e.g., SIN, JHB.")
        return DESTINATION

    user_data_temp["destination"] = airports
    await update.message.reply_text("💰 What's your budget?")
    return BUDGET

async def set_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp["original_budget"] = update.message.text.strip()
    await update.message.reply_text("💱 What currency? (e.g., SGD, USD, EUR)")
    return CURRENCY

async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp["currency"] = update.message.text.strip().upper()

    # Change the entered budget to USD

    try:
        rate = get_usd_to_currency_rate(user_data_temp["currency"])
        original_budget = float(user_data_temp["original_budget"])
        converted_budget = round(original_budget / rate, 2)

        user_data_temp["budget_usd"] = converted_budget
        user_data_temp["budget"] = original_budget

        print(f"Original Budget: {user_data_temp['currency']} {user_data_temp['budget']:.2f}")
        print(f"Converted Budget (USD): USD {user_data_temp['budget_usd']:.2f}")



    except Exception as e:    
        await update.message.reply_text(f"⚠️ Could not convert budget to USD: {e}. Assuming budget is in USD.")
        user_data_temp["budget"] = float(user_data_temp["original_budget"])
        user_data_temp["budget_usd"] = user_data_temp["budget"]
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
        selected_date = get_today()
    elif choice == "date_tomorrow":
        selected_date = get_tomorrow()
    elif choice == "date_weekend":
        # Find next Saturday
        selected_date = get_next_saturday()
    elif choice == "date_next_week":
        selected_date = get_next_week
    elif choice == "date_manual":
        await query.edit_message_text("📆 Please type your travel date (YYYY-MM-DD):")
        return "WAITING_FOR_MANUAL_DATE"

    if choice != "date_manual":
        user_data_temp["dates"] = selected_date
        if user_data_temp["trip_type"] == "roundtrip":
            keyboard = [
                [InlineKeyboardButton("1 day after", callback_data="return_1d")],
                [InlineKeyboardButton("3 days after", callback_data="return_3d")],
                [InlineKeyboardButton("Next weekend", callback_data="return_weekend")],
                [InlineKeyboardButton("Manual Date Entry", callback_data="return_manual")]
            ]
            await query.message.reply_text(
                "📅 Choose your return date:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return RETURN_DATE_SELECTION
        
        summary = (
            f"✅ Preferences Locked In!\n\n"
            f"🧭 Trip Type: ✈️ One-way\n"
            f"📍 From: {', '.join(user_data_temp['origin'])}\n"
            f"📍 To: {', '.join(user_data_temp['destination'])}\n"
            f"💰 Budget: {user_data_temp['currency']} {user_data_temp['budget']}\n"
            f"📅 Departure Date: {user_data_temp['dates']}"
        )

        await query.message.reply_text(summary + "\n\n⏳ Hang tight... looking for flights!")

        try:
            records = await run_etl({**user_data_temp, "budget": user_data_temp["budget_usd"]})
            # 🔍 DEBUG: Print all records returned by ETL
            print("🔍 All ETL Records:")
            for idx, rec in enumerate(records):
                print(f"Record #{idx + 1}: {rec}")
            msg = format_flights_for_display(records, user_data_temp["currency"])
            await query.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await query.message.reply_text(f"⚠️ Error searching flights: {e}")

        return ConversationHandler.END
    
async def handle_return_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    dep_date = datetime.strptime(user_data_temp["dates"], "%Y-%m-%d")

    if choice == "return_1d":
        ret_date = dep_date + timedelta(days=1)
    elif choice == "return_3d":
        ret_date = dep_date + timedelta(days=3)
    elif choice == "return_weekend":
        # Assume return on next Sunday after departure
        days_until_sun = (6 - dep_date.weekday()) % 7 or 7
        ret_date = dep_date + timedelta(days=days_until_sun)
    elif choice == "return_manual":
        await query.edit_message_text("📆 Please enter your return date (YYYY-MM-DD):")
        return RETURN_DATE

    if choice != "return_manual":
        if ret_date <= dep_date:
            await query.edit_message_text("⚠️ Return date must be after the departure date. Try again.")
            return RETURN_DATE_SELECTION

        user_data_temp["return_date"] = ret_date.strftime("%Y-%m-%d")
        summary = (
            f"✅ Preferences Locked In!\n\n"
            f"🧭 Trip Type: ✈️ Round-Trip\n"
            f"📍 From {', '.join(user_data_temp['origin'])}\n"
            f"📍 To {', '.join(user_data_temp['destination'])}\n"
            f"💰 Budget: {user_data_temp['currency']} {user_data_temp['budget']}\n"
            f"📅 Departure Date: {user_data_temp['dates']}\n"
            f"📅 Return Date: {user_data_temp['return_date']}"
        )

        await update.callback_query.message.reply_text(summary + "\n\n⏳ Hang tight... looking for flights!")

        try:
            records = await run_etl({**user_data_temp, "budget": user_data_temp["budget_usd"]})
            msg = format_flights_for_display(records, user_data_temp["currency"])
            await query.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await query.message.reply_text(f"⚠️ Error searching flights: {e}")
        
        return ConversationHandler.END

async def handle_manual_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        datetime.strptime(text, "%Y-%m-%d")
        user_data_temp["dates"] = text
        
        if user_data_temp["trip_type"] == "roundtrip":
            keyboard = [
                [InlineKeyboardButton("1 day after", callback_data="return_1d")],
                [InlineKeyboardButton("3 days after", callback_data="return_3d")],
                [InlineKeyboardButton("Next weekend", callback_data="return_weekend")],
                [InlineKeyboardButton("Manual Date Entry", callback_data="return_manual")]
            ]
            await update.message.reply_text(
                "📅 Choose your return date:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return RETURN_DATE_SELECTION
        
        summary = (
            f"✅ Preferences saved!\n\n"
            f"From: {', '.join(user_data_temp['origin'])}\n"
            f"To: {', '.join(user_data_temp['destination'])}\n"
            f"Max Budget: {user_data_temp['currency']} {user_data_temp['budget']}\n"
            f"Travel Date: {user_data_temp['dates']}"
        )
        await update.message.reply_text(summary + "\n\n⏳ Searching flights, please wait...")

        try:
            records = await run_etl({**user_data_temp, "budget": user_data_temp["budget_usd"]})
            msg = format_flights_for_display(records, user_data_temp["currency"])
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error searching flights: {e}")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid date in YYYY-MM-DD format:")
        return TRAVEL_DATES  # Return to the same state to handle retry
    
async def handle_return_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        dep_date = datetime.strptime(user_data_temp["dates"], "%Y-%m-%d")
        ret_date = datetime.strptime(text, "%Y-%m-%d")

        if ret_date <= dep_date:
            await update.message.reply_text("⚠️ Return date must be after departure. Please re-enter.")
            return RETURN_DATE

        user_data_temp["return_date"] = text
        summary = (
            f"✅ Preferences saved!\n\n"
            f"Trip Type: Roundtrip\n"
            f"From: {', '.join(user_data_temp['origin'])}\n"
            f"To: {', '.join(user_data_temp['destination'])}\n"
            f"Budget: {user_data_temp['currency']} {user_data_temp['budget']}\n"
            f"Departure: {user_data_temp['dates']}\n"
            f"Return: {user_data_temp['return_date']}"
        )
        await update.message.reply_text(summary + "\n\n⏳ Searching flights, please wait...")

        try:
            records = await run_etl({**user_data_temp, "budget": user_data_temp["budget_usd"]})
            msg = format_flights_for_display(records, user_data_temp["currency"])
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error searching flights: {e}")
        
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("⚠️ Invalid date format. Please use YYYY-MM-DD:")
        return RETURN_DATE

async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the search conversation"""
    await update.message.reply_text("❌ Search canceled.")
    return ConversationHandler.END

def search():
    """Creates and returns the ConversationHandler for search functionality"""
    return ConversationHandler(
        entry_points=[CommandHandler("search", start_search)],
        states={
            TRIP_TYPE: [CallbackQueryHandler(set_trip_type)],
            ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_origin)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_destination)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_budget)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_currency)],
            TRAVEL_DATES: [
                CallbackQueryHandler(handle_date_selection),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_date),
            ],
            RETURN_DATE_SELECTION: [
                CallbackQueryHandler(handle_return_date_selection),
            ],
            RETURN_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_return_date),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_search)],
    )