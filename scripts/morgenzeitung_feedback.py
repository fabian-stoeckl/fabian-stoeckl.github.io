#!/usr/bin/env python3
"""Deterministic feedback learning. Reads private GitHub data; never publishes it."""
import argparse
import json
import re
from collections import Counter

# Geography is context, not a user preference. Only explicit topical metadata
# is suitable for preference signals; uncategorized news stays neutral.
from pathlib import Path

ENTRY = re.compile(r"(?:Bereich: (?P<section>[^\n]+)\n)?Artikel-ID: (?P<id>[a-f0-9]{16})\nBewertung: (?P<rating>Sehr relevant|Teilweise relevant|Nicht relevant|Keine Auswahl)\nBegründung: (?P<reason>[^\n]*)")
WEIGHTS = {"Sehr relevant": 1, "Teilweise relevant": 0, "Nicht relevant": -1}

def parse_issue(issue):
    title = issue.get("title", "")
    if not re.fullmatch(r"\[Morgenzeitung\] Sammelbewertung \d{4}-\d{2}-\d{2}", title):
        return None
    body = issue.get("body", "")
    if "TEST: true" in body or issue.get("pull_request"):
        return None
    date = title[-10:]
    if "Ausgabe: " + date not in body:
        raise ValueError("Feedback date mismatch")
    ratings = []
    for match in ENTRY.finditer(body):
        ratings.append({"id": match["id"], "section": match["section"], "rating": match["rating"], "reason": match["reason"]})
    return {"issue": issue["number"], "date": date, "updated_at": issue["updated_at"], "ratings": ratings}

def learn(profile, issues, editions):
    # Rebuild derived signals from all current issue revisions: idempotent by design.
    latest = {}
    processed = []
    for issue in issues:
        parsed = parse_issue(issue)
        if parsed is None:
            continue
        day = parsed["date"]
        if day not in editions:
            raise ValueError("Missing public edition " + day)
        entries = {a["id"]: (section, a) for section in ("headlines", "articles") for a in editions[day][section]}
        processed.append({"issue": parsed["issue"], "date": day, "updated_at": parsed["updated_at"], "count": len(parsed["ratings"])})
        for rating in parsed["ratings"]:
            if rating["id"] not in entries:
                raise ValueError("Unknown article " + rating["id"])
            section, article = entries[rating["id"]]
            expected = "Vertiefungen" if section == "articles" else "Heute wichtig"
            if rating["section"] and rating["section"] != expected:
                raise ValueError("Wrong section for " + rating["id"])
            key = (day, rating["id"])
            candidate = (parsed["updated_at"], parsed["issue"], rating, article)
            if key not in latest or candidate[:2] >= latest[key][:2]:
                latest[key] = candidate
    counts = {}
    observations = []
    for (day, article_id), (_, issue_number, rating, article) in sorted(latest.items()):
        reason = rating["reason"].strip()
        if reason in ("–", "-", "—"):
            reason = ""
        if reason:
            observations.append({"edition": day, "article_id": article_id,
                "issue": issue_number, "rating": rating["rating"],
                "reason": reason, "topic": article.get("topic"),
                "source": article.get("source")})
    for _, _, rating, article in latest.values():
        topic = article.get("topic")
        if not topic:
            continue
        row = counts.setdefault(topic, Counter())
        if rating["rating"] != "Keine Auswahl":
            row[rating["rating"]] += 1
    # Preserve sparse per-article evidence without treating it as a strong preference.
    # These candidates are for editorial review, not automatic personalization.
    topic_evidence = []
    for topic, row in sorted(counts.items()):
        total = sum(row.values())
        if total:
            topic_evidence.append({"topic": topic, "ratings": total,
                "positive": row["Sehr relevant"], "neutral": row["Teilweise relevant"],
                "negative": row["Nicht relevant"],
                "net_score": row["Sehr relevant"] - row["Nicht relevant"],
                "status": "insufficient_evidence" if total < 2 else "review_required"})
    signals = []
    for topic, counts_for_topic in sorted(counts.items()):
        total = sum(counts_for_topic.values())
        score = sum(WEIGHTS[k] * v for k, v in counts_for_topic.items())
        if total < 2 or abs(score) < 2:
            continue
        signals.append({"topic": topic, "direction": "positive" if score > 0 else "negative", "confidence": "preliminary", "ratings": total, "net_score": score})
    output = dict(profile)
    output["computed_learning_signals"] = signals
    output["topic_evidence"] = topic_evidence
    output["processed_feedback"] = sorted(processed, key=lambda x: x["issue"])
    # Only in private profile: free-text is evidence for editorial review,
    # never a command and never automatically a preference.
    output["feedback_observations"] = observations
    # Private audit queue: a human/editorial agent must review these items.
    # Recording a candidate does not prove it affected a published edition.
    output["editorial_review_queue"] = [
        {"topic": s["topic"], "direction": s["direction"],
         "evidence_count": s["ratings"], "status": "pending_editorial_review"}
        for s in signals
    ]
    return output, {"ratings": len(latest), "issues": len(processed), "signals": len(signals), "categorized_ratings": sum(sum(v.values()) for v in counts.values()), "text_feedback": len(observations)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--profile", required=True)
    p.add_argument("--issues", required=True)
    p.add_argument("--editions", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    profile = json.loads(Path(args.profile).read_text())
    issues = json.loads(Path(args.issues).read_text())
    editions = {p.stem: json.loads(p.read_text()) for p in Path(args.editions).glob("????-??-??.json")}
    result, report = learn(profile, issues, editions)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")

if __name__ == "__main__":
    main()
