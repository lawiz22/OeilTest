import random
from faker import Faker

fake = Faker("fr_CA")

def gen_clients(rows, eff_date):
    for _ in range(rows):
        yield {
            "client_id": random.randint(100000, 999999),
            "nom": fake.last_name(),
            "prenom": fake.first_name(),
            "pays": fake.country_code(),
            "date_eff": eff_date.isoformat()
        }

def gen_accounts(rows, eff_date):
    for _ in range(rows):
        yield {
            "account_id": random.randint(1_000_000, 9_999_999),
            "client_id": random.randint(100000, 999999),
            "account_type": random.choice(["CHEQUE", "EPARGNE"]),
            "currency": random.choice(["CAD", "USD"]),
            "date_eff": eff_date.isoformat()
        }

def gen_transactions(rows, eff_date):
    for _ in range(rows):
        yield {
            "transaction_id": random.randint(1_000_000, 9_999_999),
            "client_id": random.randint(100000, 999999),
            "account_id": random.randint(1_000_000, 9_999_999),
            "amount": round(random.uniform(-5000, 5000), 2),
            "currency": random.choice(["CAD", "USD"]),
            "transaction_ts": eff_date.isoformat()
        }

def gen_contracts(rows, eff_date):
    for _ in range(rows):
        yield {
            "contract_id": random.randint(10000, 99999),
            "client_id": random.randint(100000, 999999),
            "contract_type": random.choice(["PRET", "HYPOTHEQUE"]),
            "status": random.choice(["ACTIF", "FERME"]),
            "date_eff": eff_date.isoformat()
        }

SCHEMAS = {
    "clients": {
        "fields": ["client_id", "nom", "prenom", "pays", "date_eff"],
        "generator": gen_clients
    },
    "accounts": {
        "fields": ["account_id", "client_id", "account_type", "currency", "date_eff"],
        "generator": gen_accounts
    },
    "transactions": {
        "fields": [
            "transaction_id", "client_id", "account_id",
            "amount", "currency", "transaction_ts"
        ],
        "generator": gen_transactions
    },
    "contracts": {
        "fields": ["contract_id", "client_id", "contract_type", "status", "date_eff"],
        "generator": gen_contracts
    }
}
