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
