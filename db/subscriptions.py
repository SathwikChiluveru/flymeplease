import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def subscription_exists(subscription):
    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASS")
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    DBNAME = os.getenv("DB_NAME")

    try:
        conn = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        cursor = conn.cursor()

        query = """
            SELECT 1 FROM subscriptions 
            WHERE user_id = %s AND origin = %s AND destination = %s 
            AND departure_date = %s AND trip_type = %s
        """

        cursor.execute(query, (
            subscription["user_id"],
            subscription["origin"],
            subscription["destination"],
            subscription["departure_date"],
            subscription["trip_type"]
        ))

        exists = cursor.fetchone() is not None

        cursor.close()
        conn.close()

        return exists
    except Exception as e:
        raise Exception(f"DB check error: {e}")

def add_subscription(subscription):
    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASS")
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    DBNAME = os.getenv("DB_NAME")

    try:
        conn = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO subscriptions 
            (user_id, origin, destination, currency, budget, budget_usd, departure_date, return_date, trip_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            subscription["user_id"],
            subscription["origin"],
            subscription["destination"],
            subscription["currency"],
            subscription["budget"],
            subscription["budget_usd"],
            subscription["departure_date"],
            subscription.get("return_date"),
            subscription["trip_type"]
        ))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise Exception(f"DB insert error: {e}")
