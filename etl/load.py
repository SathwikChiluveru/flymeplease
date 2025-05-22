import os, csv, psycopg2
from pathlib import Path
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

def load_to_csv(records, filename="data/processed_flights.csv"):
    Path("data").mkdir(exist_ok=True)
    if not records:
        return

    file_exists = Path(filename).exists()

    with open(filename, mode='a' if file_exists else 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)

def load_to_db(records):

    if not records:
        print("No records to insert.")
        return

    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASS")
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    DBNAME = os.getenv("DB_NAME")

    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        print("Connection successful!")
        cursor = connection.cursor()

        # Step 1: Group records by flight (unique flight is by fetch_date, route, price, score, tags)
        flights_map = {}  # key -> flight_data values + list of legs
        for rec in records:
            key = (rec["fetch_date"], rec["route"], rec["price"], rec.get("score"), rec.get("tags"))
            if key not in flights_map:
                flights_map[key] = {
                    "flight_data": key,
                    "legs": []
                }
            flights_map[key]["legs"].append({
                "leg_type": rec["leg_type"],
                "departure": rec["departure"],
                "arrival": rec["arrival"],
                "airline": rec["airline"],
                "flight_number": rec["flight_number"]
            })

        # Step 2: Insert flights and get their IDs
        flight_data_rows = [fd["flight_data"] for fd in flights_map.values()]
        insert_flight_data_query = """
            INSERT INTO flight_data (fetch_date, route, price, score, tags)
            VALUES %s RETURNING id
        """
        execute_values(cursor, insert_flight_data_query, flight_data_rows)
        flight_ids = [row[0] for row in cursor.fetchall()]

        # Step 3: Insert legs referencing flight_id
        flight_legs_rows = []
        for flight_id, fd in zip(flight_ids, flights_map.values()):
            for leg in fd["legs"]:
                flight_legs_rows.append((
                    flight_id,
                    leg["leg_type"],
                    leg["departure"],
                    leg["arrival"],
                    leg["airline"],
                    leg["flight_number"]
                ))

        insert_legs_query = """
            INSERT INTO flight_legs (flight_id, leg_type, departure, arrival, airline, flight_number)
            VALUES %s
        """
        execute_values(cursor, insert_legs_query, flight_legs_rows)

        connection.commit()
        print(f"Inserted {len(flight_ids)} flight_data rows and {len(flight_legs_rows)} flight_legs rows.")

        cursor.close()
        connection.close()
        print("Connection closed.")

    except Exception as e:
        print(f"Failed to connect or insert data: {e}")
