"""Structural checks only for Pressespiegel: journalistic truth requires human/AI source review."""
import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

ROOT=Path("Privat/Pressespiegel/data")
ID=re.compile(r"^[a-f0-9]{16}$")
EVENT_KEY=re.compile(r"^[a-z0-9][a-z0-9-]{2,99}$")

def canonical(url):
    p=urlsplit(url)
    if p.scheme!="https" or not p.netloc or p.username or p.password or not p.hostname:
        raise ValueError("Original HTTPS URL required")
    query=urlencode(sorted((k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith("utm_") and k.lower() not in ("fbclid","gclid")))
    return urlunsplit(("https",p.netloc.lower(),p.path.rstrip("/"),query,""))

def validate(ed):
    date.fromisoformat(ed["date"])
    stamp=datetime.fromisoformat(ed["researched_at"].replace("Z","+00:00"))
    if stamp.tzinfo is None: raise ValueError("Researched timestamp needs timezone")
    if type(ed.get("preview")) is not bool: raise ValueError("preview must be explicit")
    if not isinstance(ed.get("articles"),list) or not isinstance(ed.get("headlines"),list):
        raise ValueError("Both sections required")
    if len(ed["articles"])>15 or len(ed["headlines"])>20:
        raise ValueError("Too many articles")
    if not ed["articles"] and not ed["headlines"]: raise ValueError("Empty edition")
    ids,urls=set(),set()
    for section in ("articles","headlines"):
        for a in ed[section]:
            if not ID.fullmatch(a.get("id","")): raise ValueError("Invalid ID")
            for key in ("title","source","summary","url","published_at"):
                if not isinstance(a.get(key),str) or not a[key].strip():
                    raise ValueError(f"Missing {key}")
            date.fromisoformat(a["published_at"][:10])
            if section=="articles" and not a.get("topic"): raise ValueError("Missing topic")
            if section=="headlines" and a.get("region") not in ("Österreich","International"):
                raise ValueError("Missing region")
            event=a.get("event_key")
            if event is not None and (not isinstance(event,str) or not EVENT_KEY.fullmatch(event)):
                raise ValueError("Invalid editorial event key")
            distinct=a.get("distinct_contribution")
            if distinct is not None and (not isinstance(distinct,str) or not distinct.strip() or len(distinct)>400):
                raise ValueError("Invalid editorial distinct contribution")
            related=a.get("related_article")
            if related is not None:
                if not isinstance(related,dict) or any(
                    not isinstance(related.get(k),str) or not related[k].strip()
                    for k in ("title","source","url")
                ):
                    raise ValueError("Incomplete related original article")
                related_url=canonical(related["url"])
                if related_url==canonical(a["url"]):
                    raise ValueError("Related article must be a different original URL")
            correction=a.get("correction")
            if correction is not None:
                if ed["preview"] or not isinstance(correction,dict):
                    raise ValueError("Structured article corrections require a real edition")
                required=("corrected_at","previous_summary","note","source_url")
                if any(not isinstance(correction.get(k),str) or not correction[k].strip() for k in required):
                    raise ValueError("Incomplete article correction")
                timestamp=datetime.fromisoformat(correction["corrected_at"].replace("Z","+00:00"))
                if timestamp.tzinfo is None: raise ValueError("Correction needs a timezone")
                if len(correction["note"])>900 or len(correction["previous_summary"])>3000:
                    raise ValueError("Correction explanation is too long")
                if correction["previous_summary"]==a["summary"]:
                    raise ValueError("Correction must change the described content")
                canonical(correction["source_url"])
            level=a.get("evidence_level")
            if not ed["preview"] and level not in ("headline","teaser","read","unknown"):
                raise ValueError("Missing source evidence level")
            if level is not None and level not in ("headline","teaser","read","unknown"):
                raise ValueError("Invalid source evidence level")
            url=canonical(a["url"])
            if a["id"] in ids or url in urls: raise ValueError("Duplicate ID/URL")
            ids.add(a["id"]);urls.add(url)


# Conservative, non-destructive editorial candidate detection. A shared subject
# is not evidence that two original reports describe the same specific event.
NEWS_STOPWORDS=frozenset("""
the a an and or but of in on for to with by from after as at is are was were be
has have had will says said over under amid around about how why what which this
that its it into more less than new now yet first second one two today yesterday
der die das den dem des ein eine einer einem eines und oder aber von vom im in
auf am an um zu zur zum fur für mit nach bei aus als ist sind hat haben wird
war werden gegen durch wegen über ueber unter seit auch noch nun neue neuer
neuen neue entwicklung bericht berichtet sollen könnte koennte
""".split())

# Equivalences are search hints only, not assertions of one identical event.
TOKEN_EQUIVALENTS={
    "aktien":"stock","aktie":"stock","stocks":"stock","equities":"stock",
    "shares":"stock","techwerte":"tech","technologieaktien":"tech",
    "technology":"tech","technologie":"tech","ai":"ki",
    "selloff":"verkaufswelle","ausverkauf":"verkaufswelle",
    "sell":"verkaufswelle","einbruch":"verkaufswelle",
    "central":"zentral","banks":"bank","banken":"bank",
    "inflationary":"inflation","rates":"zins","interest":"zins",
}
TOKEN_RE=re.compile(r"[a-z0-9]+",re.ASCII)

def news_terms(value):
    """Fuzzy word anchors from *public* text, never proof of same event."""
    normal=unicodedata.normalize("NFKD",str(value).casefold().replace("ß","ss"))
    plain="".join(ch for ch in normal if not unicodedata.combining(ch))
    return {TOKEN_EQUIVALENTS.get(t,t) for t in TOKEN_RE.findall(plain)
            if len(t)>=3 and t not in NEWS_STOPWORDS and not t.isdigit()}

def cluster_candidates(ed):
    """Advisory pairs; no mutation, automatic grouping, deletion or censorship.

    Explicit event keys are precise editorial annotations. Other candidates
    use conservative public-title+summary overlap and require human review.
    """
    entries=[("headlines",a) for a in ed["headlines"]]+[
        ("articles",a) for a in ed["articles"]]
    groups={}
    for section,a in entries:
        if a.get("event_key"):
            groups.setdefault(a["event_key"],[]).append((section,a))
    named=[{"event_key":key,"articles":[{"id":a["id"],"title":a["title"],"section":section,
            "distinct_contribution":a.get("distinct_contribution")}
            for section,a in rows]} for key,rows in sorted(groups.items())
            if len(rows)>1]
    document_frequency=Counter(t for _,a in entries for t in news_terms(a["title"]))
    limit=max(3,len(entries)//3)
    possible=[]
    for i,(section_a,a) in enumerate(entries):
        for section_b,b in entries[i+1:]:
            if a.get("event_key") and a.get("event_key")==b.get("event_key"):
                continue
            title_a={x for x in news_terms(a["title"]) if document_frequency[x]<=limit}
            title_b={x for x in news_terms(b["title"]) if document_frequency[x]<=limit}
            shared=title_a & title_b
            if not shared:
                continue
            union=title_a | title_b
            denom=min(len(title_a),len(title_b))
            title_sim=len(shared)/len(union) if union else 0
            containment=len(shared)/denom if denom else 0
            a_summary=news_terms(a["summary"]);b_summary=news_terms(b["summary"])
            body_common=a_summary & b_summary
            body_overlap=len(body_common)/len(a_summary|b_summary) if a_summary|b_summary else 0
            similar_titles=len(shared)>=3 and (title_sim>=0.40 or containment>=0.75)
            similar_story=(len(shared)>=2 and len(body_common)>=5 and body_overlap>=0.32)
            if not (similar_titles or similar_story):
                continue
            possible.append({
                "first":{"id":a["id"],"title":a["title"],"section":section_a},
                "second":{"id":b["id"],"title":b["title"],"section":section_b},
                "shared_title_terms":sorted(shared),
                "hint":"similar_titles" if similar_titles else "overlapping_descriptions",
            })
    # Use IDs and titles, not arbitrary article positions, for reproducible logs.
    possible.sort(key=lambda x:(x["first"]["id"],x["second"]["id"]))
    return {"explicit_event_groups":named,"possible_same_event":possible,
            "without_event_key":sum(not a.get("event_key") for _,a in entries),
            "total":len(entries)}

def historical_overlap(ed,prior_editions):
    """Flag exact URL reruns or already curated event keys across real editions.

    Re-use might be justified by a new angle or factual update: *never* delete.
    """
    current=[("headlines",a) for a in ed["headlines"]]+[
        ("articles",a) for a in ed["articles"]]
    earlier={}
    for old in prior_editions:
        if old.get("preview") or old.get("date")==ed.get("date"):
            continue
        for a in old.get("headlines",[])+old.get("articles",[]):
            earlier.setdefault(canonical(a["url"]),[]).append((old["date"],a))
    notes=[]
    for section,a in current:
        for day,previous in earlier.get(canonical(a["url"]),[]):
            notes.append({"date":day,"id":a["id"],"title":a["title"],
                          "section":section,"prior_id":previous["id"],"reason":"same_original_url"})
    return sorted(notes,key=lambda x:(x["date"],x["id"]))

def print_cluster_review(ed,prior_editions=()):
    """Human-readable prepublication report; this is not a publish gate."""
    report=cluster_candidates(ed)
    print(f"CLUSTER REVIEW {ed['date']}: {report['total']} articles; "
          f"{report['without_event_key']} without event_key.")
    for group in report["explicit_event_groups"]:
        print("KNOWN EVENT",group["event_key"],":")
        for row in group["articles"]:
            extra=" (independent angle recorded)" if row["distinct_contribution"] else " (compare contribution)"
            print(f"  {row['section']} / {row['id']}: {row['title']}{extra}")
    for row in report["possible_same_event"]:
        print(f"CHECK POTENTIAL OVERLAP {row['first']['id']} / {row['second']['id']}: "
              f"{row['first']['title']} | {row['second']['title']}; "
              f"hint={row['hint']}; shared={', '.join(row['shared_title_terms'])}")
    for row in historical_overlap(ed,prior_editions):
        print(f"CHECK REPEATED ORIGINAL from {row['date']}: {row['title']} ({row['id']})")
    print("EDITORIAL DECISION REQUIRED: verify specific event, timing, primary "
          "report vs independent angle; preserve substantive counterpositions. "
          "No article removed or event_key inferred automatically.")
    if not report["possible_same_event"] and not report["explicit_event_groups"]:
        print("No strong lexical candidate found; manual cross-language and "
              "same-event review is still essential.")
    return report


# Phase 4: explicit, read-only publication-source signals. These numbers
# trigger HUMAN questions; they never feed a ranking, quota or publication gate.
SOURCE_ALIASES={
    "orf science":"ORF","orf":"ORF",
    "reuters":"Reuters","associated press":"AP","ap":"AP",
    "financial times":"Financial Times",
    "the guardian":"The Guardian","guardian":"The Guardian",
}
def publisher_group(value):
    """Normalize *declared publication* names without guessing syndication."""
    cleaned=" ".join(str(value or "").strip().split())
    key=cleaned.casefold()
    return SOURCE_ALIASES.get(key,cleaned)

def diversity_snapshot(ed):
    """Summarize visible source exposure; never infer ideology or preferences."""
    if ed.get("preview"):
        return {"date":ed.get("date"),"preview":True,"total":0,"sections":{},
                "alerts":[],"all_sources":[]}
    entries=[("Heute wichtig",a) for a in ed["headlines"]]+[
        ("Vertiefungen",a) for a in ed["articles"]]
    sections={}
    alerts=[]
    for label,rows in [
        ("Gesamtausgabe",[a for _,a in entries]),
        ("Heute wichtig",ed["headlines"]),
        ("Vertiefungen",ed["articles"])
    ]:
        count=Counter(publisher_group(a["source"]) for a in rows)
        ordered=sorted(count.items(),key=lambda p:(-p[1],p[0]))
        sections[label]={"total":len(rows),"sources":[
            {"source":publisher,"count":n} for publisher,n in ordered],
            "distinct_source_groups":len(ordered)}
        # These are advisory thresholds, NEVER quotas or automatic removals.
        if len(rows)>=6:
            alerts.extend({"section":label,"source":publisher,"count":n,
                           "total":len(rows),"kind":"concentration_to_review"}
                          for publisher,n in ordered if n>=4 and n*5>=len(rows)*2)
    genres=Counter(str(a.get("article_type") or "nicht klassifiziert").strip()
                   for _,a in entries)
    return {"date":ed["date"],"preview":False,"total":len(entries),
            "sections":sections,
            "all_sources":sections["Gesamtausgabe"]["sources"],
            "article_types":[{"type":key,"count":num}
                             for key,num in sorted(genres.items())],
            "news_regions":dict(sorted(Counter(
                a.get("region","nicht klassifiziert") for a in ed["headlines"]).items())),
            "alerts":alerts}

def recurring_concentration(ed,prior_editions=()):
    """Flag repeated dependence on a publisher without suppressing that source."""
    editions=[ed]+[x for x in prior_editions if not x.get("preview") and x.get("date")!=ed["date"]]
    snapshots=[diversity_snapshot(x) for x in editions]
    per_source={}
    for snap in snapshots:
        for signal in snap["alerts"]:
            if signal["section"]!="Gesamtausgabe":
                continue
            per_source.setdefault(signal["source"],[]).append(snap["date"])
    return [{"source":name,"dates":sorted(set(days),reverse=True)}
            for name,days in sorted(per_source.items())
            if len(set(days))>=2]

def print_diversity_review(ed,prior_editions=()):
    """Advisory newsroom review with no file writes or content decisions."""
    snap=diversity_snapshot(ed)
    if snap["preview"]:
        print("DIVERSITY REVIEW: imported preview; not an independently researched issue.")
        return snap
    print(f"DIVERSITY REVIEW {snap['date']}: {snap['total']} articles.")
    for section,details in snap["sections"].items():
        described=", ".join(f"{p['source']}: {p['count']}"
                            for p in details["sources"]) or "(no articles)"
        print(f"PUBLICATION SOURCES {section} ({details['total']}): {described}")
    print("NEWS REGIONS: "+", ".join(
        f"{area}: {n}" for area,n in snap["news_regions"].items()))
    print("ARTICLE TYPES: "+", ".join(
        f"{p['type']}: {p['count']}" for p in snap["article_types"]))
    for alert in snap["alerts"]:
        print(f"REVIEW CONCENTRATION ({alert['section']}): {alert['source']} "
              f"{alert['count']}/{alert['total']}. This is not a source quota.")
    for recurring in recurring_concentration(ed,prior_editions):
        print(f"REVIEW REPEATED CONCENTRATION: {recurring['source']} across "
              f"{', '.join(recurring['dates'])}")
    print("EDITORIAL REVIEW REQUIRED: check independently sourced ORIGINALS, "
          "agency republications, neglected strong alternatives, topic/country "
          "breadth, scientific/primary evidence, views challenging existing "
          "assumptions, and fair contrary evidence. A numerical concentration "
          "alone does not justify removal or token publisher substitution.")
    print("PERSONALIZATION SAFEGUARD: do not infer a topic ban from one negative "
          "rating, lack of feedback, suggested-reason clicks or poor access "
          "to paywalled originals. Test competing hypotheses against genuine "
          "freely written feedback and later reader response.")
    print("NO AUTOMATIC ACTION: no article, topic, publisher, ranking or reader "
          "preference was changed. Editorial judgement and verifiable evidence "
          "are required; no source quotas or enforced balance.")
    return snap

def editorial_warnings(ed):
    """Advisory newsroom signals; not a semantic classifier or publication veto."""
    if ed["preview"]: return []
    entries=ed["headlines"]+ed["articles"]
    missing=sum(1 for a in entries if not a.get("event_key"))
    warnings=[]
    if missing:
        warnings.append(f"{missing} article(s) have no event_key; check event overlap manually")
    events={}
    for a in entries:
        key=a.get("event_key")
        if key:events.setdefault(key,[]).append(a)
    for key,rows in events.items():
        if len(rows)>1 and any(not a.get("distinct_contribution") for a in rows[1:]):
            warnings.append(f"Event {key!r} appears {len(rows)} times; document what is genuinely new")
    return warnings

def verify(root=ROOT):
    index=json.loads((root/"index.json").read_text())
    days=index["dates"]
    if days!=sorted(set(days),reverse=True): raise ValueError("Index is not unique descending")
    if set(days)!={f.stem for f in root.glob("????-??-??.json")}:
        raise ValueError("Index must match all edition files")
    warnings=[]
    for day in days:
        date.fromisoformat(day)
        ed=json.loads((root/(day+".json")).read_text())
        validate(ed)
        if ed["date"]!=day: raise ValueError("Date mismatch")
        warnings.extend(f"{day}: {item}" for item in editorial_warnings(ed))
    return len(days),warnings

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("verify","cluster-review","diversity-review"))
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--date",help="Date YYYY-MM-DD to review; latest if omitted")
    p.add_argument("--previous-days",type=int,default=3,
                   help="Number of prior published issues for exact-URL repeat checks")
    args=p.parse_args()
    if args.action=="verify":
        count,warnings=verify(args.root)
        print(f"PASS: {count} edition(s); structural test only. Source evidence needs editorial review.")
        for note in warnings:
            print("EDITORIAL REVIEW (non-blocking): "+note)
    else:
        if not 0<=args.previous_days<=30:
            p.error("--previous-days must be 0..30")
        days=json.loads((args.root/"index.json").read_text())["dates"]
        selected=args.date or (days[0] if days else None)
        if selected not in days:
            p.error("--date must refer to a published indexed issue")
        ed=json.loads((args.root/(selected+".json")).read_text())
        validate(ed)
        older=[json.loads((args.root/(day+".json")).read_text())
               for day in days if day<selected][:args.previous_days]
        if args.action=="cluster-review":
            print_cluster_review(ed,older)
        else:
            print_diversity_review(ed,older)
if __name__=="__main__": main()
