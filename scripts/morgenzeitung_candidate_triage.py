"""Separate research-candidate failures from actual preselection gate failures.

Run BEFORE immutable S4 capture. Preserve every rejected raw item in a PRIVATE
diagnostic alongside an explicitly rechecked, publisher-verified eligible pool.
Never turn INCONCLUSIVE into PASS or permit selection from rejected items.
"""
import argparse
import json
from pathlib import Path

from scripts.morgenzeitung_live_source_check import check_candidates, check_date
from scripts.morgenzeitung_source_diversity import audit_source_diversity
from scripts.morgenzeitung_source_preflight import preflight


def triage(candidates, date, *, minimum=15, checker=None, editorial_mode=False, no_link_tests=False):
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Original unselected research candidates required")
    if type(minimum) is not int or minimum < 1:
        raise ValueError("Positive minimum required")
    if editorial_mode or no_link_tests:
        result = preflight(candidates, date, minimum=minimum, checker=checker,
                           allow_partial=True, editorial_mode=editorial_mode,
                           no_link_tests=no_link_tests)
        return {"schema": 1, "date": date, "raw_count": len(candidates),
                "eligible_count": result["ready_count"],
                "rejected_count": result["blocked_count"],
                "ready_for_final_preflight": result["preflight_passed"],
                "minimum": minimum, "eligible": result["verified_candidates"],
                "rejected": [{"state": "NEEDS_RESEARCH", **row}
                             for row in result["blocked"]],
                "diversity": result["diversity"],
                "important": "Editorial provenance assessed once; capture only eligible candidates. Separate publication and learning checks remain required."}
    checker = checker or check_candidates
    eligible, rejected, seen = [], [], set()
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("Invalid raw candidate structure")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("Each researched candidate needs a unique identity")
        seen.add(identifier)
        try:
            check_date(item.get("published_at"), date)
            result = checker([item], date, publisher_dates=True)
            record = result["checked"][0]
            # Never let an invented/unstamped feed flag stand in for evidence.
            identity = record.get("original_article_http_verified") is True
            feed_evidence = record.get("publisher_feed_evidence")
            feed = (record.get("publisher_feed_verified") is True
                    and isinstance(feed_evidence, dict)
                    and feed_evidence.get("publisher_feed_verified") is True
                    and bool(feed_evidence.get("publication_time"))
                    and (feed_evidence.get("original_url") == item.get("source_url")
                         or feed_evidence.get("article_url") == item.get("source_url")))
            if identity or feed:
                if item.get("verified") is not True:
                    raise ValueError("Candidate not independently marked source-verified")
                eligible.append(dict(item))
            else:
                rejected.append({"id": identifier, "source": item.get("source"),
                                 "state": "NEEDS_RESEARCH",
                                 "reason": "No direct or evidence-backed official-publisher original identity"})
        except (ValueError, OSError, IndexError, KeyError, TypeError) as exc:
            rejected.append({"id": identifier, "source": item.get("source"),
                             "state": "NEEDS_RESEARCH", "reason": str(exc)})
    diverse = audit_source_diversity(eligible) if eligible else None
    ready = bool(len(eligible) >= minimum and diverse is not None and diverse["diversity_passed"])
    return {
        "schema": 1, "date": date, "raw_count": len(candidates),
        "eligible_count": len(eligible), "rejected_count": len(rejected),
        "ready_for_final_preflight": ready, "minimum": minimum,
        "eligible": eligible, "rejected": rejected, "diversity": diverse,
        "important": ("The ELIGIBLE pool MUST separately pass the unchanged "
                      "scripts.morgenzeitung_source_preflight.preflight gate "
                      "before private immutable S4 and selection. Raw rejected "
                      "research evidence must be archived privately, not dropped."),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--eligible", type=Path, required=True)
    p.add_argument("--diagnostics", type=Path, required=True)
    p.add_argument("--minimum", type=int, default=15)
    p.add_argument("--no-link-tests", action="store_true",
                   help="Preserve discovered articles without HTTP, feed, or date gate")
    p.add_argument("--editorial-mode", action="store_true",
                   help="Use documented discovery provenance instead of live HTTP checks")
    args = p.parse_args()
    if args.eligible == args.diagnostics:
        p.error("Eligible and diagnostic files must not be the same")
    result = triage(json.loads(args.candidates.read_text()),
                    args.date, minimum=args.minimum, editorial_mode=args.editorial_mode,
                    no_link_tests=args.no_link_tests)
    args.eligible.write_text(json.dumps(result["eligible"],ensure_ascii=False,indent=2)+"\n")
    report = {key:value for key,value in result.items() if key != "eligible"}
    args.diagnostics.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"eligible":result["eligible_count"],
                      "needs_research":result["rejected_count"],
                      "ready_for_final_preflight":result["ready_for_final_preflight"]}))
    if not result["ready_for_final_preflight"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
