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

def load_to_db(trip_records):

    if not trip_records:
        print("No records to insert.")
        return
    
    trip_records = sorted(trip_records, key=lambda x: x["price"])

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

        # Insert into flight_data
        flight_data_rows = [
            (
                str(rec["id"]), rec["fetch_date"], rec["trip_type"], str(rec["trip_id"]),
                rec["origin"], rec["destination"], rec["price"], rec["score"], rec["tags"]
            )
            for rec in trip_records
        ]

        insert_data_query = """
            INSERT INTO flight_data (id, fetch_date, trip_type, trip_id, origin, destination, price, score, tags)
            VALUES %s
        """
        execute_values(cursor, insert_data_query, flight_data_rows)

        # Insert legs
        flight_legs_rows = []
        for rec in trip_records:
            for leg in rec["legs"]:
                flight_legs_rows.append((
                    str(rec["trip_id"]), leg["leg_type"], leg["origin"], leg["destination"],
                    leg["departure"], leg["arrival"], leg["airline"], leg["flight_number"]
                ))

        insert_legs_query = """
            INSERT INTO flight_legs (trip_id, leg_type, origin, destination, departure, arrival, airline, flight_number)
            VALUES %s
        """
        execute_values(cursor, insert_legs_query, flight_legs_rows)

        connection.commit()
        print(f"Inserted {len(trip_records)} flight_data and {len(flight_legs_rows)} legs.")
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Failed to connect or insert data: {e}")
