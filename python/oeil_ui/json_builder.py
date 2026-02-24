import json
from decimal import Decimal
from datetime import datetime, date


class PolicyJsonBuilder:

    @staticmethod
    def build(dataset, tests):

        return {
            "dataset_name": dataset.dataset_name,
            "environment": dataset.environment,
            "synapse_allowed": dataset.synapse_allowed,
            "max_synapse_cost_usd": dataset.max_synapse_cost_usd,
            "tests": [
                {
                    "test_code": t.test_code,
                    "column_name": t.column_name,
                    "hash_algorithm": t.hash_algorithm,
                    "frequency": t.frequency,
                    "threshold_value": t.threshold_value,
                    "checksum_level": t.checksum_level,
                    "column_list": t.column_list,
                    "order_by_column": t.order_by_column,
                    "enabled": t.is_enabled,
                }
                for t in tests
            ],
        }

    @staticmethod
    def _json_serializer(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)

    @staticmethod
    def to_json(policy_dict):
        return json.dumps(
            policy_dict,
            indent=2,
            default=PolicyJsonBuilder._json_serializer,
        )