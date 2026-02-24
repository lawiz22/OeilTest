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

    def get_dataset_by_id(self, dataset_id: int):

        query = """
        SELECT
            policy_dataset_id,
            dataset_name,
            environment,
            synapse_allowed,
            max_synapse_cost_usd,
            is_active
        FROM vigie_policy_dataset
        WHERE policy_dataset_id = :dataset_id
        """

        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"dataset_id": dataset_id}
            ).mappings().first()

        return result

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

    def get_test_types(self):

        query = """
        SELECT
            test_type_id,
            test_code,
            description,
            requires_synapse
        FROM vigie_policy_test_type
        ORDER BY test_code
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query)).mappings().all()

        return result

    def get_available_columns_for_dataset(self, dataset_name: str):

        query = """
        SELECT DISTINCT src.column_name
        FROM (
            SELECT c.column_name
            FROM ctrl.dataset d
            INNER JOIN ctrl.dataset_column c
                ON d.dataset_id = c.dataset_id
            WHERE d.dataset_name = :dataset_name

            UNION

            SELECT t.column_name
            FROM vigie_policy_test t
            INNER JOIN vigie_policy_dataset p
                ON t.policy_dataset_id = p.policy_dataset_id
            WHERE p.dataset_name = :dataset_name
              AND t.column_name IS NOT NULL
              AND LTRIM(RTRIM(t.column_name)) <> ''
        ) src
        ORDER BY src.column_name
        """

        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"dataset_name": dataset_name}
            ).mappings().all()

        return result

    def find_test_type_by_id(self, test_type_id: int):

        query = """
        SELECT
            test_type_id,
            test_code,
            description,
            requires_synapse
        FROM vigie_policy_test_type
        WHERE test_type_id = :test_type_id
        """

        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"test_type_id": test_type_id}
            ).mappings().first()

        return result

    def policy_test_exists(
        self,
        dataset_id: int,
        test_type_id: int,
        column_name,
        frequency: str,
        exclude_policy_test_id=None,
    ):

        query = """
        SELECT TOP 1
            policy_test_id
        FROM vigie_policy_test
        WHERE policy_dataset_id = :dataset_id
          AND test_type_id = :test_type_id
          AND ISNULL(column_name, '') = ISNULL(:column_name, '')
          AND ISNULL(frequency, '') = ISNULL(:frequency, '')
          AND is_enabled = 1
                    AND (:exclude_policy_test_id IS NULL OR policy_test_id <> :exclude_policy_test_id)
        """

        with self.engine.connect() as conn:
            row = conn.execute(
                text(query),
                {
                    "dataset_id": dataset_id,
                    "test_type_id": test_type_id,
                    "column_name": column_name,
                    "frequency": frequency,
                    "exclude_policy_test_id": exclude_policy_test_id,
                }
            ).mappings().first()

        return row is not None

    def add_policy_test(
        self,
        dataset_id: int,
        test_type_id: int,
        column_name,
        frequency: str,
        hash_algorithm,
        threshold_value,
    ):

        query = """
        INSERT INTO vigie_policy_test
        (
            policy_dataset_id,
            test_type_id,
            is_enabled,
            frequency,
            threshold_value,
            column_name,
            hash_algorithm
        )
        OUTPUT INSERTED.policy_test_id
        VALUES
        (
            :dataset_id,
            :test_type_id,
            1,
            :frequency,
            :threshold_value,
            :column_name,
            :hash_algorithm
        )
        """

        with self.engine.begin() as conn:
            row = conn.execute(
                text(query),
                {
                    "dataset_id": dataset_id,
                    "test_type_id": test_type_id,
                    "frequency": frequency,
                    "threshold_value": threshold_value,
                    "column_name": column_name,
                    "hash_algorithm": hash_algorithm,
                }
            ).mappings().first()

        if not row or row.get("policy_test_id") is None:
            raise RuntimeError("Insert completed but no policy_test_id was returned")

        return row["policy_test_id"]

    def get_policy_test_by_id(self, dataset_id: int, policy_test_id: int):

        query = """
        SELECT
            t.policy_test_id,
            t.policy_dataset_id,
            t.test_type_id,
            tt.test_code,
            t.column_name,
            t.frequency,
            t.hash_algorithm,
            t.threshold_value,
            t.is_enabled
        FROM vigie_policy_test t
        INNER JOIN vigie_policy_test_type tt
            ON t.test_type_id = tt.test_type_id
        WHERE t.policy_dataset_id = :dataset_id
          AND t.policy_test_id = :policy_test_id
        """

        with self.engine.connect() as conn:
            row = conn.execute(
                text(query),
                {
                    "dataset_id": dataset_id,
                    "policy_test_id": policy_test_id,
                },
            ).mappings().first()

        return row

    def update_policy_test(
        self,
        dataset_id: int,
        policy_test_id: int,
        column_name,
        frequency: str,
        hash_algorithm,
        threshold_value,
    ):

        query = """
        UPDATE vigie_policy_test
        SET
            column_name = :column_name,
            frequency = :frequency,
            hash_algorithm = :hash_algorithm,
            threshold_value = :threshold_value
        WHERE policy_dataset_id = :dataset_id
          AND policy_test_id = :policy_test_id
        """

        with self.engine.begin() as conn:
            result = conn.execute(
                text(query),
                {
                    "dataset_id": dataset_id,
                    "policy_test_id": policy_test_id,
                    "column_name": column_name,
                    "frequency": frequency,
                    "hash_algorithm": hash_algorithm,
                    "threshold_value": threshold_value,
                },
            )

        return result.rowcount

    def delete_policy_test(self, dataset_id: int, policy_test_id: int):

        query = """
        DELETE FROM vigie_policy_test
        WHERE policy_test_id = :policy_test_id
          AND policy_dataset_id = :dataset_id
        """

        with self.engine.begin() as conn:
            result = conn.execute(
                text(query),
                {
                    "policy_test_id": policy_test_id,
                    "dataset_id": dataset_id,
                }
            )

        return result.rowcount