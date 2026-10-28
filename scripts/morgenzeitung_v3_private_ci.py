"""Fail-closed V3 CI check for newly published editions' PRIVATE evidence dossier.

Only the GitHub private feedback repository is consulted; this code never
makes network requests to publishers or to any newspaper article URL.
Unchanged editions are already validated offline by the V3 public CI tests.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.morgenzeitung_v3_engine import validate_edition

REPO = "fabian-stoeckl/morgenzeitung-feedback"
DATE_FILE = re.compile(r"^Privat/Morgenzeitung-3/data/(\d{4}-\d{2}-\d{2})\.json$")
COMMIT = re.compile(r"^[a-f0-9]{40}$")


def changed_dates(files):
    """Only review relevant changed editions, never article link availability."""
    dates = set()
    index_changed = False
    for name in files:
        if name == "Privat/Morgenzeitung-3/data/index.json":
            index_changed = True
        match = DATE_FILE.fullmatch(name)
        if match:
            dates.add(match.group(1))
    if index_changed and not dates:
        raise ValueError("V3 index changed without a dated edition file")
    return sorted(dates)


def files_since(base):
    if not COMMIT.fullmatch(str(base)):
        raise ValueError("Missing valid base SHA for V3 private release check")
    result = subprocess.run(["git", "diff", "--name-only", base, "HEAD"],
                            check=True, capture_output=True, text=True)
    return result.stdout.splitlines()


def fetch_private_dossier(date, token, opener=urlopen):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("Invalid evidence date")
    if not token or len(token) < 20:
        raise ValueError("Private GitHub access token is missing")
    url = ("https://api.github.com/repos/" + REPO
           + "/contents/morgenzeitung-v3/evidence/" + date + ".json")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with opener(request, timeout=25) as response:
            data = json.load(response)
    except (HTTPError, URLError) as e:
        raise ValueError("Private evidence dossier not retrievable for " + date
                         + " (GitHub API access error)") from e
    if not isinstance(data, dict) or data.get("encoding") != "base64":
        raise ValueError("Invalid private evidence representation for " + date)
    try:
        value = json.loads(base64.b64decode(data["content"], validate=False))
    except (ValueError, KeyError, TypeError) as e:
        raise ValueError("Unparseable private evidence dossier for " + date) from e
    if not isinstance(value, dict):
        raise ValueError("Non-object private evidence dossier for " + date)
    return value


def verify_changed(root, files, token, fetcher=fetch_private_dossier):
    days = changed_dates(files)
    if not days:
        return {"checked": [], "preview_skipped": []}
    data_dir = Path(root) / "Privat/Morgenzeitung-3/data"
    index = json.loads((data_dir / "index.json").read_text(encoding="utf-8"))
    listed = index.get("dates", [])
    checked, retired = [], []
    for day in days:
        path = data_dir / (day + ".json")
        if day not in listed:
            # One-time retirement of the non-independent V1-copy preview.
            # No new/real daily edition can be silently removed this way.
            if day == "2026-10-27" and not path.exists():
                retired.append(day)
                continue
            raise ValueError("V3 dated edition is missing from index: " + day)
        edition = json.loads(path.read_text(encoding="utf-8"))
        if edition.get("date") != day:
            raise ValueError("V3 edition/index date mismatch")
        if edition.get("preview") is True:
            raise ValueError("New V3 editions cannot be previews")
        # A new real edition MUST have its private original-source dossier in
        # the feedback repo and must pass the actual private review, not just a
        # self-declared public receipt.
        evidence = fetcher(day, token)
        errors = validate_edition(edition, dossier=evidence, require_dossier=True)
        if errors:
            raise ValueError("V3 private factual review failed for " + day
                             + ": " + ", ".join(errors[:8]))
        checked.append(day)
    return {"checked": checked, "preview_skipped": [], "retired_preview": retired}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    report = verify_changed(args.root, files_since(args.base),
                            os.getenv("MORGENZEITUNG_FEEDBACK_TOKEN", ""))
    print("V3 private dossier check: " + json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
