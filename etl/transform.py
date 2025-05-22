from datetime import datetime
import json

def transform_to_records(raw_api_responses, user_id=None):
    rows = []
    fetch_date = datetime.utcnow().isoformat()
    
    # raw_api_responses is a list of dicts, each is one API response (per origin-destination combo)
    for data in raw_api_responses:
        itineraries = data.get("data", {}).get("itineraries", [])
        
        for item in itineraries:
            legs = item.get("legs", [])
            price_raw = item.get("price", {}).get("raw")
            if price_raw is None:
                continue  # skip invalid prices
            
            for i, leg in enumerate(legs):
                leg_type = "outbound" if i == 0 else "return"
                rows.append({
                    "fetch_date": fetch_date,
                    "route": f"{leg.get('origin', {}).get('id', '')} → {leg.get('destination', {}).get('id', '')}",
                    "price": price_raw,
                    "departure": leg.get("departure"),
                    "arrival": leg.get("arrival"),
                    "airline": leg.get("carriers", {}).get("marketing", [{}])[0].get("name", ""),
                    "flight_number": leg.get("segments", [{}])[0].get("flightNumber", ""),
                    "score": item.get("score"),
                    "tags": ", ".join(item.get("tags", [])),
                    "leg_type": leg_type
                })
    return rows
