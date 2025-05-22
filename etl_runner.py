import asyncio
from etl.extract import fetch_raw_flights
from etl.transform import transform_to_records
from etl.load import load_to_csv

user_data = {
    "trip_type": "round-trip",
    "origin": ["SIN", "JHB"],
    "destination": ["KUL", "LBJ"],
    "budget": 300,
    "dates": "2025-05-25",
    "return_date": "2025-05-30"
}

async def run_etl():
    print("🔍 Extracting data...")
    raw_json = await fetch_raw_flights(user_data)
    print("Raw extracted data:", raw_json)  # Debug print
    
    print("🔄 Transforming data...")
    records = transform_to_records(raw_json)
    print(f"Transformed records count: {len(records)}")  # Debug print

    print("💾 Loading data...")
    load_to_csv(records)
    print("✅ Done! Saved to data/processed_flights.csv")


if __name__ == "__main__":
    asyncio.run(run_etl())
