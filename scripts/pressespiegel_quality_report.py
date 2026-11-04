"""Advisory, non-blocking editorial diagnostics. Not a ranking or fact checker."""
import json
import re
from collections import Counter
from pathlib import Path
from morgenzeitung_neu import editorial_warnings

ROOT = Path("Privat/Pressespiegel/data")
LIMITED = ("teaser", "headline", "unknown")


def outlet_family(label):
    """Group obvious label variants; syndication is still a distinct source caveat."""
    name = str(label or "").strip()
    lowered = name.casefold()
    if lowered == "orf" or lowered.startswith("orf /") or lowered.startswith("orf science"):
        return "ORF (inkl. gekennzeichneter Agenturmeldungen)"
    if lowered in ("ap", "associated press"):
        return "Associated Press"
    return name or "Unbekannt"


def shared_topic_signal(entries, rubric, date):
    """Conservative metadata-only repetition hint; not a topic classifier."""
    if rubric != "Vertiefungen" or len(entries) < 5:
        return []
    # Topic labels are authored by the editor; title words aren't reliable
    # enough to infer semantic overlap. Stopwords remove generic connectors.
    generic = {"und", "oder", "mit", "von", "des", "der", "die", "das",
               "ein", "eine", "im", "in", "am", "auf", "für", "eu", "us",
               "europäische", "europäischer", "internationale", "internationalen"}
    tokens = Counter()
    for story in entries:
        words = set(re.findall(r"[a-zäöüß]+", str(story.get("topic", "")).casefold()))
        tokens.update(w for w in words if (len(w) >= 4 or w == "ki")
                      and w not in generic)
    common = [(word, count) for word, count in tokens.most_common()
              if count >= 4 and count / len(entries) > 0.60]
    if not common:
        return []
    word, count = common[0]
    return [f"{date}, {rubric}: broad topic label '{word}' occurs in "
            f"{count}/{len(entries)} pieces; inspect thematic clustering "
            "(a metadata hint, not a semantic classification or quota)."]


def section_signals(entries, rubric, date):
    """Flag editorial blind spots; never automatically delete or rank a story."""
    if len(entries) < 5:
        return []
    notes = []
    sources = Counter(outlet_family(a.get("source")) for a in entries)
    leading, amount = sources.most_common(1)[0]
    if amount / len(entries) > 0.60:
        notes.append(f"{date}, {rubric}: {amount}/{len(entries)} from {leading}; "
                     "verify independent alternatives before accepting this concentration.")
    limited = sum(a.get("evidence_level", "unknown") in LIMITED for a in entries)
    if limited / len(entries) > 0.70:
        notes.append(f"{date}, {rubric}: {limited}/{len(entries)} rely on "
                     "headline, teaser or undocumented access; check every summary "
                     "against original evidence without penalizing paywalls.")
    notes.extend(shared_topic_signal(entries, rubric, date))
    return notes


def recent_diagnostics(root, days, window=7):
    """Brief historical view prevents treating each new source cluster in isolation."""
    notes = []
    recent = []
    missing_discoveries = []
    for day in reversed(days[:window]):
        file = root / (day + ".json")
        if not file.is_file():
            continue
        ed = json.loads(file.read_text(encoding="utf-8"))
        if ed.get("preview") is True:
            continue
        features = ed.get("articles", [])
        news = ed.get("headlines", [])
        notes.extend(section_signals(features, "Vertiefungen", day))
        notes.extend(section_signals(news, "Heute wichtig", day))
        if len(news) >= 10 and sum(a.get("region") == "Österreich" for a in news) <= 1:
            notes.append(f"{day}, Heute wichtig: at most one Austria story among "
                         f"{len(news)}; check whether major Austrian events were missed "
                         "(no geographic quota).")
        if len(features) >= 5:
            counts = Counter(outlet_family(a.get("source")) for a in features)
            source, amount = counts.most_common(1)[0]
            recent.append((day, source, amount, len(features)))
        if day >= "2026-11-05" and not ed.get("new_sources") and not ed.get("new_topics"):
            # Track exploration separately from publisher trends: the two
            # independent signals must never suppress each other.
            missing_discoveries.append(day)
    for (d1, s1, n1, t1), (d2, s2, n2, t2) in zip(recent, recent[1:]):
        if t1 and t2 and s1 != s2 and n1 / t1 > 0.60 and n2 / t2 > 0.60:
            notes.append(f"{d1} to {d2}: dominant outlet changed from {s1} "
                         f"({n1}/{t1}) to {s2} ({n2}/{t2}); examine whether "
                         "recent feedback was overinterpreted rather than a proven preference.")
    if len(missing_discoveries) >= 5:
        notes.append("Discovery has been empty in at least five recent editions; "
                     "review whether exploration is actually attempted, without filler.")
    return notes


def review(root=ROOT):
    days = json.loads((root / "index.json").read_text(encoding="utf-8"))["dates"]
    date = days[0]
    ed = json.loads((root / (date + ".json")).read_text(encoding="utf-8"))
    entries = ed["headlines"] + ed["articles"]
    sources = Counter(a.get("source", "") for a in entries)
    levels = Counter(a.get("evidence_level", "unknown") for a in entries)
    notes = editorial_warnings(ed)
    if len(sources) == 1 and len(entries) > 1:
        notes.append("All articles draw from one publication; check diversity.")
    if len(entries) >= 8 and sources.most_common(1)[0][1] > len(entries) * 0.60:
        notes.append("More than 60% of articles use a single source; review balance, not an automatic veto.")
    if sum(levels[k] for k in LIMITED) > len(entries) * 0.75:
        notes.append("More than 75% of summaries rely on limited original access; review evidence depth.")
    notes.extend(recent_diagnostics(root, days))
    report = [f"### Pressespiegel editorial signals — {date}",
              f"- {len(ed['headlines'])} headlines; {len(ed['articles'])} in-depth articles",
              f"- Source distribution: {', '.join(f'{k}: {v}' for k, v in sources.most_common())}",
              f"- Original access: {', '.join(f'{k}: {v}' for k, v in levels.most_common())}",
              "- Editorial evaluation: these are advisory checks, **not** verification "
              "of article accuracy or reader value; no publisher, topic or region quotas."]
    report += [f"- REVIEW: {note}" for note in notes]
    return "\n".join(report) + "\n"


if __name__ == "__main__":
    print(review())
