import sys
import json
import argparse
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
# CONFIG FILES
# =====================================================
CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "run_extractions.json"
EXAMPLE_CONFIG_PATH = CONFIG_DIR / "run_extractions.example.json"


def load_config(config_path=None):
    if config_path is not None:
        selected_path = Path(config_path)
    elif DEFAULT_CONFIG_PATH.exists():
        selected_path = DEFAULT_CONFIG_PATH
    else:
        selected_path = EXAMPLE_CONFIG_PATH

    if not selected_path.exists():
        raise FileNotFoundError(
            "Extraction config not found. Expected one of: "
            f"{DEFAULT_CONFIG_PATH} or {EXAMPLE_CONFIG_PATH}."
        )

    with open(selected_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    required_keys = {
        "tables",
        "start_date",
        "end_date",
        "row_mode",
        "rows_fixed",
        "rows_random_min",
        "rows_random_max",
        "variance_mode",
        "variance_chance",
        "variance_max_pct",
        "period",
        "qs_days",
        "weekly_day",
    }

    missing_keys = sorted(required_keys - set(config.keys()))
    if missing_keys:
        raise ValueError(
            f"Invalid extraction config ({selected_path}). Missing keys: {missing_keys}"
        )

    print(f"[INFO] Using extraction config: {selected_path}")
    return config


# =====================================================
# ROW COUNT RESOLUTION
# =====================================================
def resolve_row_count(config):
    """
    Détermine le nombre réel de lignes à générer
    """
    if config["row_mode"] == "FIXED":
        return config["rows_fixed"]

    if config["row_mode"] == "RANDOM":
        return random.randint(
            config["rows_random_min"],
            config["rows_random_max"]
        )

    raise ValueError("Invalid row_mode")


# =====================================================
# MAIN ORCHESTRATION
# =====================================================
def main(config_path=None):
    config = load_config(config_path)

    ensure_schema()

    # =================================================
    # Injecter la variance dans le module extractor
    # =================================================
    if config["variance_mode"] == "NONE":
        extractor.VARIANCE_MODE = "NONE"
        extractor.VARIANCE_CHANCE = 0
    else:
        extractor.VARIANCE_MODE = "RANDOM"
        extractor.VARIANCE_CHANCE = config["variance_chance"]
        extractor.VARIANCE_MAX_PCT = config["variance_max_pct"]

    start = datetime.fromisoformat(config["start_date"])
    end = datetime.fromisoformat(config["end_date"])
    current = start

    while current <= end:
        for table in config["tables"]:

            # 1️⃣ Volume réel généré
            actual_rows = resolve_row_count(config)

            # 2️⃣ Extraction (le CTRL calcule maintenant
            #     expected_rows, min/max et checksum lui-même)
            extract_dataset(
                table=table,
                extraction_date=current,
                period=config["period"],
                rows=actual_rows,
                qs_days=config["qs_days"],
                weekly_day=config["weekly_day"]
            )

        current += timedelta(days=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=None,
        help="Path to extraction JSON config. Defaults to config/run_extractions.json",
    )
    args = parser.parse_args()
    main(config_path=args.config)
