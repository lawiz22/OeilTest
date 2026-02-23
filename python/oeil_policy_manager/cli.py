import os

try:
    from .json_builder import PolicyJsonBuilder
    from .lake_writer import LakeWriter
    from .policy_repository import PolicyRepository
except ImportError:
    from json_builder import PolicyJsonBuilder
    from lake_writer import LakeWriter
    from policy_repository import PolicyRepository


CONN_STR = os.getenv("OEIL_POLICY_DB_CONN", "")
LAKE_CONN = os.getenv("OEIL_POLICY_LAKE_CONN", "")


def export_policy(dataset_id: int):
    if not CONN_STR:
        raise ValueError("Missing environment variable OEIL_POLICY_DB_CONN")
    if not LAKE_CONN:
        raise ValueError("Missing environment variable OEIL_POLICY_LAKE_CONN")

    repo = PolicyRepository(CONN_STR)

    datasets = repo.get_datasets()
    dataset = next(
        (
            row for row in datasets
            if getattr(row, "dataset_id", None) == dataset_id
            or getattr(row, "policy_dataset_id", None) == dataset_id
        ),
        None,
    )
    if dataset is None:
        raise ValueError(f"Dataset not found for dataset_id={dataset_id}")

    tests = repo.get_tests_for_dataset(dataset_id)

    policy_dict = PolicyJsonBuilder.build(dataset, tests)
    json_content = PolicyJsonBuilder.to_json(policy_dict)

    writer = LakeWriter(LAKE_CONN)
    writer.write_policy(
        container="standardized",
        path=f"_policies/{dataset.dataset_name}_{dataset.environment}.policy.json",
        content=json_content,
    )

    print("Policy exported successfully.")