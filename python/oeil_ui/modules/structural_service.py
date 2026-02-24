# modules/structural_service.py

import hashlib
from sqlalchemy import text
from .db import get_engine


def preview_structural(dataset_id: int):

    engine = get_engine()

    sql = """
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
        WHERE d.dataset_id = :dataset_id
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    );

    SELECT @json AS json_payload,
           d.structural_hash
    FROM ctrl.dataset d
    WHERE d.dataset_id = :dataset_id;
    """

    with engine.connect() as conn:
        result = conn.execute(text(sql), {"dataset_id": dataset_id}).mappings().first()

    json_string = result["json_payload"]
    db_hash_bytes = result["structural_hash"]

    new_hash = hashlib.sha256(
        json_string.encode("utf-16le")
    ).hexdigest().upper()

    db_hash_hex = db_hash_bytes.hex().upper() if db_hash_bytes else None

    return {
        "json": json_string,
        "new_hash": new_hash,
        "db_hash": db_hash_hex,
        "status": "MATCH" if db_hash_hex == new_hash else "DRIFT"
    }