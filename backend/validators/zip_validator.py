"""
ZIP/Postal Code Validator — validates postal codes for multiple countries
using per-country regex patterns.
"""
import re
import pandas as pd


# Postal code patterns per country (ISO 3166-1 alpha-2)
_ZIP_PATTERNS: dict[str, re.Pattern] = {
    "US": re.compile(r"^\d{5}(-\d{4})?$"),                          # 12345 or 12345-6789
    "CA": re.compile(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$"),       # A1A 1A1
    "UK": re.compile(                                                 # Various UK formats
        r"^[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}$"
    ),
    "GB": re.compile(r"^[A-Za-z]{1,2}\d[A-Za-z\d]?\s?\d[A-Za-z]{2}$"),
    "DE": re.compile(r"^\d{5}$"),                                     # German: 5 digits
    "FR": re.compile(r"^\d{5}$"),                                     # French: 5 digits
    "IT": re.compile(r"^\d{5}$"),                                     # Italian: 5 digits
    "ES": re.compile(r"^\d{5}$"),                                     # Spanish: 5 digits
    "NL": re.compile(r"^\d{4}\s?[A-Za-z]{2}$"),                      # Dutch: 1234 AB
    "IN": re.compile(r"^\d{6}$"),                                     # Indian: 6 digits
    "JP": re.compile(r"^\d{3}-?\d{4}$"),                              # Japanese: 123-4567
    "CN": re.compile(r"^\d{6}$"),                                     # Chinese: 6 digits
    "AU": re.compile(r"^\d{4}$"),                                     # Australian: 4 digits
    "BR": re.compile(r"^\d{5}-?\d{3}$"),                              # Brazilian: 12345-678
    "RU": re.compile(r"^\d{6}$"),                                     # Russian: 6 digits
    "KR": re.compile(r"^\d{5}$"),                                     # South Korean: 5 digits
    "MX": re.compile(r"^\d{5}$"),                                     # Mexican: 5 digits
    "ZA": re.compile(r"^\d{4}$"),                                     # South African: 4 digits
    "SE": re.compile(r"^\d{3}\s?\d{2}$"),                             # Swedish: 123 45
    "NO": re.compile(r"^\d{4}$"),                                     # Norwegian: 4 digits
    "DK": re.compile(r"^\d{4}$"),                                     # Danish: 4 digits
    "FI": re.compile(r"^\d{5}$"),                                     # Finnish: 5 digits
    "PL": re.compile(r"^\d{2}-?\d{3}$"),                              # Polish: 12-345
    "CH": re.compile(r"^\d{4}$"),                                     # Swiss: 4 digits
    "AT": re.compile(r"^\d{4}$"),                                     # Austrian: 4 digits
    "BE": re.compile(r"^\d{4}$"),                                     # Belgian: 4 digits
    "PT": re.compile(r"^\d{4}-?\d{3}$"),                              # Portuguese: 1234-567
    "SG": re.compile(r"^\d{6}$"),                                     # Singapore: 6 digits
    "HK": re.compile(r"^$"),                                          # Hong Kong: no postal code
}

# Generic fallback — allow 3-10 alphanumeric characters with optional separators
_GENERIC_PATTERN = re.compile(r"^[A-Za-z0-9\s\-]{3,10}$")


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate postal/ZIP codes.

    Kwargs:
        country: ISO country code (e.g. 'US', 'IN', 'UK'). Default 'US'.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    country = kwargs.get("country", "US").upper()
    pattern = _ZIP_PATTERNS.get(country, _GENERIC_PATTERN)

    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing postal code",
            })
            continue

        cleaned = original.strip()

        # Country-specific normalization
        if country == "CA":
            cleaned = cleaned.upper()
            # Ensure space in middle: A1A1A1 -> A1A 1A1
            no_space = cleaned.replace(" ", "")
            if len(no_space) == 6:
                cleaned = no_space[:3] + " " + no_space[3:]
        elif country in ("UK", "GB"):
            cleaned = cleaned.upper()
        elif country == "US":
            # Strip leading zeros issue? No — US ZIPs can start with 0
            cleaned = cleaned.strip()

        if pattern.match(cleaned):
            results.append({
                "original": original,
                "cleaned": cleaned,
                "is_valid": True,
                "issue_description": "",
            })
        else:
            results.append({
                "original": original,
                "cleaned": cleaned,
                "is_valid": False,
                "issue_description": f"Invalid postal code for country {country}",
            })

    return pd.DataFrame(results)
