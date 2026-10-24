"""Capture genuine preselection evidence in the PRIVATE repository.

Call BEFORE running the selector. Candidate input is the full researched,
source-verified pool, never an already published or selected list.
"""
import argparse
import base64
import hashlib
import json
import os
import pathlib
import re
import urllib.error
import urllib.request
import time

API = "https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback"


def validate_candidates(raw):
    pool = json.loads(raw)
    if not isinstance(pool, list) or not pool:
        raise ValueError("A nonempty preselection candidate list is required")
    ids = []
    for item in pool:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(key), str) and item[key].strip()
            for key in ("id", "topic", "source")
        ) or item.get("verified") is not True:
            raise ValueError("Every candidate needs id, topic, source, verified=true")
        ids.append(item["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate candidate IDs")
    return pool


class PrivateRepo:
    def __init__(self, token):
        if not token:
            raise ValueError("Missing private repository token")
        self.token = token

    def api(self, path, method="GET", payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            API + path, data=data, method=method,
            headers={"Authorization": "Bearer " + self.token,
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return json.load(response)
            except urllib.error.HTTPError as error:
                if error.code not in (429,500,502,503,504) or attempt == 2:
                    raise
            except (urllib.error.URLError, TimeoutError):
                if attempt == 2:
                    raise
            time.sleep(2 * (attempt + 1))

    def read(self, path):
        try:
            entry = self.api("/contents/" + path)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
        return base64.b64decode(entry["content"]), entry["sha"]

    def put_immutable(self, path, data):
        existing = self.read(path)
        if existing is not None:
            if existing[0] != data:
                raise ValueError("Conflicting immutable private snapshot: " + path)
            return
        try:
            self.api("/contents/" + path, "PUT", {
                "message": "Capture preselection evidence " + path,
                "content": base64.b64encode(data).decode(),
            })
        except urllib.error.HTTPError as error:
            if error.code not in (409, 422):
                raise
            concurrent = self.read(path)
            if concurrent is None or concurrent[0] != data:
                raise ValueError("Conflicting concurrent private snapshot: " + path) from error
        saved = self.read(path)
        if saved is None or saved[0] != data:
            raise ValueError("Private snapshot readback failed: " + path)


def capture(repo, date, candidates_bytes, *, limit=10, max_per_source=4):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("Invalid date")
    validate_candidates(candidates_bytes)
    if not 1 <= limit <= 15 or max_per_source < 1:
        raise ValueError('Invalid editorial selection parameters')
    profile_entry = repo.read("profile.json")
    if profile_entry is None:
        raise ValueError("Private profile missing")
    profile_bytes, profile_sha = profile_entry
    json.loads(profile_bytes)
    versions = []
    page = 1
    while True:
        batch = repo.api("/issues?state=all&per_page=100&page=" + str(page))
        versions.extend({"number": item["number"], "updated_at": item["updated_at"]}
                        for item in batch if "pull_request" not in item
                        and item["number"] not in (1, 2)
                        and not item.get("title", "").startswith("[TEST"))
        if len(batch) < 100:
            break
        page += 1
    versions.sort(key=lambda item: item["number"])
    versions_bytes = (json.dumps(versions, ensure_ascii=False, indent=2) + "\n").encode()
    paths = {
        "candidates/" + date + ".json": candidates_bytes,
        "snapshots/" + date + "-profile.json": profile_bytes,
        "snapshots/" + date + "-issues.json": versions_bytes,
        "snapshots/" + date + "-selection-parameters.json": (json.dumps({"limit": limit, "max_per_source": max_per_source}, sort_keys=True) + "\n").encode(),
    }
    # Preflight all paths before any write, preventing known conflicts.
    for path, data in paths.items():
        existing = repo.read(path)
        if existing is not None and existing[0] != data:
            raise ValueError("Conflicting immutable private snapshot: " + path)
    for path, data in paths.items():
        repo.put_immutable(path, data)
    return {
        "date": date, "candidate_sha256": hashlib.sha256(candidates_bytes).hexdigest(),
        "profile_sha256": hashlib.sha256(profile_bytes).hexdigest(),
        "profile_blob_sha": profile_sha, "issue_count": len(versions),
        "paths": list(paths),
    }



def verify_existing(repo, date):
    """Fail closed unless all four original preselection files exist and agree."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("Invalid date")
    names = {
        "candidates": "candidates/" + date + ".json",
        "profile": "snapshots/" + date + "-profile.json",
        "issues": "snapshots/" + date + "-issues.json",
        "parameters": "snapshots/" + date + "-selection-parameters.json",
    }
    entries = {}
    for key, path in names.items():
        item = repo.read(path)
        if item is None:
            raise ValueError("Missing original preselection evidence: " + path)
        entries[key] = item[0]
    validate_candidates(entries["candidates"])
    profile = json.loads(entries["profile"])
    issues = json.loads(entries["issues"])
    parameters = json.loads(entries["parameters"])
    if not isinstance(profile, dict) or not isinstance(issues, list):
        raise ValueError("Invalid original profile or issues snapshot")
    if set(parameters) != {"limit", "max_per_source"} or not isinstance(parameters["limit"], int) or not 1 <= parameters["limit"] <= 15 or not isinstance(parameters["max_per_source"], int) or parameters["max_per_source"] < 1:
        raise ValueError("Invalid original selection parameters")
    return {"date": date, "candidate_sha256": hashlib.sha256(entries["candidates"]).hexdigest(),
            "profile_sha256": hashlib.sha256(entries["profile"]).hexdigest(),
            "issue_count": len(issues), "parameters": parameters, "verified_paths": list(names.values())}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--candidates", type=pathlib.Path)
    parser.add_argument("--verify-existing", action="store_true", help="Require all four immutable private snapshots before publication")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-per-source", type=int, default=4)
    args = parser.parse_args()
    repo = PrivateRepo(os.environ.get("MORGENZEITUNG_FEEDBACK_TOKEN"))
    if args.verify_existing:
        result = verify_existing(repo, args.date)
    else:
        if args.candidates is None:
            parser.error("--candidates required when capturing")
        result = capture(repo, args.date, args.candidates.read_bytes(), limit=args.limit,
                         max_per_source=args.max_per_source)
        result["verification"] = verify_existing(repo, args.date)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
