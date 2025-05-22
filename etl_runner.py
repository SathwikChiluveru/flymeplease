import asyncio
from etl.extract import fetch_raw_flights
from etl.transform import transform_to_records
from etl.load import load_to_csv

user_data = {
    "trip_type": "roundtrip",
    "origin": ["TLS"],
    "destination": ["MLA"],
    "budget": 450,
    "dates": "2025-05-25",
    "return_date": "2025-05-30"
}

async def run_etl():
    print("🔍 Extracting data...")
    raw_json_with_budget = await fetch_raw_flights(user_data, budget=user_data.get("budget"))
    raw_json = raw_json_with_budget["raw_flights"]
    budget = raw_json_with_budget["budget"]

    print("Raw extracted data count:", len(raw_json))
    print("Budget for this search query:", budget)
    
    print("🔄 Transforming data...")
    records = transform_to_records(raw_json, budget=budget)
    print(f"Transformed records count: {len(records)}")  # Debug print

    print("💾 Loading data...")
    load_to_csv(records)
    print("✅ Done! Saved to data/processed_flights.csv")


if __name__ == "__main__":
    asyncio.run(run_etl())
