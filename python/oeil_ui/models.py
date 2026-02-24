from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PolicyDataset:
    id: int
    dataset_name: str
    environment: str
    synapse_allowed: bool
    max_synapse_cost_usd: float
    enabled: bool


@dataclass
class PolicyTestType:
    id: int
    test_code: str
    requires_column: bool
    requires_synapse: bool


@dataclass
class PolicyTest:
    id: int
    dataset_id: int
    test_code: str
    column_name: Optional[str]
    hash_algorithm: Optional[str]
    frequency: str
    enabled: bool