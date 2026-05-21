"""
Financial Validator — validates IBAN (via python-stdnum), credit card
numbers (Luhn algorithm), and currency amounts (regex).
"""
import re
import pandas as pd

# python-stdnum IBAN validation
from stdnum import iban as iban_validator


# Luhn algorithm for credit card validation
def _luhn_check(number: str) -> bool:
    """Validate a number string using the Luhn algorithm."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse = digits[::-1]
    for i, d in enumerate(reverse):
        if i % 2 == 1:
            d = d * 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _detect_card_brand(number: str) -> str:
    """Detect credit card brand from number prefix."""
    clean = re.sub(r"\D", "", number)
    if clean.startswith("4"):
        return "Visa"
    elif clean[:2] in ("51", "52", "53", "54", "55") or (2221 <= int(clean[:4] or 0) <= 2720):
        return "Mastercard"
    elif clean[:2] in ("34", "37"):
        return "American Express"
    elif clean[:4] in ("6011", "6221", "6229") or clean[:2] == "65":
        return "Discover"
    elif clean[:4] in ("3528",) or (3528 <= int(clean[:4] or 0) <= 3589):
        return "JCB"
    elif clean[:2] in ("36", "38") or clean[:3] in ("300", "301", "302", "303", "304", "305"):
        return "Diners Club"
    return "Unknown"


# Currency pattern: optional symbol, optional sign, digits with optional commas, optional decimal
_CURRENCY_PATTERN = re.compile(
    r"^[\$€£¥₹₩₫₱]?\s*-?\s*\d{1,3}(,\d{3})*(\.\d{1,4})?$|"
    r"^-?\s*\d{1,3}(,\d{3})*(\.\d{1,4})?\s*[\$€£¥₹₩₫₱]?$"
)


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate financial data: IBAN, credit card numbers, or currency amounts.

    Kwargs:
        sub_type: 'iban', 'credit_card', or 'currency'. Default auto-detect.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    sub_type = kwargs.get("sub_type", None)
    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing financial value",
            })
            continue

        # Auto-detect sub_type if not specified
        detected = sub_type
        if not detected:
            clean_digits = re.sub(r"\D", "", original)
            if len(original) >= 15 and original[:2].isalpha():
                detected = "iban"
            elif 13 <= len(clean_digits) <= 19 and clean_digits.isdigit():
                detected = "credit_card"
            else:
                detected = "currency"

        if detected == "iban":
            result = _validate_iban(original)
        elif detected == "credit_card":
            result = _validate_credit_card(original)
        else:
            result = _validate_currency(original)

        results.append(result)

    return pd.DataFrame(results)


def _validate_iban(original: str) -> dict:
    """Validate an IBAN number."""
    cleaned = original.replace(" ", "").replace("-", "").upper()
    try:
        iban_validator.validate(cleaned)
        formatted = iban_validator.format(cleaned)
        return {
            "original": original,
            "cleaned": formatted,
            "is_valid": True,
            "issue_description": "",
        }
    except Exception as e:
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": f"Invalid IBAN: {str(e)}",
        }


def _validate_credit_card(original: str) -> dict:
    """Validate a credit card number using Luhn algorithm."""
    cleaned = re.sub(r"[\s\-]", "", original)

    if not cleaned.isdigit():
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": "Credit card number contains non-digit characters",
        }

    if not _luhn_check(cleaned):
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": "Credit card number fails Luhn check",
        }

    brand = _detect_card_brand(cleaned)
    # Mask all but last 4 digits for security
    masked = "****-****-****-" + cleaned[-4:]

    return {
        "original": original,
        "cleaned": masked,
        "is_valid": True,
        "issue_description": "",
        "card_brand": brand,
    }


def _validate_currency(original: str) -> dict:
    """Validate a currency amount."""
    cleaned = original.strip()

    # Remove currency symbols and whitespace for numeric check
    numeric_str = re.sub(r"[^\d.\-,]", "", cleaned)
    numeric_str = numeric_str.replace(",", "")

    try:
        amount = float(numeric_str)
        formatted = f"{amount:,.2f}"
        return {
            "original": original,
            "cleaned": formatted,
            "is_valid": True,
            "issue_description": "",
        }
    except ValueError:
        return {
            "original": original,
            "cleaned": original,
            "is_valid": False,
            "issue_description": f"Cannot parse as currency amount: '{original}'",
        }
