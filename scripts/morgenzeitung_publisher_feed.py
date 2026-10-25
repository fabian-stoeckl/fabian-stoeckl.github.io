"""Independent DER STANDARD publisher RSS evidence when article HTML redirects to consent.

This is a strictly limited fallback for an article-page consent redirect. An RSS
item must independently identify the same story, title and publication minute.
RSS never proves article body access, and a missing item is a hard failure.
"""
import datetime as dt
from email.utils import parsedate_to_datetime
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from scripts.morgenzeitung_live_source_check import NoRedirect
from scripts.morgenzeitung_source_evidence import validate_source_url

FEED_URL = "https://www.derstandard.at/rss/wirtschaft"
MAX_BYTES = 2 * 1024 * 1024
HOSTS = {"www.derstandard.at", "derstandard.at",
         "www.derstandard.de", "derstandard.de"}


def _normalize(value):
    return "".join(c for c in value.casefold() if c.isalnum())


def verify_standard_feed(candidate, *, opener=None):
    original = validate_source_url(candidate.get("source_url"))
    parsed = urlsplit(original)
    if (candidate.get("source") != "Der Standard"
            or parsed.hostname not in HOSTS or not parsed.path.startswith("/story/")
            or parsed.query):
        raise ValueError("Publisher feed evidence only applies to a Der Standard story")
    expected_title = _normalize(candidate.get("title") or "")
    if not expected_title:
        raise ValueError("Publisher feed evidence requires a candidate title")
    try:
        stamp = dt.datetime.fromisoformat(candidate["published_at"].replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("Timezone-aware publication timestamp required")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid candidate publication timestamp") from exc
    opener = opener or urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(FEED_URL, method="GET",
                                     headers={"Accept": "application/rss+xml,application/xml",
                                              "User-Agent": "MorgenzeitungSourceCheck/1.0"})
    try:
        with opener.open(request, timeout=10) as response:
            if response.status != 200:
                raise ValueError("Publisher RSS did not return HTTP 200")
            ctype = response.headers.get("Content-Type", "").lower()
            if not any(s in ctype for s in ("xml", "rss")):
                raise ValueError("Publisher RSS did not return XML")
            data = response.read(MAX_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError,
            TimeoutError, ConnectionError) as exc:
        raise ValueError("Publisher RSS independently unreachable") from exc
    if len(data) > MAX_BYTES or b"<!DOCTYPE" in data.upper():
        raise ValueError("Publisher RSS is oversized or contains a DTD")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError("Invalid publisher RSS XML") from exc
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        date = item.findtext("pubDate") or ""
        try:
            validate_source_url(link)
            linked = urlsplit(link)
            pub = parsedate_to_datetime(date)
        except (ValueError, TypeError, IndexError):
            continue
        if pub is None or pub.tzinfo is None:
            continue
        if (linked.hostname not in HOSTS or linked.path != parsed.path or linked.query
                or _normalize(title) != expected_title):
            continue
        if (pub.astimezone(dt.timezone.utc).replace(second=0, microsecond=0)
                != stamp.astimezone(dt.timezone.utc).replace(second=0, microsecond=0)):
            raise ValueError("Publisher RSS date contradicts archived publication minute")
        return {"publisher_feed_verified": True, "publisher": "Der Standard",
                "feed_url": FEED_URL, "article_url": link,
                "publication_time": pub.isoformat(), "title_matched": True,
                "limitation": "Publisher RSS proves listing and publication time, not article body access."}
    raise ValueError("Article identity not independently present in publisher RSS")
