"""Structural checks only for Morgenzeitung Neu: journalistic truth requires human/AI source review."""
import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl, urlencode, urlunsplit

ROOT=Path("Privat/Morgenzeitung-Neu/data")
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
            level=a.get("evidence_level")
            if not ed["preview"] and level not in ("headline","teaser","read","unknown"):
                raise ValueError("Missing source evidence level")
            if level is not None and level not in ("headline","teaser","read","unknown"):
                raise ValueError("Invalid source evidence level")
            url=canonical(a["url"])
            if a["id"] in ids or url in urls: raise ValueError("Duplicate ID/URL")
            ids.add(a["id"]);urls.add(url)

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
    p.add_argument("action",choices=("verify",))
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    count,warnings=verify(args.root)
    print(f"PASS: {count} edition(s); structural test only. Source evidence needs editorial review.")
    for note in warnings:
        print("EDITORIAL REVIEW (non-blocking): "+note)
if __name__=="__main__": main()
