"""
US Validator — validates US Social Security Numbers (SSN) using regex.
"""
import re
import pandas as pd


# SSN format: AAA-GG-SSSS where:
# - Area (AAA): 001-899 (excluding 666)
# - Group (GG): 01-99
# - Serial (SSSS): 0001-9999
_SSN_PATTERN = re.compile(r"^(\d{3})-?(\d{2})-?(\d{4})$")

# Invalid SSNs
_INVALID_AREAS = {"000", "666"}
_INVALID_SSNS = {
    "000-00-0000", "111-11-1111", "222-22-2222", "333-33-3333",
    "444-44-4444", "555-55-5555", "666-66-6666", "777-77-7777",
    "888-88-8888", "999-99-9999", "123-45-6789", "987-65-4321",
}


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate US Social Security Numbers.

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
                "issue_description": "Empty or missing SSN",
            })
            continue

        # Remove spaces
        cleaned = original.replace(" ", "")

        match = _SSN_PATTERN.match(cleaned)
        if not match:
            results.append({
                "original": original,
                "cleaned": original,
                "is_valid": False,
                "issue_description": "Invalid SSN format (expected XXX-XX-XXXX or XXXXXXXXX)",
            })
            continue

        area, group, serial = match.group(1), match.group(2), match.group(3)
        formatted = f"{area}-{group}-{serial}"

        issues = []

        # Check invalid area numbers
        if area in _INVALID_AREAS:
            issues.append(f"Invalid area number: {area}")

        if int(area) >= 900:
            issues.append(f"Area number {area} is in the reserved 900+ range")

        # Check for all-zero groups
        if group == "00":
            issues.append("Group number cannot be 00")

        if serial == "0000":
            issues.append("Serial number cannot be 0000")

        # Check known invalid / test SSNs
        if formatted in _INVALID_SSNS:
            issues.append("Known invalid/test SSN")

        # Mask for security: show only last 4
        masked = f"***-**-{serial}"

        results.append({
            "original": original,
            "cleaned": formatted,
            "is_valid": len(issues) == 0,
            "issue_description": "; ".join(issues) if issues else "",
            "masked": masked,
        })

    return pd.DataFrame(results)
