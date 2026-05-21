"""
Number Validator — validates numeric values using pandas + numpy.
Checks for valid numbers, ranges, and formatting.
"""
import re
import numpy as np
import pandas as pd


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate numeric values.

    Kwargs:
        min_value: Minimum allowed value (inclusive). Default None.
        max_value: Maximum allowed value (inclusive). Default None.
        allow_negative: Whether negative numbers are allowed. Default True.
        decimal_places: Expected decimal places (None = no restriction). Default None.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    min_value = kwargs.get("min_value", None)
    max_value = kwargs.get("max_value", None)
    allow_negative = kwargs.get("allow_negative", True)
    decimal_places = kwargs.get("decimal_places", None)

    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", "", "inf", "-inf"):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing number",
            })
            continue

        # Remove common formatting (commas, currency symbols, spaces)
        cleaned = original
        cleaned = re.sub(r"[,$€£¥₹\s]", "", cleaned)

        # Handle parentheses for negative (accounting format)
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]

        # Try to parse as float
        try:
            num = float(cleaned)
        except ValueError:
            results.append({
                "original": original,
                "cleaned": original,
                "is_valid": False,
                "issue_description": f"Cannot parse as number: '{original}'",
            })
            continue

        issues = []

        # Check NaN / Inf
        if np.isnan(num) or np.isinf(num):
            issues.append("Value is NaN or Infinity")

        # Range checks
        if min_value is not None and num < float(min_value):
            issues.append(f"Value {num} is below minimum {min_value}")

        if max_value is not None and num > float(max_value):
            issues.append(f"Value {num} is above maximum {max_value}")

        # Negative check
        if not allow_negative and num < 0:
            issues.append("Negative values not allowed")

        # Decimal places check
        if decimal_places is not None and "." in cleaned:
            actual_dp = len(cleaned.split(".")[-1])
            if actual_dp > int(decimal_places):
                issues.append(f"Too many decimal places: {actual_dp} (expected max {decimal_places})")

        # Format the cleaned number
        if num == int(num) and "." not in cleaned:
            cleaned_str = str(int(num))
        else:
            cleaned_str = str(num)

        results.append({
            "original": original,
            "cleaned": cleaned_str,
            "is_valid": len(issues) == 0,
            "issue_description": "; ".join(issues) if issues else "",
        })

    return pd.DataFrame(results)
