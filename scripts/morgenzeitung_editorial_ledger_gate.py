"""Fail closed on missing or incomplete private 22-publisher editorial coverage.

A completed ledger proves documented research attempts, NOT universal source
access, fulltext, or a three-day absence of publisher articles.
"""
import argparse
import json
import os
from pathlib import Path
from scripts.morgenzeitung_capture_preselection import PrivateRepo
from scripts.morgenzeitung_source_health_archive import latest_editorial
from scripts.morgenzeitung_source_health import REQUIRED_SOURCES, validate_editorial_report


def verify_ledger(day, edition, ledger):
    if not isinstance(edition, dict) or edition.get("date") != day:
        raise ValueError("Edition date mismatch")
    if not isinstance(ledger, dict) or ledger.get("date") != day:
        raise ValueError("Private editorial ledger missing or wrong date")
    by_source = validate_editorial_report(ledger)
    if ledger.get("publisher_count") != len(REQUIRED_SOURCES):
        raise ValueError("Private ledger publisher count mismatch")
    selected = {}
    for article in edition.get("articles", []):
        if not isinstance(article, dict) or not isinstance(article.get("source"), str):
            raise ValueError("Invalid published article source")
        source = article["source"]
        selected[source] = selected.get(source, 0) + 1
    for name in REQUIRED_SOURCES:
        row = by_source[name]
        if type(row.get("selected_count")) is not int or row["selected_count"] != selected.get(name, 0):
            raise ValueError("Selected-count mismatch for " + name)
        methods = row["attempted_methods"]
        if "direct_original" not in methods or not any(
                m in methods for m in ("official_publisher_feed", "publisher_metadata", "independent_index")):
            raise ValueError("No documented direct plus alternative research for " + name)
        evidence = row.get("attempt_evidence")
        if not isinstance(evidence, list) or len(evidence) < 2 or not all(
                isinstance(s, str) and "https://" in s for s in evidence):
            raise ValueError("Missing two traceable URL-bearing attempts for " + name)
    return {
        "date": day,
        "verdict": "PASS_SOURCE_RESEARCH_COVERAGE",
        "mandatory_publishers_checked": len(by_source),
        "verified_original_publishers": sum(r["outcome"] == "VERIFIED_ARTICLES" for r in by_source.values()),
        "no_suitable_publishers": sum(r["outcome"] == "NO_SUITABLE_ARTICLES" for r in by_source.values()),
        "no_individual_original_confirmed": [n for n, r in by_source.items()
                                            if r["outcome"] == "NO_VERIFIABLE_ARTICLES"],
        "limitation": "Validates a private 22-source research ledger and published counts; not fulltext, universal eligible originals, independent external re-fetch, or three-day access history."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--edition", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("MORGENZEITUNG_FEEDBACK_TOKEN")
    if not token:
        raise SystemExit("Missing private repository token")
    repo = PrivateRepo(token)
    ledger = latest_editorial(repo, args.date)
    if ledger is None:
        raise SystemExit("AUDIT_GAP: no completed private 22-source editorial ledger")
    result = verify_ledger(args.date, json.loads(args.edition.read_text()), ledger)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
