from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class DatasetConfig:
    dataset_name: str
    frequency: str          # Q, QS, H, M
    mode: str               # COURANT | REPRISE
    date_debut_eff: Optional[date]
    date_fin_eff: Optional[date]
    expected_min_rows: int
    expected_max_rows: int
