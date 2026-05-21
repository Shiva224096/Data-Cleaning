"""
Cleaning Engine — dispatches each column to the appropriate validator,
collects results, builds per-row DataScrub_Issue_Status strings.
"""
import asyncio
from typing import Any, Callable, Coroutine

import pandas as pd

from validators import (
    email_validator,
    phone_validator,
    name_validator,
    company_validator,
    date_validator,
    number_validator,
    url_validator,
    ip_validator,
    financial_validator,
    indian_validator,
    us_validator,
    identifier_validator,
    zip_validator,
    text_validator,
)
from config import ISSUE_SEPARATOR

# Map type name -> validator module
VALIDATOR_MAP: dict[str, Any] = {
    "email": email_validator,
    "phone": phone_validator,
    "name": name_validator,
    "company": company_validator,
    "date": date_validator,
    "number": number_validator,
    "url": url_validator,
    "ip_address": ip_validator,
    "financial": financial_validator,
    "pan": indian_validator,
    "gst": indian_validator,
    "ssn": us_validator,
    "uuid": identifier_validator,
    "isbn": identifier_validator,
    "vin": identifier_validator,
    "mac_address": identifier_validator,
    "hex_color": identifier_validator,
    "zip_code": zip_validator,
    "text": text_validator,
}

# Validators that need a sub_type kwarg
SUB_TYPE_VALIDATORS = {"pan", "gst", "ssn", "uuid", "isbn", "vin", "mac_address", "hex_color"}


async def run_cleaning(
    df: pd.DataFrame,
    column_mappings: list,
    progress_callback: Callable[..., Coroutine] | None = None,
) -> dict:
    """
    Run validation on each column per the user-confirmed mapping.

    Args:
        df: The source DataFrame (string dtypes).
        column_mappings: List of ColumnMapping objects with .column, .type, .params
        progress_callback: async callable(col_name, col_index, status, details)

    Returns:
        dict with keys:
            - columns_processed: int
            - total_issues: int
            - summary: list of per-column summaries
            - column_results: dict[col_name -> validation DataFrame as records]
            - issue_status: list of per-row DataScrub_Issue_Status strings
    """
    column_results: dict[str, list[dict]] = {}
    summary: list[dict] = []
    total_issues = 0
    num_rows = len(df)

    # Initialize per-row issue list
    row_issues: list[list[str]] = [[] for _ in range(num_rows)]

    for idx, mapping in enumerate(column_mappings):
        col_name = mapping.column
        col_type = mapping.type
        params = mapping.params if hasattr(mapping, "params") else {}

        if progress_callback:
            await progress_callback(col_name, idx, "processing")

        if col_name not in df.columns:
            col_summary = {
                "column": col_name,
                "type": col_type,
                "status": "error",
                "message": f"Column '{col_name}' not found in data.",
                "valid_count": 0,
                "invalid_count": 0,
            }
            summary.append(col_summary)
            if progress_callback:
                await progress_callback(col_name, idx, "error", col_summary)
            continue

        series = df[col_name]
        validator = VALIDATOR_MAP.get(col_type)

        if validator is None:
            col_summary = {
                "column": col_name,
                "type": col_type,
                "status": "error",
                "message": f"No validator for type '{col_type}'.",
                "valid_count": 0,
                "invalid_count": 0,
            }
            summary.append(col_summary)
            if progress_callback:
                await progress_callback(col_name, idx, "error", col_summary)
            continue

        # Build kwargs for the validator
        kwargs = dict(params)
        if col_type in SUB_TYPE_VALIDATORS:
            kwargs["sub_type"] = col_type

        # Run validation (sync — validators are CPU-bound)
        validation_df = await asyncio.to_thread(validator.validate, series, **kwargs)

        # Collect per-row issues
        for row_idx, row in validation_df.iterrows():
            if not row["is_valid"]:
                issue_desc = row.get("issue_description", "")
                if issue_desc:
                    row_issues[row_idx].append(f"[{col_name}] {issue_desc}")

        valid_count = int(validation_df["is_valid"].sum())
        invalid_count = int((~validation_df["is_valid"]).sum())
        total_issues += invalid_count

        # Store results as list of records
        column_results[col_name] = validation_df.to_dict(orient="records")

        col_summary = {
            "column": col_name,
            "type": col_type,
            "status": "done",
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "valid_pct": round((valid_count / num_rows) * 100, 2) if num_rows > 0 else 0,
        }
        summary.append(col_summary)

        if progress_callback:
            await progress_callback(col_name, idx, "done", col_summary)

    # Build DataScrub_Issue_Status per row
    issue_status = [
        ISSUE_SEPARATOR.join(issues) if issues else ""
        for issues in row_issues
    ]

    return {
        "columns_processed": len(column_mappings),
        "total_issues": total_issues,
        "summary": summary,
        "column_results": column_results,
        "issue_status": issue_status,
    }
