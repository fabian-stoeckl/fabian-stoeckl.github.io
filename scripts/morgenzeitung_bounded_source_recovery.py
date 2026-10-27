"""Bounded fail-closed retry of unarchived Morgenzeitung source candidates.

This is a reusable CLI for the scheduled editorial agent, NOT a scheduler or
article generator. All network identity checks are the existing first-party
checker; the independent final source-preflight is never weakened.
"""
import argparse
import json
from pathlib import Path

from scripts.morgenzeitung_candidate_triage import triage
from scripts.morgenzeitung_source_preflight import preflight


def _retryable(reason):
    """Only access/inconclusive failures may be retried; hard errors stay hard."""
    message = str(reason).lower()
    hard = ("404", "wrong title", "title mismatch", "wrong date",
            "date mismatch", "invalid", "redirect mismatch",
            "duplicate", "different original", "not independently marked")
    if any(word in message for word in hard):
        return False
    return any(word in message for word in (
        "403", "401", "timeout", "timed out", "network",
        "inconclusive", "no direct or evidence-backed", "temporarily unavailable",
        "feed inaccessible", "connection error"))


def recover(raw, date, *, minimum=15, max_retries=2, checker=None):
    """Recheck only unresolved candidates, then apply the unchanged S4 gate.

    The initial triage counts as attempt 1. Each unresolved item may receive
    at most max_retries additional checks. Never synthesize a candidate,
    mutate the raw pool or return a pool on a failed final preflight.
    """
    if type(max_retries) is not int or not 0 <= max_retries <= 2:
        raise ValueError("max_retries must be an integer between 0 and 2")
    initial = triage(raw, date, minimum=minimum, checker=checker)
    eligible = {item["id"]: item for item in initial["eligible"]}
    by_id = {item["id"]: item for item in raw}
    pending = {item["id"]: item for item in initial["rejected"]}
    retry_counts = {item["id"]: 0 for item in raw}
    for _ in range(max_retries):
        to_retry = [identifier for identifier, row in pending.items()
                    if _retryable(row["reason"])]
        if not to_retry:
            break
        for identifier in to_retry:
            retry_counts[identifier] += 1
            check = triage([by_id[identifier]], date, minimum=1, checker=checker)
            if check["eligible"]:
                eligible[identifier] = check["eligible"][0]
                del pending[identifier]
            else:
                pending[identifier] = check["rejected"][0]
    # Preserve the original research ordering, not an access-based ranking.
    pool = [eligible[item["id"]] for item in raw if item["id"] in eligible]
    gate = preflight(pool, date, minimum=minimum, checker=checker) if pool else {
        "preflight_passed": False, "ready_count": 0,
        "blocked": [], "blocked_count": 0,
        "reason": "No independently verified candidates"}
    passed = gate["preflight_passed"] is True
    return {
        "schema": 1, "date": date, "raw_count": len(raw),
        "eligible_count": len(pool), "needs_research": list(pending.values()),
        "retry_counts": retry_counts, "final_preflight": gate,
        "ready_for_private_capture": passed,
        "eligible": pool if passed else [],
        "rule": "No immutable S4 capture or publication unless final independent preflight passes",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--eligible", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--minimum", type=int, default=15)
    parser.add_argument("--max-retries", type=int, default=2)
    args = parser.parse_args()
    if args.raw in (args.eligible, args.diagnostics) or args.eligible == args.diagnostics:
        parser.error("Raw, eligible and diagnostics paths must differ")
    if args.eligible.exists() or args.diagnostics.exists():
        parser.error("Output paths must be new; never reuse or overwrite a prior recovery attempt")
    result = recover(json.loads(args.raw.read_text(encoding="utf-8")),
                     args.date, minimum=args.minimum, max_retries=args.max_retries)
    report = {key: value for key, value in result.items() if key != "eligible"}
    args.diagnostics.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    if not result["ready_for_private_capture"]:
        raise SystemExit(2)
    args.eligible.write_text(json.dumps(result["eligible"], ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print(json.dumps({"ready": True, "eligible": result["eligible_count"],
                      "needs_research": len(result["needs_research"])}))


if __name__ == "__main__":
    main()
