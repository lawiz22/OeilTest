import sys
from pathlib import Path

# Ensure project root is on sys.path so "python.core.*" imports work
# when running this file directly (e.g. VS Code Run button)
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from python.core.extractor import insert_ctrl_index_sql

if __name__ == "__main__":
    insert_ctrl_index_sql(
        ctrl_id="TEST_MANUAL_2025-02-04_Q",
        dataset="clients",
        ctrl_path="clients/period=Q/year=2025/month=02/day=04/ctrl/test.ctrl.json"
    )

    print("DONE INSERT CTRL")