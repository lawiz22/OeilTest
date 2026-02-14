import sys
from pathlib import Path

# Ensure project root is on sys.path so "python.core.*" imports work
# when running this file directly (e.g. PyCharm Run button)
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from datetime import datetime, timedelta
import random

# Import du module extractor complet pour pouvoir modifier la variance globale
import python.core.extractor as extractor
from python.core.extractor import extract_dataset
from python.core.sqlite_schema import ensure_schema


# =====================================================
# GLOBAL CONFIG
# =====================================================
CONFIG = {
    "tables": ["clients"],

    "start_date": "2025-12-01",
    "end_date": "2025-12-30",

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
    "variance_chance": 0.23,     # 23% des runs auront un écart
    "variance_max_pct": 0.10,    # ±10%

    # ============================
    # PERIODICITY
    # ============================
    "period": "H",
    "qs_days": [1, 2, 3, 4, 5, 6, 7],
    "weekly_day": 6
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
# MAIN ORCHESTRATION
# =====================================================
def main():
    ensure_schema()

    # =================================================
    # Injecter la variance dans le module extractor
    # =================================================
    if CONFIG["variance_mode"] == "NONE":
        extractor.VARIANCE_MODE = "NONE"
        extractor.VARIANCE_CHANCE = 0
    else:
        extractor.VARIANCE_MODE = "RANDOM"
        extractor.VARIANCE_CHANCE = CONFIG["variance_chance"]
        extractor.VARIANCE_MAX_PCT = CONFIG["variance_max_pct"]

    start = datetime.fromisoformat(CONFIG["start_date"])
    end = datetime.fromisoformat(CONFIG["end_date"])
    current = start

    while current <= end:
        for table in CONFIG["tables"]:

            # 1️⃣ Volume réel généré
            actual_rows = resolve_row_count()

            # 2️⃣ Extraction (le CTRL calcule maintenant
            #     expected_rows, min/max et checksum lui-même)
            extract_dataset(
                table=table,
                extraction_date=current,
                period=CONFIG["period"],
                rows=actual_rows,
                qs_days=CONFIG["qs_days"],
                weekly_day=CONFIG["weekly_day"]
            )

        current += timedelta(days=1)


if __name__ == "__main__":
    main()
