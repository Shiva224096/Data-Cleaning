"""
Date Validator — validates and normalizes dates using python-dateutil.
"""
import pandas as pd
from dateutil import parser as date_parser
from dateutil.parser import ParserError


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate date strings and normalize to ISO 8601 (YYYY-MM-DD).

    Kwargs:
        dayfirst: Whether to interpret the first value as the day (European format).
                  Default False.
        yearfirst: Whether to interpret the first value as the year. Default False.
        output_format: strftime format string for output. Default '%Y-%m-%d'.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    dayfirst = kwargs.get("dayfirst", False)
    yearfirst = kwargs.get("yearfirst", False)
    output_format = kwargs.get("output_format", "%Y-%m-%d")

    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", "", "nat"):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing date",
            })
            continue

        try:
            parsed = date_parser.parse(
                original,
                dayfirst=dayfirst,
                yearfirst=yearfirst,
                fuzzy=True,
            )
            cleaned = parsed.strftime(output_format)

            issues = []
            # Warn about ambiguous dates like 01/02/03
            parts = original.replace("-", "/").replace(".", "/").split("/")
            if len(parts) == 3:
                try:
                    nums = [int(p) for p in parts]
                    if all(n <= 31 for n in nums):
                        # All parts could be day/month — ambiguous
                        if nums[0] <= 12 and nums[1] <= 12:
                            issues.append("Ambiguous date format (day/month order unclear)")
                except ValueError:
                    pass

            # Check for unreasonable years
            if parsed.year < 1900:
                issues.append(f"Year {parsed.year} seems too old")
            elif parsed.year > 2100:
                issues.append(f"Year {parsed.year} seems too far in the future")

            results.append({
                "original": original,
                "cleaned": cleaned,
                "is_valid": len(issues) == 0,
                "issue_description": "; ".join(issues) if issues else "",
            })

        except (ParserError, ValueError, OverflowError) as e:
            results.append({
                "original": original,
                "cleaned": original,
                "is_valid": False,
                "issue_description": f"Cannot parse date: {str(e)}",
            })

    return pd.DataFrame(results)
