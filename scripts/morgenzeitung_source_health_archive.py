"""Append-only PRIVATE GitHub source health records and evaluate three-day gaps.

Requires existing MORGENZEITUNG_FEEDBACK_TOKEN with private repository
Contents read/write; never print, log or expose that token. Uses the same
CAS/create-if-absent and remote readback as preselection snapshots.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.error
from zoneinfo import ZoneInfo

from scripts.morgenzeitung_capture_preselection import PrivateRepo
from scripts.morgenzeitung_source_health import feed_health, multi_day_alerts, validate_editorial_report

PRIVATE_PREFIX = "source-health"
SAFE_RUN = re.compile(r"^[A-Za-z0-9_-]{1,65}$")


def today_in_vienna():
    return dt.datetime.now(ZoneInfo("Europe/Vienna")).date().isoformat()


def _private(repo):
    if repo is not None:
        return repo
    token = os.environ.get("MORGENZEITUNG_FEEDBACK_TOKEN")
    if not token:
        raise ValueError("Existing private repository token is required for durable health evidence")
    return PrivateRepo(token)


def archive(repo, path, payload):
    """Never rewrite historical evidence, including reruns of the same day."""
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    repo.put_immutable(path, data)
    saved = repo.read(path)
    if saved is None or saved[0] != data:
        raise ValueError("Private source-health readback did not match original payload")
    return {"path": path, "readback": True, "private_blob_sha": saved[1]}


def latest_editorial(repo, day):
    """Read the latest *stored* daily research ledger, if any, never assume it exists."""
    prefix = PRIVATE_PREFIX + "/editorial/" + day
    try:
        children = repo.api("/contents/" + prefix)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if not isinstance(children, list):
        raise ValueError("Private editorial folder is not a directory")
    names = sorted(
        [item["name"] for item in children
         if item.get("type") == "file" and re.fullmatch(r"run-[A-Za-z0-9_-]{1,65}\.json", item.get("name", ""))],
        reverse=True)
    if not names:
        return None
    # Sorting by immutable numeric workflow run IDs when present gives the
    # latest attempt without ever overwriting its predecessor.
    def order(name):
        ident = name[4:-5]
        return (int(ident) if ident.isdecimal() else -1, name)
    newest = max(names, key=order)
    stored = repo.read(prefix + "/" + newest)
    if stored is None:
        raise ValueError("Listed editorial ledger disappeared during readback")
    return json.loads(stored[0])


def archive_feed_smoke(smoke, day, run_id, repo=None):
    if not SAFE_RUN.fullmatch(str(run_id)):
        raise ValueError("Unsafe run ID")
    result = feed_health(smoke, day, run_id=str(run_id))
    path = f"{PRIVATE_PREFIX}/feeds/{day}/run-{run_id}.json"
    saved = archive(_private(repo), path, result)
    return {**saved, "date": day, "publishers": result["publisher_count"],
            "feed_adapters": result["feed_adapters"],
            "sample_identity_confirmations": result["live_identity_sample_confirmed"]}


def archive_editorial(report, day, run_id, repo=None):
    """Store ONLY a genuinely completed 22-publisher S3/S4 research ledger.

    The runner cannot invent research: it receives the agent's actual findings
    and fails closed on missing sources, access attempts or date mismatches.
    A separate immutable path per execution preserves prior research and reruns.
    """
    if not SAFE_RUN.fullmatch(str(run_id)):
        raise ValueError("Unsafe run ID")
    if not isinstance(report, dict) or report.get("date") != day:
        raise ValueError("Editorial ledger date must match the edition date")
    validate_editorial_report(report)
    path = f"{PRIVATE_PREFIX}/editorial/{day}/run-{run_id}.json"
    saved = archive(_private(repo), path, report)
    return {**saved, "date": day, "publishers": len(report["publishers"]),
            "research_complete": True}


def archive_review(day, run_id, repo=None):
    if not SAFE_RUN.fullmatch(str(run_id)):
        raise ValueError("Unsafe run ID")
    private = _private(repo)
    date = dt.date.fromisoformat(day)
    history = []
    for lag in (2, 1, 0):
        target = (date - dt.timedelta(days=lag)).isoformat()
        record = latest_editorial(private, target)
        if record is not None:
            history.append(record)
    result = multi_day_alerts(day, history)
    result["scope"] = ("Three independently completed research ledgers are required. "
                       "Feed outage alone never proves that a publisher is unavailable.")
    result["run_id"] = str(run_id)
    path = f"{PRIVATE_PREFIX}/assessments/{day}/run-{run_id}.json"
    saved = archive(private, path, result)
    return {**saved, "date": day, "verdict": result["verdict"],
            "confirmed_blackouts": [r["publisher"] for r in result["confirmed_blackouts"]],
            "missing_editorial_dates": result.get("missing_dates", [])}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--smoke", type=Path)
    g.add_argument("--review", action="store_true")
    g.add_argument("--editorial", type=Path, help="Actual completed 22-publisher research JSON; never synthesize")
    p.add_argument("--date", default=None)
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", type=Path, help="Optional local verified result for deduplicated notifications")
    args = p.parse_args()
    day = args.date or today_in_vienna()
    if args.smoke:
        result = archive_feed_smoke(json.loads(args.smoke.read_text()), day, args.run_id)
    elif args.editorial:
        result = archive_editorial(json.loads(args.editorial.read_text()), day, args.run_id)
    else:
        result = archive_review(day, args.run_id)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
