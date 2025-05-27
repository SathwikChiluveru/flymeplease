import asyncio
from etl.extract import fetch_raw_flights
from etl.transform import transform_to_records
from etl.load import load_to_csv, load_to_db

async def run_etl(user_data):
    print("🔍 Extracting data...")
    raw_json_with_budget = await fetch_raw_flights(user_data, budget=user_data.get("budget"))
    raw_json = raw_json_with_budget["raw_flights"]
    budget = raw_json_with_budget["budget"]

    print("Raw extracted data count:", len(raw_json))
    print("Budget for this search query:", budget)
    
    print("🔄 Transforming data...")
    trip_records = transform_to_records(raw_json, user_data, budget)
    print(f"Transformed records count: {len(trip_records)}")  # Debug print

    print("💾 Loading data...")
    load_to_csv(trip_records)
    load_to_db(trip_records)
    print("✅ Done! Saved to data/processed_flights.csv")
    print("✅ Done with ETL to DB!")

    return trip_records
