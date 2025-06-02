from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup 
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from etl_runner import run_etl
import asyncio


# States for the conversation
TRIP_TYPE, ORIGIN, DESTINATION, BUDGET, CURRENCY, TRAVEL_DATES, RETURN_DATE, RETURN_DATE_SELECTION = range(8)

user_data_temp = {}

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

def format_flights_for_display(records, currency, max_flights=10):
    if not records:
        return "⚠️ No flights found matching your criteria."

    # Group flights by full round-trip (assumes each record contains 2 legs)
    round_trips = []
    for rec in records:
        legs = rec.get("legs", [])
        if len(legs) >= 2:
            legs = sorted(legs, key=lambda x: 0 if x["leg_type"] == "outbound" else 1)[:2]
            round_trips.append({
                "price": rec["price"],
                "legs": legs
            })
        elif len(legs) == 1:
            # fallback in case it's a one-way mistakenly labeled as round-trip
            round_trips.append({
                "price": rec["price"],
                "legs": legs
            })

    round_trips.sort(key=lambda x: x["price"])
    top_round_trips = round_trips[:max_flights]

    msg_lines = ["🛫 *Top 10 Cheapest Flights:*\n"]

    for i, flight in enumerate(top_round_trips, 1):
        legs = flight["legs"]
        full_route = " -> ".join([f"{leg['origin']}" for leg in legs] + [legs[-1]["destination"]])
        msg_lines.append(f"*{i}. {full_route}: {flight['price']} {currency}*")

        for leg in legs:
            try:
                dt = datetime.fromisoformat(leg["departure"])
                try:
                    dep_time = dt.strftime("%-d %B %I:%M%p")  # Unix
                except:
                    dep_time = dt.strftime("%#d %B %I:%M%p")  # Windows
            except:
                dep_time = leg["departure"].replace("T", " ")

            msg_lines.append(f"📍 *Leg:* {leg['origin']} → {leg['destination']}")
            msg_lines.append(f"🕒 *Departure:* {dep_time}")
            msg_lines.append(f"✈️ *Airline:* {leg['airline']}")
            msg_lines.append(f"🔢 *Flight No:* {leg['flight_number']}")

        if i != len(top_round_trips):
            msg_lines.append("────────────────────")
        msg_lines.append("")

    return "\n".join(msg_lines)


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
            records = await run_etl(user_data_temp)
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
            records = await run_etl(user_data_temp)
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
        summary = (
            f"✅ Preferences saved!\n\n"
            f"From: {', '.join(user_data_temp['origin'])}\n"
            f"To: {', '.join(user_data_temp['destination'])}\n"
            f"Max Budget: {user_data_temp['currency']} {user_data_temp['budget']}\n"
            f"Travel Date: {user_data_temp['dates']}"
        )
        await update.message.reply_text(summary + "\n\n⏳ Searching flights, please wait...")

        try:
            records = await run_etl(user_data_temp)
            msg = format_flights_for_display(records, user_data_temp["currency"])
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error searching flights: {e}")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid date in YYYY-MM-DD format:")
        return "WAITING_FOR_MANUAL_DATE"
    
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
        await update.message.reply_text(summary)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("⚠️ Invalid date format. Please use YYYY-MM-DD:")
        return RETURN_DATE



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
