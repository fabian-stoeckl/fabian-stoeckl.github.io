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


def verify_index(index, date):
    dates = index.get("dates") if isinstance(index, dict) else None
    if (not isinstance(dates, list) or not all(isinstance(d, str) for d in dates)
            or len(dates) != len(set(dates)) or dates != sorted(dates, reverse=True)
            or date not in dates):
        raise ValueError("Edition missing from valid descending public index")
    return True


def verify_edition(repo, date, edition, index=None):
    if index is not None:
        verify_index(index, date)
    evidence = verify_existing(repo, date)
    candidates = json.loads(repo.read("candidates/" + date + ".json")[0])
    profile = json.loads(repo.read("snapshots/" + date + "-profile.json")[0])
    params = evidence["parameters"]
    source_evidence = audit_sources(candidates)
    comparison = compare(candidates, profile, **params)
    if edition.get("date") != date or edition.get("preview") is True:
        raise ValueError("Incorrect or preview edition")
    articles = edition.get("articles")
    if not isinstance(articles, list) or any(not isinstance(a, dict) for a in articles):
        raise ValueError("Invalid edition articles")
    actual = [a.get("id") for a in articles]
    if actual != comparison["selected_ids"]:
        raise ValueError("Edition does not match independently replayed archived selection")
    return {
        "date": date,
        "prepublication_gate_verified": True,
        "candidate_sha256": evidence["candidate_sha256"],
        "profile_sha256": evidence["profile_sha256"],
        "parameters": params,
        "source_evidence": source_evidence,
        "selected_ids": actual,
        "counterfactual_effect_verified": comparison["counterfactual_effect_verified"],
        "limitation": "This gate verifies exact archived-input replay, not the original research or chronology.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date", required=True)
    p.add_argument("--edition", type=Path, required=True)
    p.add_argument("--index", type=Path)
    args = p.parse_args()
    import os
    repo = PrivateRepo(os.environ.get("MORGENZEITUNG_FEEDBACK_TOKEN"))
    result = verify_edition(repo, args.date, json.loads(args.edition.read_text()),
                            json.loads(args.index.read_text()) if args.index else None)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
