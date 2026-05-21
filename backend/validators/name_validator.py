"""
Name Validator — validates personal names using regex patterns and
normalizes to Title Case.
"""
import re
import pandas as pd


# Characters allowed in names (letters, spaces, hyphens, apostrophes, periods)
_NAME_PATTERN = re.compile(
    r"^[A-Za-zÀ-ÖØ-öø-ÿ\u0100-\u024F\u1E00-\u1EFF' \-\.]{1,100}$"
)

# Suspicious patterns
_DIGIT_PATTERN = re.compile(r"\d")
_SPECIAL_CHARS = re.compile(r"[!@#$%^&*()+=\[\]{};:\"\\|,<>?/~`]")


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate personal names: check for valid characters, normalize to Title Case.

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
                "issue_description": "Empty or missing name",
            })
            continue

        issues = []

        # Check for digits
        if _DIGIT_PATTERN.search(original):
            issues.append("Name contains digits")

        # Check for special characters
        if _SPECIAL_CHARS.search(original):
            issues.append("Name contains special characters")

        # Check overall pattern
        if not _NAME_PATTERN.match(original) and not issues:
            issues.append("Name contains invalid characters")

        # Check length
        if len(original) < 2:
            issues.append("Name too short (less than 2 characters)")

        if len(original) > 100:
            issues.append("Name too long (more than 100 characters)")

        # Normalize: strip extra whitespace and convert to Title Case
        cleaned = re.sub(r"\s+", " ", original).strip()
        cleaned = cleaned.title()

        # Fix common Title Case issues with apostrophes/hyphens
        # e.g., O'Brien, McDonald (simple heuristic)
        cleaned = re.sub(r"'(\w)", lambda m: "'" + m.group(1).upper(), cleaned)
        cleaned = re.sub(r"-(\w)", lambda m: "-" + m.group(1).upper(), cleaned)

        is_valid = len(issues) == 0
        results.append({
            "original": original,
            "cleaned": cleaned,
            "is_valid": is_valid,
            "issue_description": "; ".join(issues) if issues else "",
        })

    return pd.DataFrame(results)
