"""Access-neutral editorial scoring, real-feedback learning and private evidence guards.
No network requests, no article URL status checks. Semantic review is still required.
"""
import argparse, json, re
from collections import Counter
from datetime import datetime
from urllib.parse import urlsplit

PREFIX="[Morgenzeitung 3] Feedback "
MARKER="MORGENZEITUNG_V3_FEEDBACK_V1\n"
ID=re.compile(r"^[a-f0-9]{16}$")
DATE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
NUMBER=re.compile(r"(?<![\w])\d+(?:[.,]\d+)*(?:\s?%)?")
QUOTE=re.compile(r"[„\"]([^“\"]{3,})[“\"]")
CAUSE=re.compile(r"\b(?:verursach\w*|führt(?:e)?\s+(?:damit\s+)?zu|aufgrund|infolge|weil)\b",re.I)

def valid_url(value):
    try:
        x=urlsplit(value)
        return x.scheme=="https" and bool(x.hostname) and not (x.username or x.password)
    except (ValueError, TypeError): return False

def score(item, profile):
    # Full text, paywalls, HTTP status, excerpt length are deliberately NOT read.
    weights=(("fit",4),("novelty",3),("impact",2),("perspective",1))
    value=0
    for key,weight in weights:
        x=item.get(key,0)
        if isinstance(x,bool) or not isinstance(x,(int,float)) or not 0<=x<=5:
            raise ValueError(key+" must be 0..5")
        value+=x*weight
    topic=item.get("topic","")
    base=profile.get("topic_priorities",{}).get(topic,3)
    delta=profile.get("feedback_topic_deltas",{}).get(topic,0)
    if isinstance(base,bool) or not isinstance(base,(int,float)) or not 0<=base<=5: base=3
    if isinstance(delta,bool) or not isinstance(delta,(int,float)): delta=0
    return value+1.25*(base+max(-2,min(2,delta))-3)

def select(candidates, profile, limit=15, discovery_slots=2):
    if not isinstance(limit,int) or not 1<=limit<=15: raise ValueError("limit")
    pool=[]
    for i,item in enumerate(candidates):
        if not all(item.get(k) for k in ("id","title","source","url","topic")): continue
        if not ID.fullmatch(item["id"]) or not valid_url(item["url"]): continue
        pool.append((score(item,profile),i,item))
    pool.sort(key=lambda x:(-x[0],x[1]))
    chosen=[]; events=set(); urls=set()
    for s,_,item in pool:
        event=item.get("event") or item["url"]
        if event in events or item["url"] in urls: continue
        chosen.append((s,item));events.add(event);urls.add(item["url"])
        if len(chosen)==limit: break
    discoveries=sum(bool(x.get("discovery")) for _,x in chosen)
    if discovery_slots and len(chosen)>=discovery_slots:
        for s,_,item in pool:
            if discoveries>=discovery_slots:break
            if not item.get("discovery") or any(x["id"]==item["id"] for _,x in chosen):continue
            if any((x.get("event") or x["url"])==(item.get("event") or item["url"]) for _,x in chosen):continue
            replace=next((i for i in range(len(chosen)-1,-1,-1)
                          if not chosen[i][1].get("discovery") and chosen[i][0]-s<=7.5),None)
            if replace is not None and s>=15:
                chosen[replace]=(s,item);discoveries+=1
        chosen.sort(key=lambda x:-x[0])
    return [x for _,x in chosen]

def compare_learning(pool,before,after,new_feedback=False,limit=15):
    old=[x["id"] for x in select(pool,before,limit)]
    new=[x["id"] for x in select(pool,after,limit)]
    return {"feedback_applied":bool(new_feedback and old!=new),
            "feedback_received":bool(new_feedback),"selection_changed":old!=new,
            "before_ids":old,"after_ids":new,
            "added_ids":[x for x in new if x not in old],
            "removed_ids":[x for x in old if x not in new]}

