"""
Indian Validator — validates Indian PAN and GST numbers using regex patterns.
"""
import re
import pandas as pd


# PAN: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)
# 4th character indicates entity type: C=Company, P=Person, H=HUF, etc.
_PAN_PATTERN = re.compile(r"^[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z]$")

# GST: 2-digit state code + PAN + 1 digit entity + Z + 1 check char
# e.g., 27AAPFU0939F1ZV
_GST_PATTERN = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z][A-Z\d]$")

# Valid state codes (01-37 plus some special codes)
_VALID_STATE_CODES = set(
    [f"{i:02d}" for i in range(1, 38)]
    + ["97", "96"]  # Other territory / special
)


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate Indian identifiers: PAN or GST numbers.

    Kwargs:
        sub_type: 'pan' or 'gst'. Default 'pan'.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    sub_type = kwargs.get("sub_type", "pan")
    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": f"Empty or missing {sub_type.upper()} number",
            })
            continue

        if sub_type == "pan":
            result = _validate_pan(original)
        elif sub_type == "gst":
            result = _validate_gst(original)
        else:
            result = {
                "original": original,
                "cleaned": original,
                "is_valid": False,
                "issue_description": f"Unknown sub_type: {sub_type}",
            }

        results.append(result)

    return pd.DataFrame(results)


def _validate_pan(original: str) -> dict:
    """Validate an Indian PAN number."""
    cleaned = original.upper().replace(" ", "").replace("-", "")

    if len(cleaned) != 10:
        return {
            "original": original,
            "cleaned": cleaned,
            "is_valid": False,
            "issue_description": f"PAN must be 10 characters, got {len(cleaned)}",
        }

    if not _PAN_PATTERN.match(cleaned):
        issues = []
        if not cleaned[:3].isalpha():
            issues.append("First 3 characters must be letters")
        if cleaned[3] not in "ABCFGHLJPT":
            issues.append(f"4th character '{cleaned[3]}' is not a valid entity type (expected A/B/C/F/G/H/L/J/P/T)")
        if not cleaned[4].isalpha():
            issues.append("5th character must be a letter")
        if not cleaned[5:9].isdigit():
            issues.append("Characters 6-9 must be digits")
        if not cleaned[9].isalpha():
            issues.append("10th character must be a letter")

        return {
            "original": original,
            "cleaned": cleaned,
            "is_valid": False,
            "issue_description": "; ".join(issues) if issues else "Invalid PAN format",
        }

    # Determine entity type
    entity_types = {
        "A": "Association of Persons (AOP)",
        "B": "Body of Individuals (BOI)",
        "C": "Company",
        "F": "Firm",
        "G": "Government",
        "H": "Hindu Undivided Family (HUF)",
        "L": "Local Authority",
        "J": "Artificial Juridical Person",
        "P": "Individual/Person",
        "T": "Trust (AOP)",
    }
    entity = entity_types.get(cleaned[3], "Unknown")

    return {
        "original": original,
        "cleaned": cleaned,
        "is_valid": True,
        "issue_description": "",
        "entity_type": entity,
    }


def _validate_gst(original: str) -> dict:
    """Validate an Indian GST number."""
    cleaned = original.upper().replace(" ", "").replace("-", "")

    if len(cleaned) != 15:
        return {
            "original": original,
            "cleaned": cleaned,
            "is_valid": False,
            "issue_description": f"GST must be 15 characters, got {len(cleaned)}",
        }

    if not _GST_PATTERN.match(cleaned):
        return {
            "original": original,
            "cleaned": cleaned,
            "is_valid": False,
            "issue_description": "Invalid GST format",
        }

    # Validate state code
    state_code = cleaned[:2]
    if state_code not in _VALID_STATE_CODES:
        return {
            "original": original,
            "cleaned": cleaned,
            "is_valid": False,
            "issue_description": f"Invalid state code: {state_code}",
        }

    # Extract embedded PAN
    embedded_pan = cleaned[2:12]

    return {
        "original": original,
        "cleaned": cleaned,
        "is_valid": True,
        "issue_description": "",
        "state_code": state_code,
        "embedded_pan": embedded_pan,
    }
