"""Deterministic editorial selection for pre-researched candidates.

Call after source verification, before publishing. Feedback never overrides
factual relevance, verification, diversity or freshness gates.
"""
from collections import Counter
from scripts.morgenzeitung_feedback import topic_family
from scripts.morgenzeitung_feedback import topic_family

def select_articles(candidates, profile, limit=10, max_per_source=4):
    if not isinstance(candidates, list) or limit < 1:
        raise ValueError("Invalid candidates or limit")
    signals = {s["topic"]: s["direction"] for s in profile.get("computed_learning_signals", [])
               if s.get("confidence") == "preliminary" and s.get("direction") in ("positive", "negative")}
    ranked = []
    for index, article in enumerate(candidates):
        if not article.get("id") or not article.get("topic") or not article.get("source"):
            continue
        if article.get("verified") is False:
            continue
        direction = signals.get(article["topic"], signals.get(topic_family(article["topic"])))
        score = 2 if direction == "positive" else -2 if direction == "negative" else 0
        ranked.append((score, index, article, direction))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    chosen, source_counts, audit = [], Counter(), []
    for score, index, article, direction in ranked:
        if len(chosen) >= limit:
            break
        source = article["source"]
        if source_counts[source] >= max_per_source:
            continue
        source_counts[source] += 1
        chosen.append(article)
        audit.append({"article_id": article["id"], "topic": article["topic"],
                      "learning_direction": direction or "neutral", "learning_score": score,
                      "candidate_index": index})
    return chosen, audit
