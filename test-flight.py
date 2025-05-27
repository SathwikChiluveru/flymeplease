import asyncio
import os
from bot.flights import search_flights

# Sample user input
user_data = {
    "trip_type": "One-way",
    "origin": ["SIN"],               # Singapore, Johor Bahru
    "destination": ["KUL"],          # Kuala Lumpur, Dubai
    "budget": 300,                           # Max budget in SGD
    "dates": "2025-06-03",                  # Departure date
    # "return_date": "2025-06-06"             # Return date
}

async def main():
    print("🚀 Searching flights with user data:")
    for k, v in user_data.items():
        print(f"{k}: {v}")
    print()

    results = await search_flights(user_data)
    print("\n📋 Search Results:\n")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
