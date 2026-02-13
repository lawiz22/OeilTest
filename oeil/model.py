from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationResult:
    dataset_name: str
    run_time: datetime
    status: str             # OK / KO / WARNING
    actual_rows: int
    message: str
