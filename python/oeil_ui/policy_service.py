class PolicyService:

    def __init__(self, repository):
        self.repo = repository

    def validate_test(self, dataset, test_type, test_data):

        if test_type.requires_synapse and not dataset.synapse_allowed:
            raise ValueError(
                f"Test {test_type.test_code} requires Synapse but dataset does not allow it."
            )

        if test_type.requires_column and not test_data.get("column_name"):
            raise ValueError(
                f"Test {test_type.test_code} requires column_name."
            )

        if test_type.test_code == "DISTRIBUTED_SIGNATURE":
            if not test_data.get("hash_algorithm"):
                raise ValueError("DISTRIBUTED_SIGNATURE requires hash_algorithm.")