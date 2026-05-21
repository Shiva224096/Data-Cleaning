"""
Export Service — export cleaned data with DataScrub_Issue_Status column.
"""
from pathlib import Path

import pandas as pd

from config import UPLOAD_DIR


def export_cleaned_file(
    df: pd.DataFrame,
    cleaning_result: dict,
    file_id: str,
    fmt: str = "csv",
) -> Path:
    """
    Build a cleaned DataFrame by replacing original values with cleaned values
    from the cleaning result, appending a DataScrub_Issue_Status column,
    and writing it to disk.

    Args:
        df: Original DataFrame.
        cleaning_result: Output from run_cleaning().
        file_id: UUID of the file session.
        fmt: Output format ('csv' or 'xlsx').

    Returns:
        Path to the exported file.
    """
    out_df = df.copy()

    # Replace original values with cleaned values from validation results
    column_results = cleaning_result.get("column_results", {})
    for col_name, records in column_results.items():
        if col_name in out_df.columns and records:
            cleaned_values = [r.get("cleaned", r.get("original", "")) for r in records]
            if len(cleaned_values) == len(out_df):
                out_df[col_name] = cleaned_values

    # Append issue status column
    issue_status = cleaning_result.get("issue_status", [])
    if len(issue_status) == len(out_df):
        out_df["DataScrub_Issue_Status"] = issue_status
    else:
        out_df["DataScrub_Issue_Status"] = ""

    # Write to file
    suffix = ".csv" if fmt == "csv" else ".xlsx"
    output_path = UPLOAD_DIR / f"{file_id}_cleaned{suffix}"

    if fmt == "csv":
        out_df.to_csv(output_path, index=False)
    else:
        out_df.to_excel(output_path, index=False, engine="openpyxl")

    return output_path
