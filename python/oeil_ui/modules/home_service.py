from .db import get_engine
from sqlalchemy import text
from .structural_service import preview_structural

def get_dashboard_datasets():
    engine = get_engine()

    query = """
    SELECT
        p.policy_dataset_id,
        p.dataset_name,
        p.environment,
        p.is_active AS policy_enabled,
        p.synapse_allowed,
        d.dataset_id,
        d.mapping_version,
        d.structural_hash
    FROM vigie_policy_dataset p
    OUTER APPLY
    (
        SELECT TOP 1
            dd.dataset_id,
            dd.mapping_version,
            dd.structural_hash
        FROM ctrl.dataset dd
        WHERE dd.dataset_name = p.dataset_name
        ORDER BY dd.dataset_id
    ) d
    ORDER BY p.dataset_name, p.environment
    """

    with engine.connect() as conn:
        rows = conn.execute(text(query)).fetchall()

    dashboard = []

    for row in rows:
        dataset_name = row.dataset_name
        dataset_id = row.dataset_id
        structural_status = "NO STRUCTURE"

        if dataset_id:
            structural_preview = preview_structural(dataset_id)
            structural_status = structural_preview["status"]

        dashboard.append({
            "policy_dataset_id": row.policy_dataset_id,
            "dataset_name": dataset_name,
            "environment": row.environment,
            "policy_enabled": row.policy_enabled,
            "synapse_allowed": row.synapse_allowed,
            "mapping_version": row.mapping_version,
            "structural_status": structural_status
        })

    return dashboard