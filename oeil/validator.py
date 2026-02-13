def validate_row_count(actual: int, min_rows: int, max_rows: int) -> bool:
    return min_rows <= actual <= max_rows
