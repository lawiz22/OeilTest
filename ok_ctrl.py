from extractor import insert_ctrl_index_sql

if __name__ == "__main__":
    insert_ctrl_index_sql(
        ctrl_id="TEST_MANUAL_2025-02-04_Q",
        dataset="clients",
        ctrl_path="clients/period=Q/year=2025/month=02/day=04/ctrl/test.ctrl.json"
    )

    print("DONE INSERT CTRL")