import json
from decimal import Decimal
from datetime import datetime, date


class PolicyJsonBuilder:

    DEFAULT_DISTRIBUTED_SIGNATURE_COMPONENTS = "COUNT|MIN|MAX|SUM"

    @staticmethod
    def _build_integrity_preview(tests):
        integrity = {}

        for t in tests:
            test_code = (getattr(t, "test_code", None) or "").strip().upper()

            if test_code == "DISTRIBUTED_SIGNATURE":
                integrity["distributed_signature"] = {
                    "column": getattr(t, "column_name", None),
                    "algorithm": getattr(t, "hash_algorithm", None) or "SHA256",
                    "components": PolicyJsonBuilder.DEFAULT_DISTRIBUTED_SIGNATURE_COMPONENTS,
                }

            if test_code == "MIN_MAX":
                integrity["min_max"] = {
                    "column": getattr(t, "column_name", None),
                }

        return integrity

    @staticmethod
    def _serialize_policy_test(test):
        payload = {
            "test_code": test.test_code,
        }

        if test.frequency:
            payload["frequency"] = test.frequency

        if test.column_name:
            payload["column_name"] = test.column_name

        if test.threshold_value is not None:
            payload["threshold_value"] = test.threshold_value

        test_code = (test.test_code or "").strip().upper()
        if test.hash_algorithm and test_code == "DISTRIBUTED_SIGNATURE":
            payload["hash_algorithm"] = test.hash_algorithm
            payload["components"] = PolicyJsonBuilder.DEFAULT_DISTRIBUTED_SIGNATURE_COMPONENTS

        return payload

    @staticmethod
    def build(dataset, tests):

        return {
            "dataset_name": dataset.dataset_name,
            "environment": dataset.environment,
            "synapse_allowed": dataset.synapse_allowed,
            "max_synapse_cost_usd": dataset.max_synapse_cost_usd,
            "integrity": PolicyJsonBuilder._build_integrity_preview(tests),
            "tests": [PolicyJsonBuilder._serialize_policy_test(t) for t in tests],
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