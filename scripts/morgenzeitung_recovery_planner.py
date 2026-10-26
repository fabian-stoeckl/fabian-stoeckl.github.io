"""Deterministic, fail-closed recovery planner for an unarchived research pool.

The planner does not invent or download articles. Callers supply independently
researched reserve candidates; every candidate is checked by the same source
preflight used for production. Never use this to mutate archived snapshots.
"""
import argparse
import json
from scripts.morgenzeitung_source_preflight import preflight


def plan_recovery(primary, reserve, date, *, minimum=15, checker=None):
    if not isinstance(primary, list) or not isinstance(reserve, list):
        raise ValueError("Primary and reserve must be lists")
    if minimum < 1:
        raise ValueError("minimum must be positive")
    # Validate every candidate independently. Invalid originals never survive.
    def inspect(pool):
        ready, rejected = [], []
        for candidate in pool:
            if not isinstance(candidate, dict):
                raise ValueError("Candidate must be an object")
            report = preflight([candidate], date, minimum=1, checker=checker)
            if report["ready_count"] == 1:
                ready.append(candidate)
            else:
                rejected.extend(report["blocked"])
        return ready, rejected

    primary_ready, primary_blocked = inspect(primary)
    reserve_ready, reserve_blocked = inspect(reserve)
    selected, seen_ids, seen_urls = [], set(), set()
    for candidate in primary_ready + reserve_ready:
        identity = candidate.get("id")
        url = candidate.get("source_url") or candidate.get("url")
        if not identity or not url:
            continue
        if identity in seen_ids or url in seen_urls:
            continue
        seen_ids.add(identity)
        seen_urls.add(url)
        selected.append(candidate)
    if not selected:
        return {"recovered": False, "candidates": [], "blocked": primary_blocked + reserve_blocked,
                "reason": "No independently verified originals"}
    final = preflight(selected, date, minimum=minimum, checker=checker)
    return {"recovered": final["preflight_passed"], "candidates": selected if final["preflight_passed"] else [],
            "blocked": primary_blocked + reserve_blocked, "ready_count": final["ready_count"],
            "diversity": final["diversity"], "reason": final["next_action"],
            "note": "Only verified candidates; never modify archived snapshots"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary", required=True)
    parser.add_argument("--reserve", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--minimum", type=int, default=15)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.primary, encoding="utf-8") as f:
        primary = json.load(f)
    with open(args.reserve, encoding="utf-8") as f:
        reserve = json.load(f)
    report = plan_recovery(primary, reserve, args.date, minimum=args.minimum)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "candidates"}, ensure_ascii=False))
    if not report["recovered"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
