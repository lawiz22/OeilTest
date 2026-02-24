from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


class PolicyRepository:

    def __init__(self, connection_string: str):

        parts = dict(
            item.split("=", 1)
            for item in connection_string.strip(";").split(";")
            if "=" in item
        )

        server = parts.get("Server").replace("tcp:", "").split(",")[0]
        database = parts.get("Database")
        username = parts.get("Uid")
        password = parts.get("Pwd")

        url = URL.create(
            "mssql+pyodbc",
            username=username,
            password=password,
            host=server,
            database=database,
            query={
                "driver": "ODBC Driver 18 for SQL Server",
                "Encrypt": "yes",
                "TrustServerCertificate": "no",
            },
        )

        self.engine = create_engine(url, fast_executemany=True)

    # --------------------------------------------------
    # DATASETS
    # --------------------------------------------------
    def get_datasets(self):

        query = """
        SELECT
            policy_dataset_id,
            dataset_name,
            environment,
            synapse_allowed,
            max_synapse_cost_usd,
            is_active
        FROM vigie_policy_dataset
        WHERE is_active = 1
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchall()

    # --------------------------------------------------
    # TESTS
    # --------------------------------------------------
    def get_tests_for_dataset(self, dataset_id: int):

        query = """
        SELECT
            t.policy_test_id,
            t.policy_dataset_id,
            tt.test_code,
            t.column_name,
            t.hash_algorithm,
            t.frequency,
            t.is_enabled,
            t.threshold_value,
            t.checksum_level,
            t.column_list,
            t.order_by_column
        FROM vigie_policy_test t
        INNER JOIN vigie_policy_test_type tt
            ON t.test_type_id = tt.test_type_id
        WHERE t.policy_dataset_id = :dataset_id
          AND t.is_enabled = 1
        """

        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"dataset_id": dataset_id}
            )
            return result.fetchall()