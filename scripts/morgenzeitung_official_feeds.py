"""First-party RSS/Atom evidence for blocked original article pages.

Checks identity only: exact official article URL path, normalized title and
timezone-aware publication minute. Never claims fulltext access. Official feed
hosts and publisher article hosts are pinned below, NOT controlled by a
candidate, and HTTP redirects are disabled.
"""
import datetime as dt
from email.utils import parsedate_to_datetime
import unicodedata
from urllib.parse import urlsplit
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

from scripts.morgenzeitung_source_evidence import validate_source_url

MAX_BYTES = 2 * 1024 * 1024
NS = {"atom": "http://www.w3.org/2005/Atom"}
FEEDS = {
    "FAZ": (("https://www.faz.net/rss/aktuell/wirtschaft/",
             "https://www.faz.net/rss/aktuell/"), {"faz.net", "www.faz.net"}),
    "NZZ": (("https://www.nzz.ch/wirtschaft.rss",
             "https://www.nzz.ch/recent.rss"), {"www.nzz.ch", "nzz.ch"}),
    "BBC News": (("https://feeds.bbci.co.uk/news/business/rss.xml",
                  "https://feeds.bbci.co.uk/news/world/rss.xml"),
                 {"www.bbc.com", "bbc.com", "www.bbc.co.uk", "bbc.co.uk"}),
    "DIE ZEIT": (("https://newsfeed.zeit.de/wirtschaft/index",
                  "https://newsfeed.zeit.de/all"), {"www.zeit.de", "zeit.de"}),
    "DER SPIEGEL": (("https://www.spiegel.de/wirtschaft/index.rss",
                     "https://www.spiegel.de/schlagzeilen/index.rss"),
                    {"www.spiegel.de", "spiegel.de"}),
    "Handelsblatt": (("https://feeds.cms.handelsblatt.com/unternehmen",
                      "https://feeds.cms.handelsblatt.com/schlagzeilen"),
                     {"www.handelsblatt.com", "handelsblatt.com"}),
}
ALIASES = {
    "Frankfurter Allgemeine Zeitung": "FAZ",
    "Neue Zürcher Zeitung": "NZZ",
    "BBC": "BBC News",
    "ZEIT": "DIE ZEIT",
    "Der Spiegel": "DER SPIEGEL",
    "SPIEGEL": "DER SPIEGEL",
}
# Maximum two official RSS feeds per publisher; no third-party scrapers/proxies.


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _norm(s):
    return "".join(c for c in unicodedata.normalize("NFKC", s or "").casefold()
                   if c.isalnum())


def _stamp(value):
    if not value:
        raise ValueError("Official RSS item missing publication date")
    try:
        result = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        try:
            result = parsedate_to_datetime(value.strip())
        except (ValueError, TypeError, IndexError) as exc:
            raise ValueError("Official RSS timestamp invalid") from exc
    if result is None or result.tzinfo is None:
        raise ValueError("Official RSS timestamp lacks timezone")
    return result.astimezone(dt.timezone.utc)


def _bounded_feed(url, opener):
    validate_source_url(url)
    req = urllib.request.Request(url, method="GET",
        headers={"Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml",
                 "User-Agent": "MorgenzeitungSourceCheck/1.0"})
    try:
        with opener.open(req, timeout=10) as resp:
            if resp.status != 200:
                raise ValueError("Official publisher feed returned non-200")
            ct = resp.headers.get("Content-Type", "").lower()
            if not any(k in ct for k in ("xml", "rss", "atom")):
                raise ValueError("Official publisher feed is not XML")
            body = resp.read(MAX_BYTES+1)
    except (urllib.error.HTTPError, urllib.error.URLError,
            TimeoutError, ConnectionError) as exc:
        raise ValueError("Official publisher feed unreachable") from exc
    if (len(body)>MAX_BYTES or
            b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper()):
        raise ValueError("Unsafe/oversize publisher XML feed")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise ValueError("Invalid official publisher XML") from exc
    if root.tag not in ("rss", "{http://www.w3.org/2005/Atom}feed"):
        raise ValueError("Unexpected RSS/Atom root")
    return root


def _items(root):
    if root.tag == "rss":
        for item in root.findall("./channel/item"):
            yield (item.findtext("title") or "", item.findtext("link") or "",
                   item.findtext("pubDate") or "")
    else:
        for item in root.findall("atom:entry", NS):
            link = ""
            for el in item.findall("atom:link", NS):
                if el.attrib.get("rel", "alternate") == "alternate":
                    link = el.attrib.get("href", "")
                    break
            yield (item.findtext("atom:title", "", NS), link,
                   item.findtext("atom:published", "", NS)
                   or item.findtext("atom:updated", "", NS))


def verify_official_feed(candidate, *, opener=None):
    """Fetch official RSS and verify EXACT article identity without reading it.

    A missing article/blocked feeds remain inconclusive, never source PASS.
    A matched URL/title with contradictory timestamp is a hard FAIL.
    """
    if not isinstance(candidate, dict):
        raise ValueError("Candidate must be a mapping")
    label = ALIASES.get(candidate.get("source"), candidate.get("source"))
    if label not in FEEDS:
        raise ValueError("No approved official feed for publisher")
    urls, hosts = FEEDS[label]
    article_url = validate_source_url(candidate.get("source_url"))
    target = urlsplit(article_url)
    if (target.hostname not in hosts or not target.path or target.path == "/"
            or target.query):
        raise ValueError("Article URL is not a clean original publisher URL")
    title = _norm(candidate.get("title"))
    if not title or len(title) < 12:
        raise ValueError("Candidate title insufficient for identity verification")
    try:
        stamp = _stamp(candidate.get("published_at"))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Candidate publication time invalid") from exc
    opener = opener or urllib.request.build_opener(NoRedirect)
    errors = []
    for feed_url in urls:
        try:
            root = _bounded_feed(feed_url, opener)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        for feed_title, feed_link, feed_date in _items(root):
            if not feed_link:
                continue
            try:
                validate_source_url(feed_link)
                linked = urlsplit(feed_link)
            except ValueError:
                continue
            # A feed is not trusted to assert a link on another publisher.
            if (linked.hostname not in hosts or linked.path != target.path
                    or linked.query != target.query):
                continue
            if _norm(feed_title) != title:
                raise ValueError("Official publisher feed title contradicts candidate")
            observed = _stamp(feed_date)
            if (observed.replace(second=0, microsecond=0)
                    != stamp.replace(second=0, microsecond=0)):
                raise ValueError("Official publisher feed timestamp contradicts candidate")
            return {
                "publisher_feed_verified": True,
                "publisher": label,
                "feed_url": feed_url,
                "original_url": article_url,
                "title_matched": True,
                "publication_time": observed.isoformat(),
                "content_access": "metadata_only",
                "original_article_http_verified": False,
                "limitation": "Official feed proves article identity/date, never fulltext accessibility."
            }
    raise ValueError("Article not independently confirmed by official publisher feeds"
                     + (" (" + "; ".join(errors[:2]) + ")" if errors else ""))
