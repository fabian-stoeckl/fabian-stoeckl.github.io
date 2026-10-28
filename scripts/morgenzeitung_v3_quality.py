"""Small, non-blocking V3 editorial quality comparisons.

Never fetch publisher URLs. Access to full text, paywalls and article length
must NOT influence article scores. This module reports editorial evidence,
not proof of causality or an artificial minimum content-length gate.
"""
from collections import Counter
from statistics import median

RATINGS = ("Sehr relevant", "Teilweise relevant", "Nicht relevant")
GENRES = ("analysis", "investigation", "report", "explainer", "opinion", "interview", "feature")


def _rows(edition, section):
    rows = edition.get(section, [])
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def editorial_snapshot(edition):
    """Quantitative coverage diagnostics; no semantic quality inferred from length."""
    articles = _rows(edition, "articles")
    headlines = _rows(edition, "headlines")
    sizes = [len(str(r.get("summary") or "").split()) for r in articles]
    genres = Counter(str(r.get("article_type") or r.get("kind") or "").strip()
                     for r in articles)
    evidence = Counter(str(r.get("evidence_level") or r.get("level")
                           or r.get("access") or "unknown").lower()
                       for r in articles)
    return {
        "date": edition.get("date"),
        "articles": len(articles), "headlines": len(headlines),
        "summary_median_words": round(median(sizes), 1) if sizes else None,
        "article_genre_identified": sum(bool(r.get("article_type") or r.get("kind"))
                                        for r in articles),
        "article_genres": dict(genres),
        "articles_with_documented_facts": sum(bool(r.get("facts")) for r in articles),
        "articles_with_event_identity": sum(bool(r.get("event")) for r in articles),
        "articles_with_selection_reason": sum(bool(r.get("why_selected")) for r in articles),
        "source_evidence_levels": dict(evidence),
        "source_evidence_unknown": evidence["unknown"],
        "headlines_from_austria": sum(r.get("region") == "Österreich" for r in headlines),
        "headline_region_unknown": sum(r.get("region") not in ("Österreich", "International")
                                       for r in headlines),
    }


def v1_comparison(v3_edition, reference=None):
    """Descriptive benchmark with real V1 edition, not a quality verdict."""
    current = editorial_snapshot(v3_edition)
    earlier = editorial_snapshot(reference) if isinstance(reference, dict) else None
    issues = []
    if current["article_genre_identified"] < current["articles"]:
        issues.append("Label the verified article type for each selected analysis where possible.")
    if current["articles_with_documented_facts"] < current["articles"]:
        issues.append("Capture evidenced factual takeaways and changes, not just article links.")
    if current["source_evidence_unknown"]:
        issues.append("Record the true source-evidence depth; unknown stays unknown, not low relevance.")
    if current["headlines"] >= 10 and current["headlines_from_austria"] <= 1:
        issues.append("Search independent Austrian politics, macroeconomy and industry reporting more deliberately; no quotas.")
    if current["articles_with_selection_reason"] < min(3, current["articles"]):
        issues.append("Write short source-grounded 'why selected' notes for the top three deeper reports.")
    return {
        "v3": current, "v1_reference": earlier, "editorial_review": issues,
        "summary_length_is_not_quality": True,
        "release_blocked": False,
        "note": ("The comparison uses only real supplied edition files. Word counts, "
                 "coverage fields and genres are diagnostic, not quality scores; "
                 "different dates and story pools are not directly equivalent."),
    }


def calibration_review_from_feedback(candidates, frozen_profile, observed_profile,
                                     score_fn, section="Vertiefungen"):
    """Compare frozen PRE-feedback model expectations with later explicit ratings.

    No weight fitting on the evaluated votes: review surprising examples and
    request later out-of-sample evidence instead. Avoid self-selection bias.
    """
    if frozen_profile is None:
        return {"status": "missing_frozen_profile", "release_blocked": False,
                "note": "Never treat post-feedback ranking as a fair prediction."}
    votes = observed_profile.get("article_feedback", {}) if isinstance(observed_profile, dict) else {}
    original = []
    for item in candidates:
        if not isinstance(item, dict) or item.get("id") not in votes:
            continue
        vote = votes[item["id"]]
        if vote.get("rating") not in RATINGS or vote.get("section", "Vertiefungen") != section:
            continue
        original.append({"item": item, "score": score_fn(item, frozen_profile, section=section),
                         "rating": vote["rating"], "reason": vote.get("reason", "")})
    if not original:
        return {"status": "no_matching_ratings", "observed_ratings": 0,
                "release_blocked": False}
    order = sorted(original, key=lambda r: -r["score"])
    count = len(order)
    mismatches = []
    for rank, x in enumerate(order, start=1):
        if x["rating"] == "Nicht relevant" and rank <= max(1, count // 2):
            mismatches.append({
                "id": x["item"]["id"], "topic": x["item"].get("topic"),
                "rank_among_rated": rank, "rating": x["rating"],
                "explicit_reason": x["reason"][:250],
                "review": "Check editorial assumptions about fit, novelty and analytical depth.",
            })
    distribution = Counter(x["rating"] for x in original)
    return {
        "status": "descriptive_review_only" if count >= 5 else "too_few_ratings",
        "observed_ratings": count, "ratings": dict(distribution),
        "highest_pre_feedback_scored_negative_examples": mismatches[:5],
        "automatic_weight_changes": False, "out_of_sample_quality_proven": False,
        "release_blocked": False,
        "note": ("Uses a frozen pre-feedback profile and actually rated same-pool candidates. "
                 "Only a hypothesis for editorial calibration; no in-sample automatic tuning, "
                 "no inference from silence, paywall, publisher brand or full-text access."),
    }


def reader_comparison_candidates(candidates, selected, score_fn, profile, section="Vertiefungen"):
    """Private optional suggestions. Only editor-approved items can become public."""
    chosen = {r.get("id") for r in selected}
    selected_urls = {r.get("url") for r in selected}
    options = []
    for row in candidates:
        if not isinstance(row, dict) or row.get("id") in chosen or row.get("url") in selected_urls:
            continue
        try:
            value = score_fn(row, profile, section=section)
        except (TypeError, ValueError, KeyError):
            continue
        options.append((value, row))
    options.sort(key=lambda pair: -pair[0])
    return {
        "private_editorial_suggestions": [
            {"id": row["id"], "title": row.get("title"), "source": row.get("source"),
             "url": row.get("url"), "review_required": True}
            for _, row in options[:2]
        ],
        "automatic_publication": False,
        "note": ("Publish at most 1–2 approved genuine alternatives explicitly within "
                 "edition.editorial_comparisons; user rating is optional, never inferred "
                 "from a click, and cannot affect the initial pre-feedback choice."),
    }
