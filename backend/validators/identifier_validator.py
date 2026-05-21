"""
Identifier Validator — validates UUID, ISBN (stdnum), VIN (stdnum),
MAC addresses, and Hex color codes.
"""
import re
import uuid as uuid_lib
import pandas as pd

# python-stdnum imports
from stdnum import isbn as isbn_validator
from stdnum import exceptions as stdnum_exceptions

# VIN regex (17 chars, no I, O, Q)
_VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")

# VIN check digit weights
_VIN_TRANSLITERATION = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
}
_VIN_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def _vin_check_digit(vin: str) -> bool:
    """Validate VIN check digit (position 9)."""
    try:
        total = sum(
            _VIN_TRANSLITERATION.get(c, 0) * _VIN_WEIGHTS[i]
            for i, c in enumerate(vin)
        )
        remainder = total % 11
        check_char = "X" if remainder == 10 else str(remainder)
        return vin[8] == check_char
    except (KeyError, IndexError):
        return False


# MAC address patterns
_MAC_PATTERNS = [
    re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$"),  # AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF
    re.compile(r"^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$"),      # AABB.CCDD.EEFF
    re.compile(r"^[0-9A-Fa-f]{12}$"),                            # AABBCCDDEEFF
]

# Hex color
_HEX_COLOR_PATTERN = re.compile(r"^#?([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate identifiers: UUID, ISBN, VIN, MAC address, or hex color.

    Kwargs:
        sub_type: One of 'uuid', 'isbn', 'vin', 'mac_address', 'hex_color'.
                  Default 'uuid'.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    sub_type = kwargs.get("sub_type", "uuid")
    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": f"Empty or missing {sub_type}",
            })
            continue

        if sub_type == "uuid":
            result = _validate_uuid(original)
        elif sub_type == "isbn":
            result = _validate_isbn(original)
        elif sub_type == "vin":
            result = _validate_vin(original)
        elif sub_type == "mac_address":
            result = _validate_mac(original)
        elif sub_type == "hex_color":
            result = _validate_hex_color(original)
        else:
            result = {
                "original": original,
                "cleaned": original,
                "is_valid": False,
                "issue_description": f"Unknown identifier sub_type: {sub_type}",
            }

        results.append(result)

    return pd.DataFrame(results)


def _validate_uuid(original: str) -> dict:
    """Validate a UUID string."""
    try:
        parsed = uuid_lib.UUID(original)
        return {
            "original": original,
            "cleaned": str(parsed),
            "is_valid": True,
            "issue_description": "",
            "uuid_version": parsed.version,
        }
    except ValueError:
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": "Invalid UUID format",
        }


def _validate_isbn(original: str) -> dict:
    """Validate an ISBN using python-stdnum."""
    cleaned = original.replace(" ", "").replace("-", "")
    try:
        isbn_validator.validate(cleaned)
        formatted = isbn_validator.format(cleaned)
        isbn_type = "ISBN-13" if len(cleaned) == 13 else "ISBN-10"
        return {
            "original": original,
            "cleaned": formatted,
            "is_valid": True,
            "issue_description": "",
            "isbn_type": isbn_type,
        }
    except (stdnum_exceptions.InvalidChecksum, stdnum_exceptions.InvalidLength,
            stdnum_exceptions.InvalidFormat, stdnum_exceptions.InvalidComponent) as e:
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": f"Invalid ISBN: {str(e)}",
        }
    except Exception as e:
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": f"Invalid ISBN: {str(e)}",
        }


def _validate_vin(original: str) -> dict:
    """Validate a Vehicle Identification Number."""
    cleaned = original.upper().replace(" ", "").replace("-", "")

    if len(cleaned) != 17:
        return {
            "original": original,
            "cleaned": cleaned,
            "is_valid": False,
            "issue_description": f"VIN must be 17 characters, got {len(cleaned)}",
        }

    if not _VIN_PATTERN.match(cleaned):
        return {
            "original": original,
            "cleaned": cleaned,
            "is_valid": False,
            "issue_description": "VIN contains invalid characters (I, O, Q not allowed)",
        }

    issues = []
    if not _vin_check_digit(cleaned):
        issues.append("VIN check digit (position 9) is incorrect")

    # Extract info from VIN
    wmi = cleaned[:3]   # World Manufacturer Identifier
    vds = cleaned[3:9]  # Vehicle Descriptor Section
    vis = cleaned[9:]   # Vehicle Identifier Section
    model_year_char = cleaned[9]

    return {
        "original": original,
        "cleaned": cleaned,
        "is_valid": len(issues) == 0,
        "issue_description": "; ".join(issues) if issues else "",
    }


def _validate_mac(original: str) -> dict:
    """Validate a MAC address."""
    cleaned = original.strip()

    matched = any(p.match(cleaned) for p in _MAC_PATTERNS)
    if not matched:
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": "Invalid MAC address format",
        }

    # Normalize to AA:BB:CC:DD:EE:FF format
    hex_chars = re.sub(r"[^0-9A-Fa-f]", "", cleaned)
    if len(hex_chars) != 12:
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": "MAC address must contain exactly 12 hex digits",
        }

    normalized = ":".join(hex_chars[i:i + 2].upper() for i in range(0, 12, 2))

    return {
        "original": original,
        "cleaned": normalized,
        "is_valid": True,
        "issue_description": "",
    }


def _validate_hex_color(original: str) -> dict:
    """Validate a hex color code."""
    cleaned = original.strip()

    if not _HEX_COLOR_PATTERN.match(cleaned):
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": "Invalid hex color format (expected #RGB, #RRGGBB, or #RRGGBBAA)",
        }

    # Normalize: ensure # prefix and uppercase
    if not cleaned.startswith("#"):
        cleaned = "#" + cleaned

    # Expand shorthand (#RGB -> #RRGGBB)
    hex_part = cleaned[1:]
    if len(hex_part) == 3:
        hex_part = "".join(c * 2 for c in hex_part)
        cleaned = "#" + hex_part

    cleaned = cleaned.upper()

    return {
        "original": original,
        "cleaned": cleaned,
        "is_valid": True,
        "issue_description": "",
    }
