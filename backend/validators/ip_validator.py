"""
IP Address Validator — validates IPv4 and IPv6 addresses using Python's
built-in ipaddress module.
"""
import ipaddress
import pandas as pd


def validate(series: pd.Series, **kwargs) -> pd.DataFrame:
    """
    Validate IP addresses (both IPv4 and IPv6).

    Kwargs:
        version: Restrict to specific IP version (4 or 6). Default None (accept both).
        reject_private: Whether to flag private/reserved IPs. Default False.

    Returns DataFrame with columns: [original, cleaned, is_valid, issue_description]
    """
    version = kwargs.get("version", None)
    reject_private = kwargs.get("reject_private", False)

    results = []

    for val in series:
        original = str(val).strip()

        if not original or original.lower() in ("nan", "none", "null", ""):
            results.append({
                "original": original,
                "cleaned": "",
                "is_valid": False,
                "issue_description": "Empty or missing IP address",
            })
            continue

        try:
            ip = ipaddress.ip_address(original)
            cleaned = str(ip)  # normalized form
            issues = []

            # Version check
            if version is not None:
                if version == 4 and ip.version != 4:
                    issues.append(f"Expected IPv4 but got IPv{ip.version}")
                elif version == 6 and ip.version != 6:
                    issues.append(f"Expected IPv6 but got IPv{ip.version}")

            # Private/reserved checks
            if reject_private:
                if ip.is_private:
                    issues.append("IP address is in a private range")
                if ip.is_reserved:
                    issues.append("IP address is in a reserved range")
                if ip.is_loopback:
                    issues.append("IP address is a loopback address")

            # Additional info
            ip_info = {
                "version": ip.version,
                "is_private": ip.is_private,
                "is_loopback": ip.is_loopback,
                "is_reserved": ip.is_reserved,
                "is_multicast": ip.is_multicast,
            }

            results.append({
                "original": original,
                "cleaned": cleaned,
                "is_valid": len(issues) == 0,
                "issue_description": "; ".join(issues) if issues else "",
            })

        except ValueError:
            # Try parsing as a network (CIDR notation)
            try:
                network = ipaddress.ip_network(original, strict=False)
                cleaned = str(network)
                results.append({
                    "original": original,
                    "cleaned": cleaned,
                    "is_valid": True,
                    "issue_description": "",
                })
            except ValueError:
                results.append({
                    "original": original,
                    "cleaned": original,
                    "is_valid": False,
                    "issue_description": f"Invalid IP address: '{original}'",
                })

    return pd.DataFrame(results)
