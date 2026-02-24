from sqlalchemy import create_engine, text


class StructRepository:

    def __init__(self, connection_string: str):

        if not connection_string:
            raise ValueError("OEIL_AZURE_SQL_CONN not defined")

        # Parse ODBC connection string
        params = {
            item.split("=", 1)[0]: item.split("=", 1)[1]
            for item in connection_string.strip(";").split(";")
            if "=" in item
        }

        driver = params.get("Driver", "").replace("{", "").replace("}", "")
        server_raw = params.get("Server", "")
        database = params.get("Database", "")
        uid = params.get("Uid", "")
        pwd = params.get("Pwd", "")

        # Clean server (handle tcp:host,port)
        if server_raw.startswith("tcp:"):
            server_raw = server_raw.replace("tcp:", "")

        if "," in server_raw:
            host, port = server_raw.split(",", 1)
            server = f"{host}:{port}"
        else:
            server = server_raw

        sqlalchemy_url = (
            f"mssql+pyodbc://{uid}:{pwd}@{server}/{database}"
            f"?driver={driver.replace(' ', '+')}"
        )

        self.engine = create_engine(sqlalchemy_url)

    # 🔹 Get dataset by name
    def get_dataset_by_name(self, dataset_name: str):

        query = """
        SELECT *
        FROM ctrl.dataset
        WHERE dataset_name = :dataset_name
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"dataset_name": dataset_name})
            return result.mappings().first()

    # 🔹 Get columns for dataset
    def get_columns_for_dataset(self, dataset_id: int):

        query = """
        SELECT *
        FROM ctrl.dataset_column
        WHERE dataset_id = :dataset_id
        ORDER BY ordinal
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"dataset_id": dataset_id})
            return result.mappings().all()

    # 🔹 Get SQL-generated JSON EXACTLY like SP_REFRESH_STRUCTURAL_HASH
    def get_sql_generated_json(self, dataset_name: str):

        query = """
        DECLARE @json NVARCHAR(MAX);

        SELECT @json =
        (
            SELECT
                d.dataset_name AS [dataset],
                d.source_system,
                d.mapping_version,
                (
                    SELECT
                        c.ordinal,
                        c.column_name AS [name],
                        c.type_source,
                        c.type_sink,
                        c.nullable,
                        c.is_key,
                        c.key_ordinal,
                        c.is_tokenized,
                        c.normalization_rule,
                        c.is_control_excluded
                    FROM ctrl.dataset_column c
                    WHERE c.dataset_id = d.dataset_id
                    ORDER BY c.ordinal
                    FOR JSON PATH
                ) AS columns
            FROM ctrl.dataset d
            WHERE d.dataset_name = :dataset_name
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        );

        SELECT @json AS json_payload;
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"dataset_name": dataset_name})
            return result.scalar()

    def get_dataset_by_id(self, dataset_id: int):

        query = """
        SELECT *
        FROM ctrl.dataset
        WHERE dataset_id = :dataset_id
        """

        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"dataset_id": dataset_id})
            return result.mappings().first()    