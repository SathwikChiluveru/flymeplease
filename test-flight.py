import asyncio
import os
from bot.flights import search_flights

# Sample user input
user_data = {
    "trip_type": "roundtrip",
    "origin": ["SIN"],               # Singapore, Johor Bahru
    "destination": ["JHB"],          # Kuala Lumpur, Dubai
    "budget": 190,                           # Max budget in SGD
    "dates": "2025-05-25",                  # Departure date
    "return_date": "2025-05-30"             # Return date
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
