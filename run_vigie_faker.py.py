"""
=====================================================
🔥 RUN VIGIE FAKER — SIMPLE, LISIBLE, EFFICACE
=====================================================

👉 Modifie UNIQUEMENT la section CONFIG.
👉 Puis : python run_vigie_faker.py

CHAOS :
- 0   → parfait
- 40  → réaliste
- 95  → 💩 apocalypse contrôlée
=====================================================
"""

from datetime import datetime, timedelta
from vigie_faker import write_fake_vigie_run

# =====================================================
# 🔧 CONFIG — TOUCHE ICI
# =====================================================

START_DATE = "2026-05-01"
END_DATE   = "2026-05-30"

DATASETS = [
    "transactions",
    "clients",
     "accounts",
     "contracts",
]

PERIODICITY = "Q"
CHAOS_LEVEL = 100

EXPECTED_ROWS_BASE = {
    "clients": 123,
    "accounts": 200,
    "contracts": 180,
    "transactions": 200
}

# =====================================================
# 🚀 MAIN
# =====================================================

def main():
    start = datetime.fromisoformat(START_DATE)
    end   = datetime.fromisoformat(END_DATE)

    current = start
    total = 0

    print("🔥 START VIGIE FAKE GENERATION")
    print(f"📆 {START_DATE} → {END_DATE}")
    print(f"📊 DATASETS = {DATASETS}")
    print(f"🧨 CHAOS = {CHAOS_LEVEL}")
    print("-" * 60)

    while current <= end:
        for dataset in DATASETS:

            ctrl_id = f"{dataset}_{current.date().isoformat()}_{PERIODICITY}"
            expected_rows = EXPECTED_ROWS_BASE.get(dataset, 100)

            write_fake_vigie_run(
                ctrl_id=ctrl_id,
                dataset=dataset,
                periodicity=PERIODICITY,
                extraction_date=current.date().isoformat(),
                expected_rows=expected_rows,
                chaos_level=CHAOS_LEVEL
            )

            total += 1

        current += timedelta(days=1)

    print("-" * 60)
    print(f"✅ DONE — {total} runs generated")

# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":
    main()
