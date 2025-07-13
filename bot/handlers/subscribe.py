from telegram import Update
from telegram.ext import ContextTypes
from db.subscriptions import add_subscription, subscription_exists
from etl_runner import run_etl

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 5:
            await update.message.reply_text("Usage: /subscribe ORIGIN DESTINATION BUDGET CURRENCY YYYY-MM-DD")
            return

        origin, destination, budget_str, currency, date = args
        user_id = str(update.effective_user.id)

        try:
            budget = float(budget_str)
        except ValueError:
            await update.message.reply_text("💰 Budget must be a number.")
            return

        from utils.currency import get_usd_to_currency_rate
        try:
            rate = get_usd_to_currency_rate(currency.upper())
            budget_usd = float(round(budget / rate, 2))
        except Exception as e:
            await update.message.reply_text(f"⚠️ Currency conversion failed: {e}")
            return

        subscription = {
            "user_id": user_id,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "budget": budget,
            "budget_usd": budget_usd,
            "currency": currency.upper(),
            "departure_date": date,
            "return_date": None,
            "trip_type": "one-way"
        }

        # Save subscription to DB (sync now)
        if subscription_exists(subscription):
            await update.message.reply_text(
                f"⚠️ You’ve already subscribed to this route on {date}. Use /my_routes to view!"
            )
            return

        add_subscription(subscription)

        # Fetch flights immediately via ETL
        records = await run_etl({
            "origin": [origin.upper()],
            "destination": [destination.upper()],
            "currency": currency.upper(),
            "trip_type": "one-way",
            "dates": date,
            "budget": budget_usd
        })

        from utils.formatters import format_flights_for_display
        formatted = format_flights_for_display(records, currency.upper())

        await update.message.reply_text(
            f"✅ Subscribed to {origin.upper()} ➡ {destination.upper()} on {date} with {currency.upper()} {budget:.2f}!\n\n"
            f"Here's what's available now:\n\n{formatted}",
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Failed to subscribe: {e}")
