"""Non-blocking editorial signals; not a substitute for source verification."""
import json
from collections import Counter
from pathlib import Path
from morgenzeitung_neu import editorial_warnings

ROOT = Path("Privat/Pressespiegel/data")

def review(root=ROOT):
    days=json.loads((root/"index.json").read_text(encoding="utf-8"))["dates"]
    date=days[0]
    ed=json.loads((root/(date+".json")).read_text(encoding="utf-8"))
    entries=ed["headlines"]+ed["articles"]
    sources=Counter(a.get("source","") for a in entries)
    levels=Counter(a.get("evidence_level","unknown") for a in entries)
    notes=editorial_warnings(ed)
    if len(sources)==1 and len(entries)>1:
        notes.append("All articles draw from one publication; check whether diversity is adequate.")
    # Overall source balance can conceal concentration in personally selected
    # deep dives, or conversely in the objective news section.
    for rubric, group in (("Vertiefungen", ed["articles"]),
                          ("Heute wichtig", ed["headlines"])):
        if len(group) >= 5:
            counts = Counter(a.get("source", "") for a in group)
            source, amount = counts.most_common(1)[0]
            if amount / len(group) > 0.6:
                notes.append(f"{rubric}: {amount}/{len(group)} pieces from {source}; "
                             "review editorial variety, no automatic outlet quota.")
    if len(entries)>=8 and sources.most_common(1)[0][1] > len(entries)*0.6:
        notes.append("More than 60% of articles use a single source; review balance, not an automatic veto.")
    if sum(levels[k] for k in ("teaser","headline","unknown")) > len(entries)*0.75:
        notes.append("More than 75% of summaries rely on limited original access; review evidence depth.")
    report=[f"### Pressespiegel editorial signals — {date}",
            f"- {len(ed['headlines'])} headlines; {len(ed['articles'])} in-depth articles",
            f"- Source distribution: {', '.join(f'{k}: {v}' for k,v in sources.most_common())}",
            f"- Original access: {', '.join(f'{k}: {v}' for k,v in levels.most_common())}",
            "- Editorial evaluation: these are advisory metadata checks, **not** verification of truth, completeness or reader value."]
    report += [f"- REVIEW: {note}" for note in notes]
    return "\n".join(report)+"\n"

if __name__ == "__main__":
    print(review())
