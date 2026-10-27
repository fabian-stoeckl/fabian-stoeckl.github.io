"""Pre-archive source preflight: reject access failures before immutable selection.

This is a research aid, NEVER evidence for a published gate PASS.
Run on the full unarchived pool; replace inaccessible candidates with genuinely
researched independent articles, then repeat until the pool is ready.
"""
import argparse
import json
from scripts.morgenzeitung_live_source_check import check_candidates, check_date
from scripts.morgenzeitung_source_diversity import audit_source_diversity
from scripts.morgenzeitung_source_evidence import validate_source_url


def preflight(candidates, date, *, minimum=15, checker=None, allow_partial=False, editorial_mode=False):
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Nonempty original candidate pool required")
    checker = checker or check_candidates
    ready, blocked = [], []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Invalid candidate")
        try:
            check_date(candidate.get("published_at"), date)
            # Editorial mode avoids fragile network availability as an article gate.
            # Require a concrete, non-placeholder editorial discovery trail.
            if editorial_mode:
                validate_source_url(candidate.get("source_url"))
                discovery = candidate.get("discovery_evidence")
                if (candidate.get("verified") is True
                        and isinstance(candidate.get("title"), str)
                        and len(candidate["title"].strip()) >= 8
                        and isinstance(candidate.get("source"), str)
                        and candidate["source"].strip()
                        and isinstance(discovery, dict)
                        and discovery.get("method") in (
                            "publisher_page", "publisher_feed", "search_result",
                            "news_index", "publisher_metadata")
                        and isinstance(discovery.get("reference"), str)
                        and discovery["reference"].strip()):
                    ready.append(candidate)
                else:
                    blocked.append({"id": candidate.get("id"), "source": candidate.get("source"),
                                    "reason": "Missing concrete editorial discovery evidence"})
                continue
            result = checker([candidate], date, publisher_dates=True)
            record = result["checked"][0]
            feed_evidence = record.get("publisher_feed_evidence")
            feed_verified = (record.get("publisher_feed_verified") is True
                             and isinstance(feed_evidence, dict)
                             and feed_evidence.get("publisher_feed_verified") is True
                             and bool(feed_evidence.get("publication_time"))
                             and (feed_evidence.get("original_url") == candidate.get("source_url")
                                  or feed_evidence.get("article_url") == candidate.get("source_url")))
            if candidate.get("verified") is True and (
                    record.get("original_article_http_verified") is True or feed_verified):
                ready.append(candidate)
            else:
                blocked.append({"id": candidate.get("id"), "source": candidate.get("source"),
                                "reason": "INCONCLUSIVE: no independent article confirmation"})
        except (ValueError, OSError, IndexError, KeyError, TypeError) as exc:
            blocked.append({"id": candidate.get("id"), "source": candidate.get("source"),
                            "reason": str(exc)})
    diversity = audit_source_diversity(ready) if ready else None
    # Partial mode is safe only when the caller captures the verified subset,
    # NEVER the original mixed pool. Legacy strict behavior remains default.
    passed = (len(ready) >= minimum and (allow_partial or not blocked)
              and diversity is not None and diversity["diversity_passed"])
    return {"preflight_passed": bool(passed), "verified_candidates": ready,
            "capture_scope": "VERIFIED_SUBSET_ONLY" if allow_partial else "FULL_INPUT_ONLY",
            "ready_count": len(ready),
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
    parser.add_argument("--eligible-output", help="Write ONLY independently verified candidates; required for partial mode")
    parser.add_argument("--editorial-mode", action="store_true",
                        help="Use URL/date/title and concrete discovery provenance; no live HTTP existence check")
    parser.add_argument("--allow-partial", action="store_true", help="Pass with rejected raw candidates only when eligible-output is provided")
    args = parser.parse_args()
    if (args.allow_partial or args.editorial_mode) and not args.eligible_output:
        parser.error("--allow-partial/--editorial-mode requires --eligible-output to prevent mixed-pool capture")
    with open(args.candidates, encoding="utf-8") as stream:
        pool = json.load(stream)
    result = preflight(pool, args.date, minimum=args.minimum,
                       allow_partial=args.allow_partial, editorial_mode=args.editorial_mode)
    if args.eligible_output and result["preflight_passed"]:
        from pathlib import Path
        Path(args.eligible_output).write_text(
            json.dumps(result["verified_candidates"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "verified_candidates"},
                     ensure_ascii=False, indent=2))
    if not result["preflight_passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
