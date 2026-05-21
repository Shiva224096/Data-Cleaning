"""
Email Validator — validates and normalizes email addresses using the
email-validator library.
"""
import pandas as pd
from email_validator import validate_email, EmailNotValidError


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate email addresses.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing email address",
            })
            continue

        try:
            email_info = validate_email(original, check_deliverability=False)
            normalized = email_info.normalized
            results.append({
                "original": original,
                "cleaned": normalized,
                "is_valid": True,
                "issue_description": "",
            })
        except EmailNotValidError as e:
            results.append({
                "original": original,
                "cleaned": original,
                "is_valid": False,
                "issue_description": f"Invalid email: {str(e)}",
            })

    return pd.DataFrame(results)
