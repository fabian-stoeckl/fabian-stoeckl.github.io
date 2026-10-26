"""Check candidate source concentration before immutable preselection capture.

An overconcentrated pool is a research-quality failure, not an excuse to forge
article provenance or retroactively edit a previously archived pool.
"""
from collections import Counter


def audit_source_diversity(candidates, *, max_share=0.70, min_sources=3):
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Nonempty candidate pool required")
    sources = []
    for candidate in candidates:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("source"), str) or not candidate["source"].strip():
            raise ValueError("Every candidate requires a source")
        sources.append(candidate["source"].strip().casefold())
    counts = Counter(sources)
    top_source, top_count = counts.most_common(1)[0]
    share = top_count / len(sources)
    return {"candidate_count": len(sources), "distinct_sources": len(counts),
            "largest_source": top_source, "largest_source_count": top_count,
            "largest_source_share": round(share, 4),
            "diversity_passed": share <= max_share and len(counts) >= min_sources}


def require_source_diversity(candidates):
    result = audit_source_diversity(candidates)
    if not result["diversity_passed"]:
        raise ValueError("Candidate source concentration too high; research additional independently verified publishers BEFORE immutable capture")
    return result
