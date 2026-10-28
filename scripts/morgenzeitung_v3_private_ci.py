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
DATE_FILE = re.compile(r"^Privat/Persoenliche-Zeitung/(?:[^/]+/)*data/(\d{4}-\d{2}-\d{2})\.json$")
COMMIT = re.compile(r"^[a-f0-9]{40}$")


def changed_dates(files):
    """Only review relevant changed editions, never article link availability."""
    dates = set()
    index_changed = False
    for name in files:
        if name.startswith("Privat/Persoenliche-Zeitung/") and name.endswith("/data/index.json"):
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
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-[a-z0-9-]+)?", date):
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


REGISTRY="services/morgenzeitung-v3/editions.json"


def registered_editions(root):
    path=Path(root)/REGISTRY
    records=json.loads(path.read_text())["editions"] if path.exists() else [
        {"id":"regular","data_dir":"Privat/Persoenliche-Zeitung/data","dossier_suffix":""}]
    found={}
    for row in records:
        folder=row.get("data_dir","")
        if (not re.fullmatch(r"Privat/Persoenliche-Zeitung/(?:[a-zA-Z0-9_-]+/)*data",folder)
            or folder in found or not re.fullmatch(r"(?:-[a-z0-9-]+)?",row.get("dossier_suffix",""))):
            raise ValueError("Invalid/duplicate edition registry entry")
        found[folder]=row
    return found


def public_edition_paths(root):
    root=Path(root)
    registered=registered_editions(root)
    paths=[]
    for folder in registered:
        data=root/folder
        index=json.loads((data/"index.json").read_text())
        days=index.get("dates",[])
        if not days or days!=sorted(set(days),reverse=True):raise ValueError("Invalid date index")
        disk={p.stem for p in data.glob("????-??-??.json")}
        if disk!=set(days):raise ValueError("Orphan/unlisted edition JSON")
        for day in days:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",day):raise ValueError("Invalid index date")
            path=data/(day+".json")
            if json.loads(path.read_text()).get("date")!=day:raise ValueError("Edition date mismatch")
            paths.append(path)
    for path in (root/"Privat/Persoenliche-Zeitung").rglob("*.json"):
        if path.parent.name=="data" and path.parent.relative_to(root).as_posix() not in registered:
            raise ValueError("Unregistered public edition directory: "+str(path.parent))
    return paths


def verify_changed(root, files, token, fetcher=fetch_private_dossier):
    # Registry changes must recheck every mapped dossier, not merely its syntax.
    records=registered_editions(root)
    targets={name for name in files if DATE_FILE.fullmatch(name)}
    if REGISTRY in files:
        targets.update(path.relative_to(Path(root)).as_posix() for path in public_edition_paths(root))
    for name in files:
        if name.startswith("Privat/Persoenliche-Zeitung/") and name.endswith("/data/index.json"):
            folder=str(Path(name).parent)
            if not any(str(Path(p).parent)==folder for p in targets):
                raise ValueError("V3 index changed without a dated edition file")
    checked=[]
    for name in sorted(targets):
        day=DATE_FILE.fullmatch(name).group(1)
        folder=str(Path(name).parent)
        if folder not in records:raise ValueError("Unregistered public edition directory: "+folder)
        index=json.loads((Path(root)/folder/"index.json").read_text())
        if day not in index.get("dates",[]):raise ValueError("V3 dated edition is missing from index: "+day)
        edition=json.loads((Path(root)/name).read_text())
        if edition.get("date")!=day:raise ValueError("V3 edition/index date mismatch")
        if edition.get("preview") is True:raise ValueError("New V3 editions cannot be previews")
        record=records[folder]
        key=record.get("dossier_overrides",{}).get(day,day+record.get("dossier_suffix",""))
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-[a-z0-9-]+)?",key):raise ValueError("Invalid dossier key")
        evidence=fetcher(key,token)
        errors=validate_edition(edition,dossier=evidence,require_dossier=True)
        if errors:raise ValueError("V3 private factual review failed for "+day+": "+", ".join(errors[:8]))
        checked.append(day)
    return {"checked":checked}


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
