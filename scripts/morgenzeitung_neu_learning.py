"""Compact, inspectable editorial ordering; no article link requests.

Candidate fields: fit and novelty in 0..5, topic and source text; optional
verified_facts is a drafting aid and NOT an accessibility score.
"""
from collections import Counter

def select(candidates, profile, limit=15):
    if not 1 <= limit <= 15:
        raise ValueError("limit must be 1..15")
    priorities = profile.get("topics", {})
    deltas = profile.get("feedback_topic_deltas", {})
    ranked = []
    for index, item in enumerate(candidates):
        if not all(item.get(k) for k in ("title", "source", "url", "topic")):
            continue
        if not item["url"].startswith("https://"):
            continue
        fit, novelty = item.get("fit", 0), item.get("novelty_score", 0)
        if not all(isinstance(n, (int, float)) and not isinstance(n, bool) and 0 <= n <= 5 for n in (fit, novelty)):
            raise ValueError("fit and novelty_score must be 0..5")
        priority = priorities.get(item["topic"], 3)
        if not isinstance(priority, (int, float)) or not 0 <= priority <= 5:
            priority = 3
        change = max(-2, min(2, deltas.get(item["topic"], 0)))
        score = 4 * fit + 3 * novelty + 2 * (priority + change)
        ranked.append((score, index, item))
    ranked.sort(key=lambda r: (-r[0], r[1]))
    chosen, audit, seen_events, sources = [], [], set(), Counter()
    for score, index, item in ranked:
        event = item.get("event") or item.get("url")
        if event in seen_events:
            continue
        # Variety is a TIE-BREAKER only: never discard the best-scoring work
        # because too many articles come from the same publisher.
        chosen.append(item)
        audit.append({"id": item.get("id"), "score": score, "candidate_order": index})
        sources[item["source"]] += 1
        seen_events.add(event)
        if len(chosen) >= limit:
            break
    return chosen, audit
