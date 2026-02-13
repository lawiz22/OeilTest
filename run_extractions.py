from datetime import datetime, timedelta
import random

from extractor import extract_dataset
from sqlite_schema import ensure_schema

# =====================================================
# GLOBAL CONFIG
# =====================================================
CONFIG = {
    "tables": ["clients"],

    "start_date": "2026-09-01",
    "end_date": "2026-09-30",

    # ============================
    # VOLUME CONFIG
    # ============================
    # FIXED  → toujours le même nombre de lignes
    # RANDOM → volume aléatoire à chaque extraction
    "row_mode": "RANDOM",        # FIXED | RANDOM
    "rows_fixed": 500,
    "rows_random_min": 700,
    "rows_random_max": 1664,

    # ============================
    # VARIANCE (CTRL MISMATCH)
    # ============================
    # NONE   → expected_rows == actual_rows
    # RANDOM → expected_rows peut diverger
    "variance_mode": "RANDOM",   # NONE | RANDOM
    "variance_chance": 0.23,      # 30% des runs auront un écart
    "variance_max_pct": 0.10,    # ±15%

    # ============================
    # PERIODICITY
    # ============================
    "period": "H",
    "qs_days": [1, 2, 3, 4, 5, 6 ,7],     # Mar → Ven
    "weekly_day": 6              # Dimanche
}

# =====================================================
# ROW COUNT RESOLUTION
# =====================================================
def resolve_row_count():
    """
    Détermine le nombre réel de lignes à générer
    """
    if CONFIG["row_mode"] == "FIXED":
        return CONFIG["rows_fixed"]

    if CONFIG["row_mode"] == "RANDOM":
        return random.randint(
            CONFIG["rows_random_min"],
            CONFIG["rows_random_max"]
        )

    raise ValueError("Invalid row_mode")


# =====================================================
# EXPECTED ROWS (CTRL VARIANCE)
# =====================================================
def resolve_expected_rows(actual_rows):
    """
    Détermine le expected_rows écrit dans le CTRL
    Peut volontairement diverger du réel
    """
    if CONFIG["variance_mode"] == "NONE":
        return actual_rows

    # Pas d'écart cette fois-ci
    if random.random() > CONFIG["variance_chance"]:
        return actual_rows

    # Appliquer un delta aléatoire
    delta_pct = random.uniform(
        -CONFIG["variance_max_pct"],
        CONFIG["variance_max_pct"]
    )

    expected = int(actual_rows * (1 + delta_pct))
    return max(expected, 0)


# =====================================================
# MAIN ORCHESTRATION
# =====================================================
def main():
    ensure_schema()

    start = datetime.fromisoformat(CONFIG["start_date"])
    end = datetime.fromisoformat(CONFIG["end_date"])
    current = start

    while current <= end:
        for table in CONFIG["tables"]:

            # 1️⃣ Volume réel généré
            actual_rows = resolve_row_count()

            # 2️⃣ Volume attendu déclaré dans le CTRL
            expected_rows = resolve_expected_rows(actual_rows)

            # 3️⃣ Extraction
            extract_dataset(
                table=table,
                extraction_date=current,
                period=CONFIG["period"],

                # 👇 CONTRAT OFFICIEL
                rows=actual_rows,

                qs_days=CONFIG["qs_days"],
                weekly_day=CONFIG["weekly_day"]
            )

        current += timedelta(days=1)


if __name__ == "__main__":
    main()
