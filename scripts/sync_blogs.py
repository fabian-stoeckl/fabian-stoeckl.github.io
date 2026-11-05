"""Automatically refresh all available Noahpinion RSS posts and retain older cached items."""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

FEED = "https://www.noahpinion.blog/feed"
DC = "{http://purl.org/dc/elements/1.1/}creator"
DEFAULT = Path("Privat/Pressespiegel/data/blogs.json")
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "div", "li", "h1", "h2", "h3"):
            self.parts.append(" ")

    def handle_data(self, value):
        self.parts.append(value)


def excerpt(value, limit=620):
    """A readable feed-based preview, never a claim of independent article analysis."""
    parser = PlainText()
    parser.feed(value or "")
    cleaned = re.sub(r"\\s+", " ", unescape("".join(parser.parts))).strip()
    if len(cleaned) <= limit:
        return cleaned
    prefix = cleaned[:limit]
    sentence_end = max(prefix.rfind(". "), prefix.rfind("? "), prefix.rfind("! "))
    if sentence_end >= int(limit * 0.6):
        return prefix[:sentence_end + 1].strip()
    return prefix.rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"


def parse_feed(raw):
    root = ET.fromstring(raw)
    candidates = []
    for item in root.findall(".//channel/item"):
        creator = (item.findtext(DC) or item.findtext("author") or "").strip()
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        parsed = urlsplit(url)
        if (not title or parsed.scheme != "https" or
                parsed.hostname not in ("www.noahpinion.blog", "noahpinion.blog",
                                        "noahpinion.substack.com") or
                parsed.username or parsed.password):
            continue
        try:
            published = parsedate_to_datetime((item.findtext("pubDate") or "").strip())
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        candidates.append((published, {
            "title": title, "url": url, "published_at": published.date().isoformat(),
            "author": creator, "description": excerpt(item.findtext(CONTENT) or item.findtext("description") or ""),
            "published_time": published.astimezone(timezone.utc).isoformat(timespec="seconds")
        }))
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    posts, seen = [], set()
    for _, post in candidates:
        if post["url"] in seen:
            continue
        posts.append(post)
        seen.add(post["url"])
    if len(posts) < 5:
        raise ValueError("RSS has fewer than five valid Noahpinion posts; previous data kept")
    return {
        "author": "Noah Smith", "name": "Noahpinion",
        "homepage": "https://www.noahpinion.blog/", "feed": FEED,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "posts": posts
    }


def merge_archive(fresh, previous):
    """Keep every valid previously collected post when it falls off the RSS window."""
    if not isinstance(previous, dict) or not isinstance(previous.get("posts"), list):
        raise ValueError("Stored blog archive is invalid; refusing to overwrite it")
    old_summaries = {p.get('url'): p for p in previous['posts'] if isinstance(p, dict) and p.get('summary_source') == 'article' and p.get('summary_de')}
    seen = set()
    combined = []
    for post in [*fresh["posts"], *previous["posts"]]:
        if not isinstance(post, dict):
            continue
        url = post.get("url")
        if not isinstance(url, str):
            continue
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or
                parsed.hostname not in ("www.noahpinion.blog", "noahpinion.blog",
                                        "noahpinion.substack.com") or
                parsed.username or parsed.password):
            continue
        key = parsed.hostname.removeprefix("www.") + parsed.path.rstrip("/").lower()
        if key in seen:
            continue
        if (not isinstance(post.get("title"), str) or not post["title"].strip() or
                not isinstance(post.get("published_at"), str) or
                not re.fullmatch(r"\d{4}-\d{2}-\d{2}", post["published_at"])):
            continue
        seen.add(key)
        if url in old_summaries and not post.get('summary_de'):
            original = old_summaries[url]
            post = {**post, **{field: original[field] for field in (
                'summary_de', 'summary_source', 'summary_access', 'summary_generated_at'
            ) if field in original}}
        combined.append(post)
    combined.sort(key=lambda p: (p["published_at"], p.get("published_time", "")), reverse=True)
    fresh["posts"] = combined
    return fresh


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    request = Request(FEED, headers={
        "User-Agent": "Mozilla/5.0 (compatible; PersonalNewspaperRSS/1.0)",
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.7"
    })
    with urlopen(request, timeout=25) as response:
        payload = response.read(6_000_001)
    if len(payload) > 6_000_000:
        raise ValueError("RSS response too large; previous data kept")
    data = parse_feed(payload)
    if args.output.exists():
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        data = merge_archive(data, previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated Noahpinion archive: {len(data['posts'])} posts; "
          f"newest: {data['posts'][0]['title']}")


if __name__ == "__main__":
    main()
