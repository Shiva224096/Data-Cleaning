"""
Company Validator — validates company names using TheFuzz for fuzzy
matching to detect duplicates / near-duplicates.
"""
import re
import pandas as pd
from thefuzz import fuzz, process


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate company names by checking formatting and detecting near-duplicates
    using fuzzy string matching.

    Kwargs:
        threshold: Fuzzy match threshold (0-100). Default 85.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    threshold = int(kwargs.get("threshold", 85))
    results = []

    # Collect all non-empty company names for duplicate detection
    all_names: list[str] = []
    name_to_canonical: dict[str, str] = {}  # normalized -> first occurrence

    # First pass: collect and normalize names
    originals = []
    for val in series:
        original = str(val).strip()
        originals.append(original)
        if original and original.lower() not in ("nan", "none", "null", ""):
            normalized = _normalize_company_name(original)
            if normalized not in name_to_canonical:
                name_to_canonical[normalized] = original
            all_names.append(normalized)

    # Build canonical list (unique normalized names)
    canonical_list = list(name_to_canonical.keys())

    # Second pass: validate each entry
    for original in originals:
        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing company name",
            })
            continue

        issues = []
        normalized = _normalize_company_name(original)
        cleaned = _format_company_name(original)

        # Check for suspiciously short names
        if len(original) < 2:
            issues.append("Company name too short")

        # Check for special character overload
        alpha_ratio = sum(c.isalpha() or c.isspace() for c in original) / max(len(original), 1)
        if alpha_ratio < 0.5:
            issues.append("Company name has too many special characters")

        # Fuzzy match for near-duplicates
        if len(canonical_list) > 1:
            matches = process.extract(normalized, canonical_list, scorer=fuzz.token_sort_ratio, limit=3)
            for match_name, score, _ in matches:
                if score >= threshold and match_name != normalized:
                    canonical_original = name_to_canonical.get(match_name, match_name)
                    issues.append(
                        f"Possible duplicate of '{canonical_original}' (similarity: {score}%)"
                    )
                    break  # Only report the best match

        is_valid = len(issues) == 0
        results.append({
            "original": original,
            "cleaned": cleaned,
            "is_valid": is_valid,
            "issue_description": "; ".join(issues) if issues else "",
        })

    return pd.DataFrame(results)


def _normalize_company_name(name: str) -> str:
    """Normalize a company name for comparison: lowercase, remove punctuation, collapse whitespace."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    # Normalize common suffixes
    replacements = {
        " incorporated": " inc",
        " corporation": " corp",
        " limited": " ltd",
        " company": " co",
        " pvt ltd": " pvt ltd",
        " private limited": " pvt ltd",
        " llc": " llc",
        " llp": " llp",
    }
    for old, new in replacements.items():
        if name.endswith(old):
            name = name[: -len(old)] + new
    return name


def _format_company_name(name: str) -> str:
    """Format a company name with proper casing."""
    cleaned = re.sub(r"\s+", " ", name).strip()

    # Title case but keep known abbreviations uppercase
    abbreviations = {"llc", "llp", "inc", "corp", "ltd", "pvt", "co", "plc", "ag", "sa", "gmbh"}

    words = cleaned.split()
    formatted_words = []
    for word in words:
        if word.lower() in abbreviations:
            formatted_words.append(word.upper())
        elif word.isupper() and len(word) <= 5:
            # Likely an abbreviation like "IBM", "HP"
            formatted_words.append(word)
        else:
            formatted_words.append(word.title())

    return " ".join(formatted_words)
