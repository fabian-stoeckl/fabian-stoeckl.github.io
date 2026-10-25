"""Post-publication, append-only *private* acceptance check for a real daily edition.

This verifies actual public HTTPS and original private snapshots; it NEVER
constructs missing editorial inputs or upgrades PARTIAL evidence to PASS.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from scripts.morgenzeitung_publication_audit import live_json
from scripts.morgenzeitung_publisher_date_evidence import fetch_publisher_metadata

PRIVATE_API = "https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback"
REQUIRED = ("candidates/{d}.json", "snapshots/{d}-profile.json",
            "snapshots/{d}-issues.json", "snapshots/{d}-selection-parameters.json",
            "runs/{d}.json", "audits/{d}-live-learning.json",
            "audits/{d}-acceptance.json")
# Append-only final proof may supplement a historical immutable PARTIAL
# acceptance, but may NEVER overwrite it or erase failed prior attempts.
OPTIONAL = ("audits/{d}-acceptance-final.json",
            "audits/{d}-real-feedback-and-profile-verification.json")
REAL_ARTICLES = (
    ("ORF", "https://science.orf.at/stories/3237885/", "2026-10-23T14:28:00+02:00"),
    ("Der Standard", "https://www.derstandard.de/story/3000000345164/von-autos-bis-maschinen-chinas-aggressive-exporte-lassen-europas-motor-stottern", "2026-10-23T18:00:00+02:00"),
    ("Die Presse", "https://www.diepresse.com/41386433/um-dieses-katastrophenbudget-kann-man-die-unis-nur-beneiden", "2026-10-23T14:11:00+02:00"),
    ("Handelsblatt", "https://www.handelsblatt.com/politik/deutschland/chemie-basf-und-evonik-die-besondere-rolle-des-michael-vassiliadis/100263453.html", "2026-10-23T18:09:00+02:00"),
)


class PrivateAPI:
    def __init__(self, token):
        if not token:
            raise ValueError("Missing MORGENZEITUNG_FEEDBACK_TOKEN")
        self.token = token

    def request(self, path, method="GET", body=None):
        req = urllib.request.Request(
            PRIVATE_API + "/contents/" + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": "Bearer " + self.token,
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"},
            method=method)
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    def read(self, path):
        try:
            obj = self.request(path)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
        return base64.b64decode(obj["content"])

    def append(self, path, value):
        """Write a unique immutable proof, then confirm byte-for-byte readback."""
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        before = self.read(path)
        if before is not None:
            if before != raw:
                raise ValueError("Existing immutable evidence differs: " + path)
            return
        try:
            self.request(path, "PUT", {"message": "Archive production acceptance verification",
                                       "content": base64.b64encode(raw).decode()})
        except urllib.error.HTTPError as exc:
            if exc.code not in (409, 422):
                raise
        if self.read(path) != raw:
            raise ValueError("Private immutable evidence readback mismatch: " + path)


def inspect_publisher_pages(articles, *, count=5, fetch=fetch_publisher_metadata):
    """Genuine publisher GETs; access-restricted is inconclusive, never match."""
    checks, hosts = [], set()
    for article in articles:
        url, stamp = article.get("url"), article.get("published_at")
        if not isinstance(url, str) or not isinstance(stamp, str):
            continue
        host = urlsplit(url).hostname
        if not host or host in hosts:
            continue
        hosts.add(host)
        try:
            evidence = fetch(url, stamp)
        except (ValueError, TypeError) as exc:
            evidence = {"status": "inconclusive", "reason": str(exc)}
        checks.append({"source": article.get("source"), "url": url,
                       "declared_published_at": stamp, "evidence": evidence})
        if len(checks) >= count:
            break
    return checks


def evaluate(date, index, edition, private_files, publisher_checks):
    """Pure fail-closed verdict function; suitable for synthetic regression tests."""
    paths = [p.format(d=date) for p in REQUIRED]
    missing = [p for p in paths if private_files.get(p) is None]
    checks = {"public_edition_current": False, "private_origins_complete": not missing,
              "private_snapshots_match_audit": False,
              "public_matches_audited_selection": False,
              "private_run_committed": False, "private_acceptance_pass": False,
              "publisher_metadata_checked": False}
    errors = []
    if isinstance(index, dict) and isinstance(edition, dict):
        dates = index.get("dates")
        articles = edition.get("articles")
        checks["public_edition_current"] = bool(
            isinstance(dates, list) and dates and dates[0] == date
            and edition.get("date") == date and not edition.get("preview")
            and isinstance(articles, list) and 10 <= len(articles) <= 15)
    if not checks["public_edition_current"]:
        errors.append("No verified current public edition")
    def parsed(template):
        value = private_files.get(template.format(d=date))
        if value is None:
            return None
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            errors.append("Invalid private evidence: " + template)
            return None
    audit = parsed("audits/{d}-live-learning.json")
    acceptance = parsed("audits/{d}-acceptance.json")
    final_acceptance = parsed("audits/{d}-acceptance-final.json")
    independent_feedback = parsed("audits/{d}-real-feedback-and-profile-verification.json")
    run = parsed("runs/{d}.json")
    if not missing and isinstance(audit, dict):
        original_candidates = private_files["candidates/" + date + ".json"]
        original_profile = private_files["snapshots/" + date + "-profile.json"]
        issues = parsed("snapshots/{d}-issues.json")
        parameters = parsed("snapshots/{d}-selection-parameters.json")
        checks["private_snapshots_match_audit"] = bool(
            audit.get("candidate_pool_sha256") == hashlib.sha256(original_candidates).hexdigest()
            and audit.get("profile_sha256") == hashlib.sha256(original_profile).hexdigest()
            and issues == audit.get("issue_versions")
            and parameters == audit.get("selection_parameters"))
        selected = (audit.get("selection_comparison") or {}).get("selected_ids", [])
        published = [a.get("id") for a in edition.get("articles", [])] if isinstance(edition, dict) else []
        checks["public_matches_audited_selection"] = bool(
            selected and selected == published
            and (audit.get("publication_audit") or {}).get("publication_verified") is True)
    if isinstance(run, dict):
        commit = run.get("public_merge_commit")
        checks["private_run_committed"] = bool(
            run.get("date") == date and run.get("status") == "PASS"
            and isinstance(commit, str) and re.fullmatch("[0-9a-f]{40}", commit))
    if isinstance(acceptance, dict):
        checks["private_acceptance_pass"] = acceptance.get("date") == date and acceptance.get("verdict") == "PASS"
    if not checks["private_acceptance_pass"] and isinstance(final_acceptance, dict):
        # A historical immutable PARTIAL report is never rewritten to PASS.
        # A separate final evidence file is accepted only with a genuine owner
        # issue/profile replay, a readback-verified S7 run, and the independently
        # verified archived-input -> live-HTTPS article-order comparison.
        final_evidence = final_acceptance.get("evidence") or {}
        source_feedback = (independent_feedback or {}).get("feedback_provenance") or {}
        source_profile = (independent_feedback or {}).get("deterministic_profile_check") or {}
        final_checks = final_acceptance.get("checks") or {}
        required_check_names = set((acceptance or {}).get("checks") or {})
        checks["private_acceptance_pass"] = bool(
            isinstance(acceptance, dict)
            and acceptance.get("date") == date
            and acceptance.get("verdict") == "PARTIAL"
            and final_acceptance.get("date") == date
            and final_acceptance.get("verdict") == "PASS"
            and final_acceptance.get("scope") == "productive_feedback_learning_and_publication_not_full_publisher_access"
            and final_acceptance.get("parent_immutable_acceptance_verdict") == "PARTIAL"
            and required_check_names
            and all((final_checks.get(k) or {}).get("status") == "PASS"
                    for k in required_check_names)
            and final_evidence.get("real_feedback_verification_path")
                  == "audits/" + date + "-real-feedback-and-profile-verification.json"
            and final_evidence.get("live_learning_audit_path")
                  == "audits/" + date + "-live-learning.json"
            and final_evidence.get("private_s7_run_path") == "runs/" + date + ".json"
            and final_evidence.get("public_merge_commit") == (run or {}).get("public_merge_commit")
            and (run or {}).get("private_readback_verified") is True
            and (run or {}).get("status") == "PASS"
            and final_evidence.get("private_run_readback_verified") is True
            and source_feedback.get("status") == "PASS"
            and source_feedback.get("unique_ratings_reconciled_against_public_original_editions", 0) > 0
            and source_profile.get("status") == "PASS"
            and source_profile.get("stored_computed_learning_signals_match") is True
            and isinstance(audit, dict)
            and (audit.get("publication_audit") or {}).get("editorial_effect_verified") is True
        )
    statuses = [r.get("evidence", {}).get("status") for r in publisher_checks]
    checks["publisher_metadata_checked"] = ("match" in statuses and
                                             not any(s in ("mismatch", "conflict") for s in statuses))
    if any(s in ("mismatch", "conflict") for s in statuses):
        errors.append("Publisher metadata contradicts stored article timestamp")
    if missing:
        errors.append("Missing original private files: " + ", ".join(missing))
    # Distinguish detected contradiction from absent supporting evidence.
    verdict = "FAIL" if any("contradicts" in e for e in errors) else (
        "PASS" if all(checks.values()) else "PARTIAL")
    return {"date": date, "verdict": verdict, "checks": checks,
            "missing_original_evidence": missing, "errors": errors,
            "publisher_checks": publisher_checks,
            "note": "PASS requires genuine preselection, live selection match, independently verified feedback/profile/run acceptance and publisher evidence. Synthetic tests never count."}


def immutable_acceptance_path(date, run_id, attempt):
    """Unique append-only report per GitHub run *attempt*, including reruns."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(date)):
        raise ValueError("Invalid edition date")
    if not re.fullmatch(r"[0-9]{1,20}", str(run_id)):
        raise ValueError("Invalid GitHub workflow run ID")
    if not re.fullmatch(r"[1-9][0-9]{0,9}", str(attempt)):
        raise ValueError("Invalid GitHub workflow run attempt")
    return "audits/" + date + "-daily-acceptance-" + str(run_id) + "-attempt-" + str(attempt) + ".json"


