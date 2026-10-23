#!/usr/bin/env python3
"""Deterministic feedback learning. Reads private GitHub data; never publishes it."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

ENTRY = re.compile(r"(?:Bereich: (?P<section>[^\n]+)\n)?Artikel-ID: (?P<id>[a-f0-9]{16})\nBewertung: (?P<rating>Sehr relevant|Teilweise relevant|Nicht relevant)\nBegründung: (?P<reason>[^\n]*)")
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
            if key not in latest or candidate[:2] > latest[key][:2]:
                latest[key] = candidate
    counts = {}
    for _, _, rating, article in latest.values():
        topic = article.get("topic") or ("Nachrichten: " + article.get("region", "Allgemein"))
        row = counts.setdefault(topic, Counter())
        if rating["rating"] != "Keine Auswahl":\n            row[rating["rating"]] += 1
    signals = []
    for topic, counts_for_topic in sorted(counts.items()):
        total = sum(counts_for_topic.values())
        score = sum(WEIGHTS[k] * v for k, v in counts_for_topic.items())
        if total < 2 or abs(score) < 2:
            continue
        signals.append({"topic": topic, "direction": "positive" if score > 0 else "negative", "confidence": "preliminary", "ratings": total, "net_score": score})
    output = dict(profile)
    output["computed_learning_signals"] = signals
    output["processed_feedback"] = sorted(processed, key=lambda x: x["issue"])
    return output, {"ratings": len(latest), "issues": len(processed), "signals": len(signals)}

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
