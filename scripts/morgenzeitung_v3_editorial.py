"""Small editorial policies retained from the original Morgenzeitung.

This module intentionally contains no networking, publisher URL probes or
publication gates. Reader feedback is data, never an instruction to execute.
"""
from collections import Counter

NEGATIVE = "Nicht relevant"
POSITIVE = "Sehr relevant"
NEUTRAL = "Teilweise relevant"
RATINGS = {NEGATIVE, POSITIVE, NEUTRAL}

# Each reason has a distinct meaning. A dislike of presentation or repetition
# must never be generalized to disliking the subject itself.
REASON_PATTERNS = {
    "already_known": ("schon bekannt", "kannte ich schon", "nichts neues", "bereits bekannt"),
    "too_shallow": ("zu oberflächlich", "wenig tiefgang", "mehr analyse", "zu wenig analyse"),
    "too_niche": ("zu speziell", "randbereich", "randthema", "juristische details"),
    "one_sided": ("einseitig", "gegenposition", "andere perspektiv"),
    "topic_dislike": ("thema interessiert mich nicht", "thema nicht interessant",
                      "weniger über", "grundsätzlich uninteressant"),
}


def reason_labels(reason, rating):
    """Label explicit criticism, never guess a topic from free text alone."""
    if rating != NEGATIVE or not isinstance(reason, str):
        return ()
    text = " ".join(reason.casefold().split())
    return tuple(label for label, fragments in REASON_PATTERNS.items()
                 if any(fragment in text for fragment in fragments))


def style_signals(article_feedback):
    """Two matching independent observations before adjusting broad styling."""
    counts = Counter()
    for row in article_feedback.values():
        if not isinstance(row, dict):
            continue
        labels = reason_labels(row.get("reason"), row.get("rating"))
        for label in labels:
            if label != "topic_dislike":
                counts[label] += 1
    return {
        "novelty": min(2, counts["already_known"] // 2),
        # Editorial planning advice only: must NOT be used to favor full-text access.
        "analysis": min(2, counts["too_shallow"] // 2),
        "broader_context": min(2, counts["too_niche"] // 2),
        "perspectives": min(2, counts["one_sided"] // 2),
    }


def editorial_feedback_metrics(profile, min_votes=5):
    """Descriptive real V3 vote trend, NEVER claims a causal learning improvement."""
    snapshots = profile.get("feedback_by_issue") or {}
    latest = {}
    for issue_id, issue in snapshots.items():
        if not isinstance(issue, dict):
            continue
        date, updated = issue.get("date"), issue.get("updated_at", "")
        if not isinstance(date, str):
            continue
        for row in issue.get("ratings", []):
            if not isinstance(row, dict) or row.get("rating") not in RATINGS:
                continue
            key = (date, row.get("id"))
            if not isinstance(key[1], str):
                continue
            if key not in latest or (updated, str(issue_id)) > latest[key][0]:
                latest[key] = ((updated, str(issue_id)), row["rating"])
    by_date = {}
    for (date, _), (_, rating) in latest.items():
        by_date.setdefault(date, Counter())[rating] += 1
    days = []
    for date in sorted(by_date):
        row = by_date[date]
        n = sum(row.values())
        days.append({"date": date, "ratings": n,
                     "very_relevant": row[POSITIVE],
                     "partly_relevant": row[NEUTRAL],
                     "not_relevant": row[NEGATIVE],
                     "very_relevant_share": round(row[POSITIVE] / n, 4)})
    sufficient = [x for x in days if x["ratings"] >= min_votes]
    return {
        "days": days,
        "trend_status": "descriptive_only" if len(sufficient) >= 2 else "insufficient_feedback",
        "latest_two_comparable_dates": [x["date"] for x in sufficient[-2:]],
        "very_relevant_share_change": (
            round(sufficient[-1]["very_relevant_share"] - sufficient[-2]["very_relevant_share"], 4)
            if len(sufficient) >= 2 else None),
        "causal_quality_improvement_proven": False,
    }
