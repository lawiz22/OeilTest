import random
from datetime import timedelta
from faker import Faker

fake = Faker("fr_CA")

def gen_clients(rows, eff_date):
    for _ in range(rows):
        yield {
            "client_id": random.randint(100000, 999999),
            "nom": fake.last_name(),
            "prenom": fake.first_name(),
            "client_type": random.choice(["PERSONNEL", "BUSINESS"]),
            "pays": fake.country(),
            "statut": random.choice(["ACTIF", "FERME"]),
            "date_effet": eff_date.date().isoformat()
        }

def gen_accounts(rows, eff_date):
    for _ in range(rows):
        yield {
            "account_id": random.randint(1_000_000, 9_999_999),
            "client_id": random.randint(100000, 999999),
            "account_type": random.choice(["CHEQUE", "EPARGNE"]),
            "currency": random.choice(["CAD", "USD"]),
            "balance": round(random.uniform(100, 250000), 2),
            "open_date": eff_date.date().isoformat()
        }

def gen_transactions(rows, eff_date):
    for _ in range(rows):
        yield {
            "transaction_id": random.randint(1_000_000, 9_999_999),
            "account_id": random.randint(1_000_000, 9_999_999),
            "amount": round(random.uniform(-5000, 5000), 2),
            "currency": random.choice(["CAD", "USD"]),
            "transaction_ts": eff_date.isoformat(),
            "ingestion_date": eff_date.date().isoformat()
        }

def gen_contracts(rows, eff_date):
    for _ in range(rows):
        start_date = eff_date.date()
        end_date = start_date + timedelta(days=random.randint(180, 1800))

        yield {
            "contract_id": random.randint(10000, 99999),
            "client_id": random.randint(100000, 999999),
            "product_type": random.choice(["PRET", "HYPOTHEQUE", "CARTE"]),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "statut": random.choice(["ACTIF", "TERMINE"])
        }

SCHEMAS = {
    "clients": {
        "fields": ["client_id", "nom", "prenom", "client_type", "pays", "statut", "date_effet"],
        "generator": gen_clients
    },
    "accounts": {
        "fields": ["account_id", "client_id", "account_type", "currency", "balance", "open_date"],
        "generator": gen_accounts
    },
    "transactions": {
        "fields": [
            "transaction_id", "account_id", "amount",
            "currency", "transaction_ts", "ingestion_date"
        ],
        "generator": gen_transactions
    },
    "contracts": {
        "fields": ["contract_id", "client_id", "product_type", "start_date", "end_date", "statut"],
        "generator": gen_contracts
    }
}