def run_daily(date, run_id, private):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("Invalid publication date")
    private_files = {path.format(d=date): private.read(path.format(d=date))
                     for path in REQUIRED + OPTIONAL}
    index = edition = None
    try:
        index = live_json("index.json")
        edition = live_json(date + ".json")
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError,
            TimeoutError, json.JSONDecodeError) as exc:
        print("HTTPS edition readback unavailable:", type(exc).__name__)
    publisher = inspect_publisher_pages(edition.get("articles", [])) if isinstance(edition, dict) else []
    report = evaluate(date, index, edition, private_files, publisher)
    report["checked_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    report["workflow_run_id"] = str(run_id)
    attempt = os.getenv("GITHUB_RUN_ATTEMPT", "1")
    report["workflow_run_attempt"] = str(attempt)
    report["verification_commit"] = os.getenv("GITHUB_SHA")
    # On a GitHub Actions rerun GITHUB_RUN_ID remains unchanged while ATTEMPT
    # increases. Preserve older immutable results instead of overwriting them.
    dest = immutable_acceptance_path(date, run_id, attempt)
    private.append(dest, report)
    print(json.dumps({"date": date, "verdict": report["verdict"],
                      "checks": report["checks"], "saved_private_path": dest},
                     ensure_ascii=False))
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as output:
            output.write("### Morgenzeitung daily acceptance: " + report["verdict"] + "\n")
            output.write("Private immutable verification saved and read back: `" + dest + "`\n")
            for name, passed in report["checks"].items():
                output.write("- " + name + ": " + ("PASS" if passed else "PARTIAL") + "\n")
    return report


def smoke():
    pages = [{"source": name, "url": url, "published_at": stamp}
             for name, url, stamp in REAL_ARTICLES]
    observed = inspect_publisher_pages(pages, count=len(pages))
    statuses = [item["evidence"]["status"] for item in observed]
    for item in observed:
        print("Real publisher:", item["source"], json.dumps(item["evidence"], ensure_ascii=False))
    return {"tested_real_pages": observed, "match_count": statuses.count("match"),
            "mismatch_count": statuses.count("mismatch"),
            "conflict_count": statuses.count("conflict"),
            "inconclusive_count": statuses.count("inconclusive"),
            "verdict": "FAIL" if any(s in ("mismatch", "conflict") for s in statuses)
                       else "PASS" if "match" in statuses else "PARTIAL"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--date", default=None)
    parser.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", "manual"))
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.smoke:
        result = smoke()
        if args.output:
            Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"verdict": result["verdict"], "match_count": result["match_count"],
                          "inconclusive_count": result["inconclusive_count"]}))
        if result["verdict"] == "FAIL":
            raise SystemExit(1)
    else:
        date = args.date or dt.datetime.now(ZoneInfo("Europe/Vienna")).date().isoformat()
        result = run_daily(date, args.run_id, PrivateAPI(os.getenv("MORGENZEITUNG_FEEDBACK_TOKEN")))
        if result["verdict"] != "PASS":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