def ingest_feedback(profile,issues,topics_by_id):
    """Replace edited Issue snapshots; negative topic generalization needs explicit reasons."""
    out=json.loads(json.dumps(profile))
    stored=out.setdefault("feedback_by_issue",{})
    processed=out.setdefault("processed_new_issues",{})
    changed=[]
    for issue in issues:
        title,body=issue.get("title",""),issue.get("body","")
        if not isinstance(title,str) or not isinstance(body,str) or issue.get("pull_request"):continue
        if not title.startswith(PREFIX) or not body.startswith(MARKER):continue
        try:
            payload=json.loads(body[len(MARKER):]);date=payload["date"]
            if not DATE.fullmatch(date) or title!=PREFIX+date or payload.get("origin")!="website-explicit" or payload.get("test"):continue
            if not isinstance(payload.get("ratings"),list):continue
            key=str(int(issue["number"]))
            rows=[]
            for row in payload["ratings"][:40]:
                if isinstance(row,dict) and ID.fullmatch(str(row.get("id",""))) and row.get("rating") in ("Sehr relevant","Teilweise relevant","Nicht relevant"):
                    rows.append({"id":row["id"],"rating":row["rating"],
                                 "reason":str(row.get("reason",""))[:600],
                                 "topic":topics_by_id.get(row["id"],"")})
            snapshot={"updated_at":str(issue.get("updated_at","")),"ratings":rows}
            if stored.get(key)!=snapshot:
                stored[key]=snapshot;processed[key]=snapshot["updated_at"];changed.append(key)
        except (KeyError,TypeError,ValueError):continue
    # Only latest evaluation per article, no phantom votes on edit.
    articles={}
    for saved in stored.values():
        for row in saved.get("ratings",[]):articles[row["id"]]=row
    pos,neg=Counter(),Counter()
    for row in articles.values():
        topic=row.get("topic");reason=row.get("reason","").lower()
        if not topic:continue
        if row["rating"]=="Sehr relevant":pos[topic]+=1
        if row["rating"]=="Nicht relevant" and any(x in reason for x in
            ("thema interessiert mich nicht","thema nicht interessant","weniger über","grundsätzlich uninteressant")):neg[topic]+=1
    out["feedback_topic_deltas"]={k:max(-2,min(2,pos[k]//2-neg[k]//2)) for k in set(pos)|set(neg)}
    return out,changed

def evidence_guard(edition,dossier):
    """PRIVATE short excerpts; warning is not an automatic claim of semantic falsity."""
    proofs=dossier.get("proofs",{}); warnings=[]; checked=0
    for item in [*edition.get("articles",[]),*edition.get("headlines",[])]:
        key=item.get("id","?"); proof=proofs.get(key,{})
        if not proof or proof.get("source_url")!=item.get("url"):
            warnings.append({"id":key,"code":"MISSING_PROVENANCE"});continue
        level=proof.get("level")
        if level not in ("headline","teaser","read"):
            warnings.append({"id":key,"code":"INVALID_LEVEL"})
        claims=proof.get("claims",[])
        if not isinstance(claims,list) or not claims:
            warnings.append({"id":key,"code":"MISSING_CLAIMS"});continue
        if " ".join(str(c.get("text","")).strip() for c in claims)!=item.get("summary","").strip():
            warnings.append({"id":key,"code":"UNCOVERED_SUMMARY"})
        for claim in claims:
            checked+=1
            sentence=str(claim.get("text","")).strip()
            excerpt=str(claim.get("source_excerpt","")).strip()
            if claim.get("supported") is not True or len(excerpt)<12:
                warnings.append({"id":key,"code":"UNSUPPORTED_CLAIM","claim":sentence[:90]});continue
            nums=lambda s:{re.sub(r"\s+","",x) for x in NUMBER.findall(s)}
            for x in nums(sentence)-nums(excerpt):
                warnings.append({"id":key,"code":"NUMBER_MISMATCH","number":x})
            for x in QUOTE.findall(sentence):
                if x not in excerpt:warnings.append({"id":key,"code":"QUOTE_MISMATCH","quote":x[:90]})
            if CAUSE.search(sentence) and not claim.get("causality_verified",False):
                warnings.append({"id":key,"code":"CAUSALITY_UNCONFIRMED","claim":sentence[:90]})
            if level=="headline" and len(sentence.split())>30:
                warnings.append({"id":key,"code":"HEADLINE_ONLY_OVERREACH"})
    return {"status":"warn" if warnings else "pass","warning_count":len(warnings),
            "claims_checked":checked,"warnings":warnings,
            "note":"Mechanical guard only; editorial semantic check remains obligatory"}

def validate_edition(ed):
    errors=[]; date=ed.get("date")
    if not isinstance(date,str) or not DATE.fullmatch(date):errors.append("invalid date")
    for key in ("researched_at","available_at"):
        try:datetime.fromisoformat(ed[key].replace("Z","+00:00"))
        except (KeyError,TypeError,ValueError,AttributeError):errors.append("invalid "+key)
    if not isinstance(ed.get("preview"),bool):errors.append("invalid preview")
    ids=set();urls=set()
    for section,limit in (("articles",15),("headlines",20)):
        rows=ed.get(section,[])
        if not isinstance(rows,list) or not 1<=len(rows)<=limit:
            errors.append("invalid count "+section);continue
        for row in rows:
            if (not isinstance(row,dict) or not ID.fullmatch(str(row.get("id","")))
                or not all(row.get(k) for k in ("title","url","source","summary","published_at"))
                or not valid_url(row.get("url"))):
                errors.append("invalid identity");continue
            if row["id"] in ids or row["url"] in urls:errors.append("duplicate")
            ids.add(row["id"]);urls.add(row["url"])
            if section=="articles" and not row.get("topic"):errors.append("missing topic")
            if section=="headlines" and row.get("region") not in ("Österreich","International"):
                errors.append("missing region")
    if ed.get("preview") is False:
        facts=ed.get("fact_audit",{})
        if not isinstance(facts,dict) or facts.get("status")!="pass" or facts.get("warning_count")!=0 or facts.get("claims_checked",0)<len(ids):
            errors.append("fact audit not passed")
        if not isinstance(ed.get("selection_audit",{}).get("feedback_applied"),bool):
            errors.append("missing selection audit")
    return errors

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["verify","rank","facts","compare","learn"])
    for a in ("edition","dossier","candidates","profile","before","issues","topic-map"):p.add_argument("--"+a)
    p.add_argument("--new-feedback",action="store_true")
    a=p.parse_args()
    def read(path):
        if not path:raise ValueError("required path missing")
        with open(path,encoding="utf-8") as f:return json.load(f)
    if a.action=="verify":out={"errors":validate_edition(read(a.edition))}
    elif a.action=="rank":out=select(read(a.candidates),read(a.profile))
    elif a.action=="facts":out=evidence_guard(read(a.edition),read(a.dossier))
    elif a.action=="compare":out=compare_learning(read(a.candidates),read(a.before),read(a.profile),a.new_feedback)
    else:
        out,changed=ingest_feedback(read(a.profile),read(a.issues),read(a.topic_map))
        out["_changed_issue_ids"]=changed
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if (a.action=="verify" and out["errors"]) or (a.action=="facts" and out["status"]=="warn"):
        raise SystemExit(2)

if __name__=="__main__":main()
