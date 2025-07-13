from datetime import datetime
import json
import uuid

def transform_to_records(raw_json, user_data, budget=None):
    rows = []
    seen_flights = set()
    fetch_date = datetime.utcnow().isoformat()
    trip_type = user_data.get("trip_type", "one-way")

    for data in raw_json:
        itineraries = data.get("data", {}).get("itineraries", [])

        for item in sorted(itineraries, key=lambda x: x.get("price", {}).get("raw", float('inf'))):
            price_raw = item.get("price", {}).get("raw")
            currency = item.get("price", {}).get("currency", "USD")
            if price_raw is None or (budget is not None and price_raw > float(budget)):
                continue

            legs_data = []
            leg_key_parts = []

            for i, leg in enumerate(item.get("legs", [])):
                leg_type = "outbound" if i == 0 else "inbound"
                origin = leg.get("origin", {}).get("id", "")
                destination = leg.get("destination", {}).get("id", "")
                departure = leg.get("departure")
                arrival = leg.get("arrival")
                airline = leg.get("carriers", {}).get("marketing", [{}])[0].get("name", "")
                flight_number = leg.get("segments", [{}])[0].get("flightNumber", "")

                leg_key_parts.append(f"{origin}-{destination}-{departure}-{arrival}-{airline}-{flight_number}")

                legs_data.append({
                    "leg_type": leg_type,
                    "origin": origin,
                    "destination": destination,
                    "departure": departure,
                    "arrival": arrival,
                    "airline": airline,
                    "flight_number": flight_number
                })

            if not legs_data:
                continue

            # Create a unique key from the leg sequence
            unique_key = "|".join(leg_key_parts)
            if unique_key in seen_flights:
                continue  # Skip duplicates
            seen_flights.add(unique_key)

            trip_id = uuid.uuid5(uuid.NAMESPACE_DNS, unique_key)  # Stable UUID for duplicates

            rows.append({
                "id": uuid.uuid4(),
                "trip_id": trip_id,
                "fetch_date": fetch_date,
                "trip_type": trip_type,
                "origin": legs_data[0]["origin"],
                "destination": legs_data[0]["destination"],
                "price": price_raw,
                "currency": currency,
                "score": item.get("score"),
                "tags": ", ".join(item.get("tags", [])),
                "legs": legs_data
            })

    return sorted(rows, key=lambda x: x["price"])[:20]
