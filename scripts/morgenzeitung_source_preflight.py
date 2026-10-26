"""Pre-archive source preflight: reject access failures before immutable selection.

This is a research aid, NEVER evidence for a published gate PASS.
Run on the full unarchived pool; replace inaccessible candidates with genuinely
researched independent articles, then repeat until the pool is ready.
"""
import argparse
import json
from scripts.morgenzeitung_live_source_check import check_candidates, check_date
from scripts.morgenzeitung_source_diversity import audit_source_diversity


def preflight(candidates, date, *, minimum=15, checker=None):
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Nonempty original candidate pool required")
    checker = checker or check_candidates
    ready, blocked = [], []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Invalid candidate")
        try:
            check_date(candidate.get("published_at"), date)
            result = checker([candidate], date, publisher_dates=True)
            record = result["checked"][0]
            if (record.get("original_article_http_verified") is True
                    or record.get("publisher_feed_verified") is True):
                ready.append(candidate)
            else:
                blocked.append({"id": candidate.get("id"), "source": candidate.get("source"),
                                "reason": "INCONCLUSIVE: no independent article confirmation"})
        except (ValueError, OSError) as exc:
            blocked.append({"id": candidate.get("id"), "source": candidate.get("source"),
                            "reason": str(exc)})
    diversity = audit_source_diversity(ready) if ready else None
    passed = len(ready) >= minimum and diversity is not None and diversity["diversity_passed"]
    return {"preflight_passed": bool(passed), "ready_count": len(ready),
            "minimum": minimum, "blocked_count": len(blocked), "blocked": blocked,
            "diversity": diversity,
            "next_action": ("Capture the full verified candidate pool BEFORE selection"
                            if passed else
                            "Research new independent articles and rerun preflight BEFORE immutable capture"),
            "limitation": "This preflight does not replace independent prepublication verification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--minimum", type=int, default=15)
    args = parser.parse_args()
    with open(args.candidates, encoding="utf-8") as stream:
        pool = json.load(stream)
    result = preflight(pool, args.date, minimum=args.minimum)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["preflight_passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
