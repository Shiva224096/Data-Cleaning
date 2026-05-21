"""
Phone Validator — validates and formats phone numbers for ALL countries
using the phonenumbers library. Detects mobile vs landline.
"""
import pandas as pd
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberType


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate phone numbers.

    Kwargs:
        region: Default region code (e.g., 'US', 'IN', 'GB'). Default is 'US'.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    region = kwargs.get("region", "US")
    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing phone number",
            })
            continue

        try:
            parsed = phonenumbers.parse(original, region)

            if not phonenumbers.is_valid_number(parsed):
                results.append({
                    "original": original,
                    "cleaned": original,
                    "is_valid": False,
                    "issue_description": f"Invalid phone number for region {region}",
                })
                continue

            # Format to E.164
            formatted = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )

            # Detect number type
            num_type = phonenumbers.number_type(parsed)
            type_names = {
                PhoneNumberType.MOBILE: "mobile",
                PhoneNumberType.FIXED_LINE: "landline",
                PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
                PhoneNumberType.TOLL_FREE: "toll_free",
                PhoneNumberType.PREMIUM_RATE: "premium_rate",
                PhoneNumberType.VOIP: "voip",
                PhoneNumberType.PERSONAL_NUMBER: "personal",
                PhoneNumberType.PAGER: "pager",
                PhoneNumberType.UAN: "uan",
                PhoneNumberType.UNKNOWN: "unknown",
            }
            detected_type = type_names.get(num_type, "unknown")

            # Get country
            country_code = phonenumbers.region_code_for_number(parsed) or region

            results.append({
                "original": original,
                "cleaned": formatted,
                "is_valid": True,
                "issue_description": "",
                "phone_type": detected_type,
                "country": country_code,
            })

        except NumberParseException as e:
            results.append({
                "original": original,
                "cleaned": original,
                "is_valid": False,
                "issue_description": f"Cannot parse phone number: {str(e)}",
            })

    return pd.DataFrame(results)
