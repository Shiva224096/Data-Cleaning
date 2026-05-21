"""
Text Validator — strips whitespace, normalizes empty strings,
and performs basic text quality checks.
"""
import re
import pandas as pd


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate text fields: strip whitespace, detect empty strings, normalize.

    Kwargs:
        min_length: Minimum required length. Default 0 (no minimum).
        max_length: Maximum allowed length. Default None (no maximum).
        strip_html: Whether to strip HTML tags. Default True.
        normalize_whitespace: Whether to collapse multiple spaces. Default True.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    min_length = int(kwargs.get("min_length", 0))
    max_length = kwargs.get("max_length", None)
    if max_length is not None:
        max_length = int(max_length)
    strip_html = kwargs.get("strip_html", True)
    normalize_ws = kwargs.get("normalize_whitespace", True)

    results = []

    for val in series:
        original = str(val)
        issues = []

        # Step 1: Strip leading/trailing whitespace
        cleaned = original.strip()

        # Step 2: Check for empty / null-like values
        if not cleaned or cleaned.lower() in ("nan", "none", "null"):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or null text value",
            })
            continue

        # Step 3: Strip HTML tags if requested
        if strip_html:
            html_stripped = re.sub(r"<[^>]+>", "", cleaned)
            if html_stripped != cleaned:
                issues.append("HTML tags removed")
                cleaned = html_stripped.strip()

        # Step 4: Normalize whitespace
        if normalize_ws:
            new_cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if new_cleaned != cleaned:
                if not issues or "whitespace" not in str(issues):
                    issues.append("Extra whitespace normalized")
                cleaned = new_cleaned

        # Step 5: Detect problematic characters
        # Check for control characters (except newline, tab)
        control_chars = re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", cleaned)
        if control_chars:
            issues.append(f"Contains {len(control_chars)} control character(s)")
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

        # Step 6: Length checks
        if min_length > 0 and len(cleaned) < min_length:
            issues.append(f"Text too short: {len(cleaned)} chars (min {min_length})")

        if max_length is not None and len(cleaned) > max_length:
            issues.append(f"Text too long: {len(cleaned)} chars (max {max_length})")

        # Step 7: Check for excessive repetition
        if len(cleaned) >= 5:
            # Check if a single character is repeated excessively
            for char in set(cleaned):
                if char != " " and cleaned.count(char) / len(cleaned) > 0.7:
                    issues.append(f"Excessive repetition of character '{char}'")
                    break

        is_valid = len(issues) == 0
        results.append({
            "original": original,
            "cleaned": cleaned,
            "is_valid": is_valid,
            "issue_description": "; ".join(issues) if issues else "",
        })

    return pd.DataFrame(results)
