import json


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
                    "enabled": t.enabled
                }
                for t in tests if t.enabled
            ]
        }

    @staticmethod
    def to_json(policy_dict):
        return json.dumps(policy_dict, indent=2)