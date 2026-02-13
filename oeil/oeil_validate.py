import csv
import sys
import json
from pathlib import Path
from datetime import datetime

if len(sys.argv) < 3:
    print("Usage: python oeil_validate.py <csv_file> <table_name>")
    sys.exit(1)

CSV_FILE = sys.argv[1]
TABLE_NAME = sys.argv[2]

csv_path = Path(CSV_FILE).resolve()

with open(csv_path, newline='', encoding='utf-8') as f:
    csv_count = sum(1 for _ in csv.reader(f)) - 1

result = {
    "dataset": TABLE_NAME,
    "expected_rows": csv_count,
    "run_ts": datetime.utcnow().isoformat()
}

output_file = Path("oeil_result.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print(f"👁️ Résultat généré : {output_file}")
print(result)
