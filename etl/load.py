import csv
from pathlib import Path

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

