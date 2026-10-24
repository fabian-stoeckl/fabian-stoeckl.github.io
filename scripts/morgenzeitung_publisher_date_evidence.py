"""Independent publisher-page timestamp evidence; no paywall bypass.

Metadata extraction is advisory until coverage is proven on real publishers.
Only a bounded HTML GET is used; redirects are disabled.
"""
import datetime as dt
from html.parser import HTMLParser
import json
import re
import urllib.error
import urllib.request

from scripts.morgenzeitung_live_source_check import NoRedirect
from scripts.morgenzeitung_source_evidence import validate_source_url

MAX_BYTES = 2097152
DATE_KEYS = {"article:published_time", "datepublished", "pubdate",
             "publishdate", "dc.date.issued"}
ARTICLE_TYPES = {"Article", "NewsArticle", "BlogPosting", "ReportageNewsArticle",
                 "AnalysisNewsArticle", "OpinionNewsArticle", "LiveBlogPosting"}


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.timestamps = []
        self._json_ld = False
        self._json_chunks = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            if key in DATE_KEYS and a.get("content"):
                self.timestamps.append(("meta:" + key, a["content"]))
        if tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._json_ld = True
            self._json_chunks = []

    def handle_data(self, data):
        if self._json_ld:
            self._json_chunks.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._json_ld:
            self._json_ld = False
            try:
                data = json.loads("".join(self._json_chunks))
            except (ValueError, TypeError):
                return
            def visit(node, depth=0, *, root=False):
                if depth > 12:
                    return
                if isinstance(node, list):
                    for value in node:
                        visit(value, depth + 1)
                elif isinstance(node, dict):
                    types = node.get("@type", [])
                    if isinstance(types, str):
                        types = [types]
                    if isinstance(types, list) and any(
                        isinstance(t, str) and t.rsplit("/", 1)[-1] in ARTICLE_TYPES
                        for t in types
                    ):
                        if isinstance(node.get("datePublished"), str):
                            self.timestamps.append(("jsonld:datePublished", node["datePublished"]))
                        # Nested related/recommended articles must not contradict
                        # the publication date of the main page.
                        return
                    for key, value in node.items():
                        if key in ("@graph", "mainEntity", "mainEntityOfPage") or root:
                            if isinstance(value, (dict, list)):
                                visit(value, depth + 1)
            visit(data, root=True)


def normalize_timestamp(value):
    if not isinstance(value, str) or len(value) > 80:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def compare_publisher_timestamp(html, declared):
    parser = MetadataParser()
    parser.feed(html)
    expected = normalize_timestamp(declared)
    if expected is None:
        raise ValueError("Declared timestamp missing timezone or invalid")
    observations = [(source, normalize_timestamp(value))
                    for source, value in parser.timestamps]
    valid = [(source, value) for source, value in observations if value is not None]
    if not valid:
        return {"status": "inconclusive", "reason": "No timezone-aware publication metadata"}
    # Publisher meta tags sometimes omit only the fractional seconds while
    # JSON-LD retains them. Both still identify the same publication second.
    unique = {value.replace(microsecond=0) for _, value in valid}
    if len(unique) > 1:
        # Expose bounded timestamp provenance for genuine publisher diagnostics;
        # never silently pick the date most convenient for the local edition.
        return {"status": "conflict", "reason": "Publisher publication metadata disagree",
                "observations": [{"source": source, "timestamp_utc": value.isoformat()}
                                 for source, value in valid[:12]]}
    observed = max((value for _, value in valid), key=lambda value: value.microsecond)
    # Newsrooms often display only HH:MM on the published article page. When
    # the declared timestamp has zero seconds, compare at that stated minute
    # precision (e.g. 14:11 vs internal JSON-LD 14:11:52). Do not round
    # explicitly second-precision declarations or ignore a date/hour change.
    exact = observed == expected
    minute_level = (expected.second == 0 and expected.microsecond == 0
                    and observed.replace(second=0, microsecond=0) == expected)
    return {"status": "match" if exact or minute_level else "mismatch",
            "resolution": "exact" if exact else "declared-minute" if minute_level else "different",
            "publisher_published_at": observed.isoformat(),
            "declared_published_at": expected.isoformat(),
            "metadata_sources": sorted({source for source, _ in valid})}


def fetch_publisher_metadata(url, declared, opener=None):
    validate_source_url(url)
    opener = opener or urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, method="GET",
                                     headers={"User-Agent": "MorgenzeitungSourceCheck/1.0",
                                              "Accept": "text/html"})
    try:
        with opener.open(request, timeout=8) as response:
            if response.status != 200:
                return {"status": "inconclusive", "reason": "Non-200 publisher response"}
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                return {"status": "inconclusive", "reason": "Publisher did not return HTML"}
            body = response.read(MAX_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ConnectionError):
        return {"status": "inconclusive", "reason": "Publisher metadata unavailable"}
    if len(body) > MAX_BYTES:
        return {"status": "inconclusive", "reason": "HTML exceeds metadata inspection limit"}
    return compare_publisher_timestamp(body.decode("utf-8", errors="replace"), declared)
