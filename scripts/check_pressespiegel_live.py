"""Post-merge public HTTPS readback: never equate a Git commit with live publication."""
import argparse
import json
import re
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
import sys
import time
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

BASE = "https://fabian-stoeckl.com/Privat/Pressespiegel"
INDEX = Path("Privat/Pressespiegel/data/index.json")
HEADERS = {"User-Agent": "Pressespiegel-public-readback/1.0", "Cache-Control": "no-cache"}


def read_json(url, opener=urlopen):
    with opener(Request(url, headers=HEADERS), timeout=12) as response:
        if response.status != 200:
            raise RuntimeError(f"Unexpected HTTP {response.status} for {url}")
        return json.load(response)


RESOURCE = re.compile(r'(?:src|href)="\./([a-zA-Z0-9_-]+\.(?:js|css))(\?v=[a-zA-Z0-9_-]+)?"')


def local_resources(html):
    """Exactly enumerate every local JS/CSS dependency, without silent exclusions."""
    matches = RESOURCE.findall(html)
    if not matches:
        raise RuntimeError("Reader HTML contains no local scripts or stylesheets")
    versions = {}
    for filename, suffix in matches:
        if not suffix:
            raise RuntimeError("Unversioned local JS/CSS dependency: " + filename)
        if filename in versions and versions[filename] != suffix:
            raise RuntimeError("Conflicting asset versions for " + filename)
        versions[filename] = suffix
    return versions


def check(base=BASE, root=INDEX.parent, opener=urlopen, require_today=False, local_today=None,
          assets_root=None):
    """Verify that the newest committed edition is actually publicly readable."""
    expected = json.loads((root / "index.json").read_text(encoding="utf-8"))
    days = expected["dates"]
    if not days or days != sorted(set(days), reverse=True):
        raise ValueError("Invalid local edition index")
    day = days[0]
    if require_today:
        today = local_today or datetime.now(ZoneInfo("Europe/Vienna")).date()
        if date.fromisoformat(day) != today:
            raise RuntimeError(f"No edition for local Vienna date {today}: newest committed edition is {day}")
    public_index = read_json(base + "/data/index.json", opener)
    if public_index.get("dates") != days:
        raise RuntimeError("Public index is stale or differs from the verified main branch")
    public_issue = read_json(base + "/data/" + day + ".json", opener)
    local_issue = json.loads((root / (day + ".json")).read_text(encoding="utf-8"))
    if public_issue != local_issue:
        raise RuntimeError("Public edition differs from the merged main branch")
    if public_issue.get("preview") is not False or public_issue.get("date") != day:
        raise RuntimeError("Published edition date/preview invalid")
    # Both the newspaper and its separate private-preferences page are active UI.
    # Previously the post-merge check omitted direct-feedback.js entirely.
    asset_root = Path(assets_root) if assets_root is not None else root.parent
    expected_config = json.loads((asset_root / "config.json").read_text(encoding="utf-8"))
    if read_json(base + "/config.json", opener) != expected_config:
        raise RuntimeError("Public feedback configuration differs from merged main")
    for page_name, url_path in (("index.html", "/"),
                                ("praeferenzen.html", "/praeferenzen.html")):
        with opener(Request(base + url_path, headers=HEADERS), timeout=12) as response:
            if response.status != 200:
                raise RuntimeError("Pressespiegel page is not publicly accessible: " + page_name)
            live_html = response.read(1_000_000).decode("utf-8", errors="replace")
            if "Pressespiegel" not in live_html:
                raise RuntimeError("Reader HTML lacks Pressespiegel marker: " + page_name)
        local_html = (asset_root / page_name).read_text(encoding="utf-8")
        local_assets = local_resources(local_html)
        remote_assets = local_resources(live_html)
        if remote_assets != local_assets:
            raise RuntimeError("Public reader asset version is stale: " + page_name)
        for filename, suffix in local_assets.items():
            url = base + "/" + filename + suffix
            with opener(Request(url, headers=HEADERS), timeout=12) as response:
                if response.status != 200:
                    raise RuntimeError("Reader asset not accessible: " + filename)
                live_content = response.read(1_000_000)
            if live_content != (asset_root / filename).read_bytes():
                raise RuntimeError("Public reader asset differs from merged main: " +
                                   page_name + " / " + filename)
    return day


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--attempts", type=int, default=12)
    p.add_argument("--delay", type=int, default=20)
    p.add_argument("--require-today", action="store_true", help="Fail if the newest edition is not from today in Vienna")
    a = p.parse_args()
    if a.attempts < 1 or a.delay < 0:
        p.error("attempts must be >= 1 and delay >= 0")
    last = ""
    for attempt in range(1, a.attempts + 1):
        try:
            day = check(require_today=a.require_today)
            print(f"LIVE VERIFIED: all reader/preferences JS and CSS, index and full {day} edition match merged main.")
            return 0
        except (OSError, ValueError, TypeError, KeyError, RuntimeError, HTTPError, URLError) as e:
            last = str(e)
            print(f"Readback {attempt}/{a.attempts} not confirmed: {last}", flush=True)
            if attempt != a.attempts:
                time.sleep(a.delay)
    print(f"LIVE NOT VERIFIED after {a.attempts} tries: {last}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
