import argparse
import random
import csv
from datetime import datetime, timedelta
from faker import Faker
from pathlib import Path

fake = Faker("en_CA")

OUTPUT_DIR = Path("output/data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# Utils
# -------------------------
def daterange(start, end, step_days=1):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=step_days)


def write_csv(filename, headers, rows):
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"📄 Fichier généré : {path}")


# -------------------------
# CLIENTS (Mensuel)
# -------------------------
def generate_clients(start, end):
    rows = []
    client_ids = []

    for month in daterange(start, end, step_days=30):
        for _ in range(random.randint(20, 50)):
            client_id = random.randint(100000, 999999)
            client_ids.append(client_id)

            rows.append([
                client_id,
                random.choice(["PERSONNEL", "BUSINESS"]),
                fake.country(),
                random.choice(["ACTIF", "FERME"]),
                month.date()
            ])

    return rows, list(set(client_ids))


# -------------------------
# ACCOUNTS (Hebdomadaire)
# -------------------------
def generate_accounts(start, end, client_ids):
    rows = []
    account_ids = []

    for week in daterange(start, end, step_days=7):
        for _ in range(random.randint(10, 30)):
            account_id = random.randint(1000000, 9999999)
            account_ids.append(account_id)

            rows.append([
                account_id,
                random.choice(client_ids),
                random.choice(["CHEQUE", "EPARGNE"]),
                random.choice(["CAD", "USD"]),
                round(random.uniform(100, 250000), 2),
                week.date()
            ])

    return rows, list(set(account_ids))


# -------------------------
# CONTRACTS (Mensuel)
# -------------------------
def generate_contracts(start, end, client_ids):
    rows = []

    for month in daterange(start, end, step_days=30):
        for _ in range(random.randint(5, 15)):
            start_date = fake.date_between(start_date=month, end_date=month + timedelta(days=10))
            end_date = start_date + timedelta(days=random.randint(180, 1800))

            rows.append([
                random.randint(10000, 99999),
                random.choice(client_ids),
                random.choice(["PRET", "HYPOTHEQUE", "CARTE"]),
                start_date,
                end_date,
                random.choice(["ACTIF", "TERMINE"])
            ])

    return rows


# -------------------------
# MAIN
# -------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True, choices=["clients", "accounts", "contracts"])
    parser.add_argument("--date_debut_eff", required=True)
    parser.add_argument("--date_fin_eff", required=True)

    args = parser.parse_args()

    start = datetime.fromisoformat(args.date_debut_eff)
    end = datetime.fromisoformat(args.date_fin_eff)

    if args.table == "clients":
        rows, _ = generate_clients(start, end)
        write_csv(
            "clients.csv",
            ["client_id", "client_type", "pays", "statut", "date_effet"],
            rows
        )

    elif args.table == "accounts":
        clients, client_ids = generate_clients(start, end)
        accounts, _ = generate_accounts(start, end, client_ids)

        write_csv(
            "accounts.csv",
            ["account_id", "client_id", "account_type", "currency", "balance", "open_date"],
            accounts
        )

    elif args.table == "contracts":
        clients, client_ids = generate_clients(start, end)
        contracts = generate_contracts(start, end, client_ids)

        write_csv(
            "contracts.csv",
            ["contract_id", "client_id", "product_type", "start_date", "end_date", "statut"],
            contracts
        )

    print("✅ Génération terminée")


if __name__ == "__main__":
    main()
