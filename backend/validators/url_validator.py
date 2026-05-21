"""
URL Validator — validates URLs using the 'validators' library.
"""
import pandas as pd
import validators as url_validators
from urllib.parse import urlparse


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate URLs.

    Kwargs:
        require_https: Whether HTTPS is required. Default False.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    require_https = kwargs.get("require_https", False)
    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing URL",
            })
            continue

        # Auto-prepend scheme if missing
        cleaned = original
        if not cleaned.startswith(("http://", "https://", "ftp://")):
            cleaned = "https://" + cleaned

        # Validate using validators library
        is_valid_url = url_validators.url(cleaned)

        if is_valid_url is not True:
            results.append({
                "original": original,
                "cleaned": original,
                "is_valid": False,
                "issue_description": "Invalid URL format",
            })
            continue

        issues = []
        parsed = urlparse(cleaned)

        # Check HTTPS requirement
        if require_https and parsed.scheme != "https":
            issues.append("URL does not use HTTPS")

        # Check for missing path issues
        if not parsed.netloc:
            issues.append("URL has no domain/host")

        # Normalize: lowercase the scheme and host
        normalized = cleaned
        if parsed.scheme and parsed.netloc:
            normalized = (
                parsed.scheme.lower()
                + "://"
                + parsed.netloc.lower()
                + parsed.path
                + (("?" + parsed.query) if parsed.query else "")
                + (("#" + parsed.fragment) if parsed.fragment else "")
            )

        results.append({
            "original": original,
            "cleaned": normalized,
            "is_valid": len(issues) == 0,
            "issue_description": "; ".join(issues) if issues else "",
        })

    return pd.DataFrame(results)
