from sqlalchemy import create_engine, text

class PolicyRepository:

    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)

    def get_datasets(self):
        query = """
        SELECT *
        FROM vigie_policy_dataset
        WHERE enabled = 1
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchall()

    def get_tests_for_dataset(self, dataset_id: int):
        query = """
        SELECT *
        FROM vigie_policy_test
        WHERE dataset_id = :dataset_id
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"dataset_id": dataset_id})
            return result.fetchall()

    def create_policy_test(self, data: dict):
        query = """
        INSERT INTO vigie_policy_test
        (dataset_id, test_code, column_name, hash_algorithm, frequency, enabled)
        VALUES
        (:dataset_id, :test_code, :column_name, :hash_algorithm, :frequency, :enabled)
        """
        with self.engine.begin() as conn:
            conn.execute(text(query), data)