import argparse
import os

from python.oeil_policy_manager.json_builder import PolicyJsonBuilder
from python.oeil_policy_manager.lake_writer import LakeWriter
from python.oeil_policy_manager.policy_repository import PolicyRepository
from python.oeil_policy_manager.config import (
    AZURE_SQL_CONN,
    STORAGE_CONN,
    STORAGE_CONTAINER,
)


def export_policy(dataset_id: int):

    print(f"🔎 Loading dataset {dataset_id} from Azure SQL...")

    repo = PolicyRepository(AZURE_SQL_CONN)

    datasets = repo.get_datasets()

    dataset = next(
        (
            row for row in datasets
            if row.policy_dataset_id == dataset_id
        ),
        None,
    )

    if dataset is None:
        raise ValueError(f"Dataset not found for dataset_id={dataset_id}")

    print(f"📦 Building policy JSON for {dataset.dataset_name}...")

    tests = repo.get_tests_for_dataset(dataset_id)

    policy_dict = PolicyJsonBuilder.build(dataset, tests)
    json_content = PolicyJsonBuilder.to_json(policy_dict)

    writer = LakeWriter(os.getenv("OEIL_AZCOPY_DEST"))

    path = (
        f"standardized/_policies/"
        f"{dataset.dataset_name}_{dataset.environment}.policy.json"
    )

    writer.write_policy(
    path=path,
    content=json_content,
)

    print("✅ Policy exported successfully.")
    print("📁 Lake path:", path)


def main():

    parser = argparse.ArgumentParser(
        description="L’ŒIL v2 — Policy Manager CLI"
    )

    parser.add_argument(
        "--export",
        type=int,
        help="Export policy for dataset_id",
    )

    args = parser.parse_args()

    if args.export:
        export_policy(args.export)
    else:
        print("Nothing to do. Use --export <dataset_id>")


if __name__ == "__main__":
    main()