import os
import json
import httpx
import asyncio

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_BASE = "https://flights-sky.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flights-sky.p.rapidapi.com"
}

ENDPOINTS = {
    "roundtrip": f"{API_BASE}/flights/search-roundtrip",
    "oneway": f"{API_BASE}/flights/search-one-way"
}

async def search_flights(user_data):
    if not RAPIDAPI_KEY:
        return "Missing API Key."

    trip_type = user_data.get("trip_type", "oneway")
    url = ENDPOINTS.get(trip_type, ENDPOINTS["oneway"])
    max_budget = float(user_data.get("budget", 99999))
    results_json = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for origin in user_data["origin"]:
            for destination in user_data["destination"]:
                params = {
                    "fromEntityId": origin,
                    "toEntityId": destination,
                    "departDate": user_data["dates"]
                }
                if trip_type == "roundtrip":
                    params["returnDate"] = user_data["return_date"]

                try:
                    response = await client.get(url, headers=HEADERS, params=params)
                    data = response.json()
                    itineraries = data.get("data", {}).get("itineraries", [])

                    for itinerary in itineraries:
                        price_info = itinerary.get("price", {})
                        price_raw = price_info.get("raw")
                        if price_raw is None or float(price_raw) > max_budget:
                            continue

                        legs_data = []
                        for leg in itinerary.get("legs", []):
                            carrier = leg.get("carriers", {}).get("marketing", [{}])[0]
                            segment = leg.get("segments", [{}])[0]
                            legs_data.append({
                                "origin": leg.get("origin", {}).get("id", ""),
                                "destination": leg.get("destination", {}).get("id", ""),
                                "departure": leg.get("departure"),
                                "arrival": leg.get("arrival"),
                                "duration_minutes": leg.get("durationInMinutes"),
                                "flight_number": segment.get("flightNumber"),
                                "airline": carrier.get("name"),
                                "logo": carrier.get("logoUrl")
                            })

                        results_json.append({
                            "route": f"{origin} → {destination}",
                            "price_raw": price_raw,
                            "price_formatted": price_info.get("formatted"),
                            "score": itinerary.get("score"),
                            "tags": itinerary.get("tags", []),
                            "farePolicy": itinerary.get("farePolicy", {}),
                            "eco": itinerary.get("eco", {}),
                            "isMashUp": itinerary.get("isMashUp", False),
                            "hasFlexibleOptions": itinerary.get("hasFlexibleOptions", False),
                            "isSelfTransfer": itinerary.get("isSelfTransfer", False),
                            "legs": legs_data
                        })

                except Exception as e:
                    continue

    return json.dumps(results_json, indent=2)

# Sample run for testing
user_data = {
    "trip_type": "roundtrip",
    "origin": ["SIN"],
    "destination": ["KUL"],
    "budget": 30,
    "dates": "2025-05-25",
    "return_date": "2025-05-30"
}

async def main():
    results = await search_flights(user_data)
    print(results)

asyncio.run(main())
