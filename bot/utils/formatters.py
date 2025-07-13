from datetime import datetime
from utils.currency import convert_price

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
        price_in_user_currency, currency_label = convert_price(flight["price"], currency)
        msg_lines.append(f"*{i}. {full_route}: {price_in_user_currency} {currency_label}*")


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