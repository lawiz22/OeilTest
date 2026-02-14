import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
import argparse
from faker import Faker

fake = Faker("fr_CA")

# -----------------------------
# CONFIG
# -----------------------------
BASE_OUTPUT = Path("output/bronze")

PERIOD_RULES = {
    "Q": lambda d: True,
    "QS": lambda d: d.weekday() in (1, 2, 3),   # mar-mer-jeu
    "H": lambda d: d.weekday() == 6,           # dimanche
    "M": lambda d: d.day == 1                  # 1er du mois
}


# -----------------------------
# DATA GENERATORS
# -----------------------------
def generate_clients(n):
    for _ in range(n):
        yield {
            "client_id": fake.random_int(100000, 999999),
            "nom": fake.last_name(),
            "prenom": fake.first_name(),
            "client_type": random.choice(["PERSONNEL", "BUSINESS"]),
            "pays": fake.country(),
            "statut": random.choice(["ACTIF", "FERME"]),
            "date_effet": fake.date_this_decade()
        }


# -----------------------------
# MAIN
# -----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--period", required=True, choices=["Q", "QS", "H", "M"])
    parser.add_argument("--rows", type=int, default=100)

    args = parser.parse_args()

    table = args.table
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    period = args.period
    rows = args.rows

    current = start

    while current <= end:
        if PERIOD_RULES[period](current):

            folder = (
                BASE_OUTPUT
                / table
                / f"period={period}"
                / f"year={current.year}"
                / f"month={current.month:02d}"
                / f"day={current.day:02d}"
                / "data"
            )
            folder.mkdir(parents=True, exist_ok=True)

            filename = f"{table}_{current.date()}_{period}.csv"
            filepath = folder / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["client_id", "nom", "prenom", "client_type", "pays", "statut", "date_effet"]
                )
                writer.writeheader()
                for row in generate_clients(rows):
                    writer.writerow(row)

            print(f"📄 CSV généré : {filepath}")

        current += timedelta(days=1)


if __name__ == "__main__":
    main()
