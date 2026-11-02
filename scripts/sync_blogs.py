"""Automatically refresh Noah Smith's five latest posts from Noahpinion RSS."""
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
DEFAULT = Path("Privat/Morgenzeitung-Neu/data/blogs.json")


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "div", "li", "h1", "h2", "h3"):
            self.parts.append(" ")

    def handle_data(self, value):
        self.parts.append(value)


def excerpt(value):
    parser = PlainText()
    parser.feed(value or "")
    cleaned = re.sub(r"\s+", " ", unescape("".join(parser.parts))).strip()
    if len(cleaned) > 230:
        cleaned = cleaned[:227].rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"
    return cleaned


def parse_feed(raw):
    root = ET.fromstring(raw)
    candidates = []
    for item in root.findall(".//channel/item"):
        creator = (item.findtext(DC) or item.findtext("author") or "").strip()
        # Exclude identifiable guest authors; an absent creator is not proof of another author.
        if creator and creator.casefold() not in ("noah smith", "noahpinion"):
            continue
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
            "description": excerpt(item.findtext("description") or "")
        }))
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    posts, seen = [], set()
    for _, post in candidates:
        if post["url"] in seen:
            continue
        posts.append(post)
        seen.add(post["url"])
        if len(posts) == 5:
            break
    if len(posts) < 5:
        raise ValueError("RSS has fewer than five valid Noah Smith posts; previous data kept")
    return {
        "author": "Noah Smith", "name": "Noahpinion",
        "homepage": "https://www.noahpinion.blog/", "feed": FEED,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "posts": posts
    }


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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Updated Noahpinion: " + " | ".join(x["title"] for x in data["posts"]))


if __name__ == "__main__":
    main()
