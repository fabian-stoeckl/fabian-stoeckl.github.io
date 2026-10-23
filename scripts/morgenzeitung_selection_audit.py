"""Auditable counterfactual for Morgenzeitung editorial selection.

Run with an already researched, verified candidate pool and a private profile.
The output is PRIVATE operational evidence; never commit it to public Pages.
"""
import argparse
import json
from pathlib import Path
from scripts.morgenzeitung_editorial import select_articles

def compare(candidate_pool, profile, *, limit=10, max_per_source=4):
    """Compare exactly the same candidates with and without learned signals."""
    if not isinstance(candidate_pool, list):
        raise ValueError("candidate_pool must be a list")
    ids = [item.get("id") for item in candidate_pool]
    if any(not item_id for item_id in ids) or len(set(ids)) != len(ids):
        raise ValueError("Candidate IDs must be present and unique")
    if not all(item.get("verified") is True for item in candidate_pool):
        raise ValueError("Every candidate must be explicitly source-verified")
    baseline, baseline_audit = select_articles(candidate_pool, {}, limit=limit, max_per_source=max_per_source)
    selected, selected_audit = select_articles(candidate_pool, profile, limit=limit, max_per_source=max_per_source)
    baseline_ids = [item["id"] for item in baseline]
    selected_ids = [item["id"] for item in selected]
    baseline_rank = {key: i + 1 for i, key in enumerate(baseline_ids)}
    selected_rank = {key: i + 1 for i, key in enumerate(selected_ids)}
    signal_rows = profile.get("computed_learning_signals", [])
    effective_signals = [s for s in signal_rows
                         if s.get("confidence") == "preliminary"
                         and s.get("direction") in ("positive", "negative")]
    changes = [
        {"article_id": item_id, "baseline_rank": baseline_rank.get(item_id),
         "learned_rank": selected_rank.get(item_id)}
        for item_id in dict.fromkeys(baseline_ids + selected_ids)
        if baseline_rank.get(item_id) != selected_rank.get(item_id)
    ]
    added = [item_id for item_id in selected_ids if item_id not in baseline_rank]
    removed = [item_id for item_id in baseline_ids if item_id not in selected_rank]
    return {
        "candidate_count": len(candidate_pool),
        "baseline_ids": baseline_ids,
        "selected_ids": selected_ids,
        "effective_signals": effective_signals,
        "baseline_audit": baseline_audit,
        "selected_audit": selected_audit,
        "rank_changes": changes,
        "newly_selected_ids": added,
        "displaced_ids": removed,
        "changed_top_n_count": len(added),
        "selection_changed": baseline_ids != selected_ids,
        "counterfactual_effect_verified": bool(effective_signals) and baseline_ids != selected_ids,\n        "publication_verified": False,\n        "editorial_effect_verified": False,
        "note": "Counterfactual ranking effect only. Real published editorial impact requires an independently verified publication and matching final article IDs."
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", required=True, help="Private audit JSON path; do not commit to public repo")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-per-source", type=int, default=4)
    args = parser.parse_args()
    candidates = json.loads(Path(args.candidates).read_text())
    profile = json.loads(Path(args.profile).read_text())
    result = compare(candidates, profile, limit=args.limit, max_per_source=args.max_per_source)
    output = Path(args.output)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"candidate_count": result["candidate_count"],
                      "changed_top_n_count": result["changed_top_n_count"],
                      "counterfactual_effect_verified": result["counterfactual_effect_verified"]}))

if __name__ == "__main__":
    main()
