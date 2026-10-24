"""Offline structural checks for source provenance (not proof of a live fetch)."""
from urllib.parse import urlsplit
import ipaddress
import re


def validate_source_url(value):
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError("Missing or oversized original article URL")
    try:
        url = urlsplit(value)
        hostname = url.hostname
        port = url.port
    except ValueError as exc:
        raise ValueError("Malformed original article URL") from exc
    if (url.scheme != "https" or not hostname or url.username is not None
            or url.password is not None or port not in (None, 443)
            or url.fragment or not re.fullmatch(r"[a-zA-Z0-9.-]+", hostname)):
        raise ValueError("Original article URL must be a clean HTTPS publisher URL")
    if hostname.lower() in ("localhost", "localhost.localdomain") or hostname.endswith(".local"):
        raise ValueError("Local URLs are not article sources")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ValueError("IP addresses are not article sources")
    if "." not in hostname or any(not part for part in hostname.split(".")):
        raise ValueError("Original article URL lacks valid publisher hostname")
    return value


def audit_sources(candidates):
    if not isinstance(candidates, list):
        raise ValueError("Candidates must be a list")
    missing = []
    invalid = []
    for i, item in enumerate(candidates):
        if not isinstance(item, dict):
            invalid.append(i)
            continue
        url = item.get("source_url")
        original = item.get("original_url")
        if original is not None and original != url:
            invalid.append(item.get("id", i))
            continue
        if url is None:
            missing.append(item.get("id", i))
            continue
        try:
            validate_source_url(url)
        except ValueError:
            invalid.append(item.get("id", i))
    return {"candidate_count": len(candidates), "url_present_count": len(candidates)-len(missing)-len(invalid),
            "missing_original_url_ids": missing, "invalid_original_url_ids": invalid,
            "source_url_structure_verified": not missing and not invalid,
            "limitation": "Structural HTTPS URL validation cannot prove that the page was fetched, is genuine or matches the summary."}
