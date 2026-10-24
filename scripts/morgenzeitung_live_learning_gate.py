"""Fail-closed private Morgenzeitung learning audit, run after HTTPS publication.

Inputs MUST be captured before selection; never reconstruct candidates from
the published edition. Output must remain in the private feedback repository.
"""
import argparse
import hashlib
import json
from pathlib import Path
from scripts.morgenzeitung_selection_audit import compare
from scripts.morgenzeitung_publication_audit import live_json, verify


def audit(date, candidates_bytes, profile_bytes, issues, limit=10, max_per_source=4):
    candidates = json.loads(candidates_bytes)
    profile = json.loads(profile_bytes)
    if limit < 1 or max_per_source < 1:\n        raise ValueError("Selection parameters must be positive")\n    if not isinstance(issues, list) or not all(
        isinstance(i, dict) and isinstance(i.get("number"), int)
        and isinstance(i.get("updated_at"), str) and i["updated_at"] for i in issues
    ):
        raise ValueError("Issue versions must contain number and updated_at")
    if len({i["number"] for i in issues}) != len(issues):
        raise ValueError("Duplicate issue versions")
    comparison = compare(candidates, profile, limit=limit, max_per_source=max_per_source)
    publication = verify(live_json("index.json"), live_json(date + ".json"), comparison, date)
    return {
        "date": date,
        "candidate_pool_sha256": hashlib.sha256(candidates_bytes).hexdigest(),
        "profile_sha256": hashlib.sha256(profile_bytes).hexdigest(),
        "issue_versions": issues,
        "selection_parameters": {"limit": limit, "max_per_source": max_per_source},
        "selection_comparison": comparison,
        "publication_audit": publication,
        "statuses": {
            "feedback": "PARTIAL",
            "profile_learning": "PARTIAL",
            "counterfactual_effect": "PASS" if comparison["counterfactual_effect_verified"] else "PARTIAL",
            "live_publication": "PASS" if publication["publication_verified"] else "FAIL",
            "productive_learning": "PARTIAL",
        },
        "note": "Feedback provenance, CI and private persistence must be verified separately before productive learning can be PASS.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date", required=True)
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--profile", type=Path, required=True)
    p.add_argument("--issue-versions", type=Path, required=True)
    p.add_argument("--private-output", type=Path, required=True)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--max-per-source", type=int, default=4)
    args = p.parse_args()
    if args.private_output.exists():
        p.error("Refusing to overwrite an existing private audit")
    result = audit(args.date, args.candidates.read_bytes(), args.profile.read_bytes(),
                   json.loads(args.issue_versions.read_text()), args.limit, args.max_per_source)
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["statuses"]))


if __name__ == "__main__":
    main()
