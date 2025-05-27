import os
import httpx

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_BASE = "https://flights-sky.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "flights-sky.p.rapidapi.com"
}

ENDPOINTS = {
    "roundtrip": f"{API_BASE}/flights/search-roundtrip",
    "one-way": f"{API_BASE}/flights/search-one-way"
}

async def fetch_raw_flights(user_data, budget=None):
    if not RAPIDAPI_KEY:
        raise Exception("Missing API Key")

    trip_type = user_data.get("trip_type", "one-way")
    url = ENDPOINTS.get(trip_type, ENDPOINTS["one-way"])

    all_results = []

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
                    response.raise_for_status()
                    data = response.json()
                    all_results.append(data)
                except Exception as e:
                    # handle or log error
                    continue
    return {"raw_flights": all_results, "budget": budget}
