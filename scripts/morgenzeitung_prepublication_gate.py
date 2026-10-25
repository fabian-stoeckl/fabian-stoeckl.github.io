"""Fail-closed prepublication gate: independently replay selection from immutable private originals.

Run on the publishing branch BEFORE merge. Never accept a selection audit supplied
by the publishing agent as proof without recomputing it from the private snapshots.
"""
import argparse
import json
from pathlib import Path
from scripts.morgenzeitung_capture_preselection import PrivateRepo, verify_existing
from scripts.morgenzeitung_selection_audit import compare
from scripts.morgenzeitung_source_evidence import audit_sources
from scripts.morgenzeitung_live_source_check import check_candidates, _same_article_publisher_redirect
from scripts.morgenzeitung_official_mirror import verify_official_mirror, verify_standard_alias


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
    evidence = verify_existing(repo, date)
    candidates = json.loads(repo.read("candidates/" + date + ".json")[0])
    profile = json.loads(repo.read("snapshots/" + date + "-profile.json")[0])
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
                record = check_candidates([canonical], date, publisher_dates=True)["checked"][0]
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
                checked.extend(check_candidates([candidate], date, publisher_dates=True)["checked"])
        live_sources = {"live_source_checks_passed": True, "checked": checked,
                        "limitation": "Official publisher mirrors require independent title/date checks and never assert restricted Reuters.com body access."}
    return {
        "date": date,
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
    p.add_argument("--check-live-sources", action="store_true")
    args = p.parse_args()
    import os
    repo = PrivateRepo(os.environ.get("MORGENZEITUNG_FEEDBACK_TOKEN"))
    edition = json.loads(args.edition.read_text())
    validate_published_count(edition)
    result = verify_edition(repo, args.date, edition,
                            json.loads(args.index.read_text()) if args.index else None,
                            check_live=args.check_live_sources)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
