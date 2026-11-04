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
    with opener(Request(base + "/", headers=HEADERS), timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("Reader HTML is not publicly accessible")
        html = response.read(1_000_000).decode("utf-8", errors="replace")
        if "Pressespiegel" not in html:
            raise RuntimeError("Reader HTML lacks Pressespiegel marker")

    # A green JSON readback must not conceal stale cached JavaScript or CSS:
    # those files drive the tabs, optional views, and feedback controls.
    asset_root = Path(assets_root) if assets_root is not None else root.parent
    local_html = (asset_root / "index.html").read_text(encoding="utf-8")
    for filename in ("app.js", "style.css"):
        pattern = r"(?:\\./)?" + re.escape(filename) + r"\\?v=([a-zA-Z0-9_-]+)"
        local = re.search(pattern, local_html)
        remote = re.search(pattern, html)
        if not local or not remote or local.group(1) != remote.group(1):
            raise RuntimeError("Public reader asset version is stale: " + filename)
        url = base + "/" + filename + "?v=" + local.group(1)
        with opener(Request(url, headers=HEADERS), timeout=12) as response:
            if response.status != 200:
                raise RuntimeError("Reader asset not accessible: " + filename)
            live_content = response.read(1_000_000)
        if live_content != (asset_root / filename).read_bytes():
            raise RuntimeError("Public reader asset differs from merged main: " + filename)
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
            print(f"LIVE VERIFIED: reader, JS/CSS assets, index and full {day} edition match merged main.")
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
