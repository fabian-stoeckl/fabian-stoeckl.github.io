"""Fail-closed prepublication gate: independently replay selection from immutable private originals.

Run on the publishing branch BEFORE merge. Never accept a selection audit supplied
by the publishing agent as proof without recomputing it from the private snapshots.
"""
import argparse
import json
from pathlib import Path
from scripts.morgenzeitung_capture_preselection import PrivateRepo, verify_existing, snapshot_paths
from scripts.morgenzeitung_selection_audit import compare
from scripts.morgenzeitung_source_evidence import audit_sources
from scripts.morgenzeitung_live_source_check import check_candidates, _same_article_publisher_redirect
from scripts.morgenzeitung_official_mirror import verify_official_mirror, verify_standard_alias
from scripts.morgenzeitung_source_policy import classify_inconclusive, check_inconclusive_budget


def verify_index(index, date):
    dates = index.get("dates") if isinstance(index, dict) else None
    if (not isinstance(dates, list) or not all(isinstance(d, str) for d in dates)
            or len(dates) != len(set(dates)) or dates != sorted(dates, reverse=True)
            or date not in dates):
        raise ValueError("Edition missing from valid descending public index")
    return True


def verify_edition(repo, date, edition, index=None, check_live=False):
    if index is not None:
        verify_index(index, date)
    version = edition.get("snapshot_version")
    names = snapshot_paths(date, version)
    evidence = verify_existing(repo, date, version=version)
    candidates = json.loads(repo.read(names["candidates"])[0])
    profile = json.loads(repo.read(names["profile"])[0])
    params = evidence["parameters"]
    source_evidence = audit_sources(candidates)
    if not source_evidence["source_url_structure_verified"]:
        raise ValueError("Unverified original publisher source URLs in archived candidates")
    comparison = compare(candidates, profile, **params)
    if edition.get("date") != date or edition.get("preview") is True:
        raise ValueError("Incorrect or preview edition")
    articles = edition.get("articles")
    if not isinstance(articles, list) or any(not isinstance(a, dict) for a in articles):
        raise ValueError("Invalid edition articles")
    actual = [a.get("id") for a in articles]
    if actual != comparison["selected_ids"]:
        raise ValueError("Edition does not match independently replayed archived selection")
    selected_ids = set(actual)
    selected_candidates = [item for item in candidates if item["id"] in selected_ids]
    live_sources = None
    if check_live:
        # Use archived originals for the independent replay. A different link
        # in the published article must itself be independently verified.
        # Reuters Breakingviews has an official Breakingviews domain; Reuters.com
        # may return 401 even for a genuine article. Never treat 401 as proof.
        edition_by_id = {article["id"]: article for article in articles}
        checked = []
        def verify_or_record_inconclusive(item):
            try:
                return check_candidates([item], date, publisher_dates=True)["checked"][0]
            except ValueError as exc:
                caution = classify_inconclusive(item, exc)
                if caution is None:
                    raise
                return caution

        for candidate in selected_candidates:
            article = edition_by_id[candidate["id"]]
            original_url = candidate["source_url"]
            published_url = article.get("url") or original_url
            if (published_url != original_url
                    and candidate.get("source") == "Der Standard"
                    and original_url.startswith(("https://www.derstandard.de/story/",
                                                  "https://derstandard.de/story/"))
                    and published_url.startswith(("https://www.derstandard.at/story/",
                                                  "https://derstandard.at/story/"))):
                # The private original remains immutable. A direct Austrian
                # canonical URL is acceptable only if exact story path/ID and
                # HTTPS publisher identity match AND the .at article itself
                # passes the normal independent live checks. Do not trust the
                # .de 302 or follow its destination to a login/cookie wall.
                validated_url = _same_article_publisher_redirect(original_url, published_url)
                canonical = dict(candidate, source_url=validated_url)
                record = verify_or_record_inconclusive(canonical)
                record["archived_source_url"] = original_url
                record["independently_verified_canonical_url"] = validated_url
                checked.append(record)
            elif published_url != original_url:
                # Independent publisher confirmation is mandatory for an alias.
                mirror = (verify_standard_alias(candidate, published_url)
                          if candidate.get('source') == 'Der Standard'
                          else verify_official_mirror(candidate, published_url))
                try:
                    result = check_candidates([candidate], date, publisher_dates=True)
                    record = result["checked"][0]
                except ValueError as exc:
                    if "HTTP 401" not in str(exc) and "HTTP 403" not in str(exc):
                        raise
                    record = {"id": candidate["id"], "original_status": "access_restricted"}
                record["official_publisher_mirror"] = mirror
                checked.append(record)
            else:
                checked.append(verify_or_record_inconclusive(candidate))
        confirmed = lambda record: (
            record.get("original_article_http_verified") is True
            or record.get("http_status") in (200, 206)
            or record.get("official_publisher_mirror", {}).get("official_mirror_verified") is True
            or record.get("publisher_feed_verified") is True)
        warnings = check_inconclusive_budget(checked)
        live_sources = {"live_source_checks_passed": all(confirmed(record) for record in checked),
                        "inconclusive_count": sum(not confirmed(record) for record in checked),
                        "checked": checked,
                        "limitation": "Consent walls and expired rolling feeds do NOT count as publisher verification. A bounded INCONCLUSIVE allows editorial provenance checks to pass with explicit warnings; contradicted source metadata, dead links and excessive uncertainty still block.",
                        "source_verification_status": "PARTIAL" if warnings else "PASS",
                        "warnings": warnings}
    return {
        "date": date,
        "snapshot_version": version,
        "prepublication_gate_verified": True,
        "candidate_sha256": evidence["candidate_sha256"],
        "profile_sha256": evidence["profile_sha256"],
        "parameters": params,
        "source_evidence": source_evidence,
        "live_source_evidence": live_sources,
        "selected_ids": actual,
        "counterfactual_effect_verified": comparison["counterfactual_effect_verified"],
        "limitation": "This gate verifies exact archived-input replay, not the original research or chronology.",
    }


def validate_published_count(edition):
    articles = edition.get('articles') if isinstance(edition, dict) else None
    if not isinstance(articles, list) or not 10 <= len(articles) <= 15:
        raise ValueError('Published edition must contain 10 to 15 articles')
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date", required=True)
    p.add_argument("--edition", type=Path, required=True)
    p.add_argument("--index", type=Path)
    p.add_argument("--check-live-sources", action="store_true",
                   help="Legacy diagnostic only; never required for publication")
    args = p.parse_args()
    import os
    repo = PrivateRepo(os.environ.get("MORGENZEITUNG_FEEDBACK_TOKEN"))
    edition = json.loads(args.edition.read_text())
    validate_published_count(edition)
    result = verify_edition(repo, args.date, edition,
                            json.loads(args.index.read_text()) if args.index else None,
                            check_live=args.check_live_sources)
    if result["live_source_evidence"] and result["live_source_evidence"]["warnings"]:
        import sys
        print("::warning::Source checks PARTIAL: publisher RSS/archive evidence unavailable for "
              + str(len(result["live_source_evidence"]["warnings"])) + " selected article(s). "
              "Editorial input replay PASS, publisher verification NOT PASS.", file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
