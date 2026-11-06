"""Read-only advisory: recurring independently authored feedback, not suggestion clicks.

Usage (only with a PRIVATE, temporary canonical GitHub Issues export):
  python3 scripts/feedback_suggestions_review.py --issues /tmp/private-issues.json \
      --current /tmp/begruendungsvorschlaege.json

Never commit private feedback exports to the public repo; never auto-publish
candidate phrases. The editorial agent must review context, source and consent.
"""
import argparse
import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

MARKER = "MORGENZEITUNG_NEU_FEEDBACK_V1\n"
TITLE = re.compile(r"^\[(?:Pressespiegel|Morgenzeitung Neu)\] Feedback (\d{4}-\d{2}-\d{2})$")
FIXED_GENERAL = [
    "Das Thema interessiert mich, aber ich kannte die Inhalte schon.",
    "Mehr analytische Tiefe: Bitte Mechanismen und Folgen erklären.",
    "Zu einseitig: Ich hätte gern auch fundierte Gegenpositionen.",
    "Mehr neue Erkenntnisse statt kurzer Ankündigungen.",
    "Mehr konkrete Daten und Auswirkungen für Österreich.",
    "Mehr davon: Diese Analyse hat mir eine neue Sichtweise eröffnet.",
]
FIXED_ARTICLE = [
    "Thema unpassend", "Zu oberflächlich", "Schon bekannt",
    "Zu speziell", "Einseitige Perspektive", "Mehr davon"
]


def normalized(value):
    if not isinstance(value, str):
        return ""
    text = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text)).strip()


def prompted(line, clicked, templates):
    token = normalized(line)
    if not token:
        return True
    for known in (*clicked, *templates):
        reference = normalized(known)
        if reference and (token == reference or SequenceMatcher(
                None, token, reference).ratio() >= .88):
            return True
    return False


def parse_issue(item):
    """Only current, genuine canonical feedback issues; PRs/tests rejected."""
    if not isinstance(item, dict) or item.get("pull_request"):
        return None
    matched = TITLE.fullmatch(str(item.get("title", "")))
    body = item.get("body")
    if not matched or not isinstance(body, str) or not body.startswith(MARKER):
        return None
    try:
        payload = json.loads(body[len(MARKER):])
    except (ValueError, TypeError):
        return None
    if (not isinstance(payload, dict) or payload.get("origin") != "website-explicit"
            or payload.get("test") is True or payload.get("date") != matched[1]
            or not isinstance(payload.get("ratings"), list)
            or not isinstance(payload.get("comment", ""), str)):
        return None
    return payload


def candidates(issues, current=None):
    """Observations only: corroboration requires separate canonical ISSUE dates."""
    current = current if isinstance(current, dict) else {}
    template_general = [*FIXED_GENERAL, *current.get("general_suggestions", [])]
    template_article = [*FIXED_ARTICLE, *current.get("suggestions", [])]
    latest = {}
    for item in issues:
        payload = parse_issue(item)
        if not payload:
            continue
        day = payload["date"]
        if day not in latest or str(item.get("updated_at", "")) > str(
                latest[day][0].get("updated_at", "")):
            latest[day] = (item, payload)

    observed = {"general": defaultdict(set), "article": defaultdict(set)}
    spelling = {"general": {}, "article": {}}
    excluded = {"prompted": 0, "invalid": 0}
    for day, (_, feedback) in latest.items():
        clicked_general = feedback.get("comment_suggestions", [])
        if not isinstance(clicked_general, list):
            clicked_general = []
        def record(group, line, clicked, templates, limit):
            text = line.strip()
            if (len(text) < 12 or len(text) > limit
                    or "\r" in text or "\t" in text or "http://" in text
                    or "https://" in text or text.startswith("[V3-Vergleich")):
                excluded["invalid"] += 1
                return
            if prompted(text, clicked, templates):
                excluded["prompted"] += 1
                return
            key = normalized(text)
            if not key:
                return
            observed[group][key].add(day)
            spelling[group].setdefault(key, text)

        for line in feedback.get("comment", "").splitlines():
            if line.strip():
                record("general", line, clicked_general, template_general, 160)
        for rating in feedback["ratings"]:
            if not isinstance(rating, dict) or not isinstance(rating.get("reason", ""), str):
                continue
            clicked_article = rating.get("suggested_reasons", [])
            if not isinstance(clicked_article, list):
                clicked_article = []
            for line in rating.get("reason", "").splitlines():
                if line.strip():
                    record("article", line, clicked_article, template_article, 120)
    def group_summary(group):
        return [
            {"text": spelling[group][key], "distinct_feedback_dates": len(days),
             "dates": sorted(days)}
            for key, days in sorted(observed[group].items(),
                key=lambda item: (-len(item[1]), item[0]))
            if len(days) >= 2
        ]
    return {
        "review_only": True, "private_export_must_not_be_published": True,
        "minimum_distinct_feedback_dates": 2,
        "canonical_feedback_dates": len(latest),
        "excluded": excluded,
        "general_candidates": group_summary("general"),
        "article_candidates": group_summary("article"),
        "note": "Exact or near-exact repeats are only editorial candidates. "
                "Check original context and contradictory free feedback; "
                "never promote clicks or automatically write private suggestions."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issues", required=True, type=Path,
                        help="PRIVATE JSON export with array of current GitHub issues")
    parser.add_argument("--current", type=Path,
                        help="PRIVATE current suggestions JSON; optional")
    args = parser.parse_args()
    source = json.loads(args.issues.read_text(encoding="utf-8"))
    if isinstance(source, dict):
        source = source.get("issues")
    if not isinstance(source, list):
        parser.error("Issues export must be a JSON array or {issues:[...]}")
    current = json.loads(args.current.read_text(encoding="utf-8")) if args.current else {}
    print(json.dumps(candidates(source, current), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
