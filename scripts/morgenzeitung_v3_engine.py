"""Access-neutral editorial scoring, real-feedback learning and private evidence guards.
No network requests, no article URL status checks. Semantic review is still required.
"""
import argparse, hashlib, json, re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from scripts.morgenzeitung_v3_editorial import (
    reason_labels, style_signals, feedback_dimensions, editorial_depth_review,
    editorial_feedback_metrics, editorial_mix_report,
    calibration_review, edition_feedback_review, edition_series_review
)

from scripts.morgenzeitung_v3_schema import validate_article_metadata

from scripts.morgenzeitung_v3_quality import (
    v1_comparison, calibration_review_from_feedback, reader_comparison_candidates
)

PREFIX="[Morgenzeitung 3] Feedback "
MARKER="MORGENZEITUNG_V3_FEEDBACK_V1\n"
ID=re.compile(r"^[a-f0-9]{16}$")
DATE=re.compile(r"^\d{4}-\d{2}-\d{2}$")
NUMBER=re.compile(r"(?<![\w])\d+(?:[.,]\d+)*(?:\s?%)?")
QUOTE=re.compile(r"[„\"]([^“\"]{3,})[“\"]")
CAUSE=re.compile(r"\b(?:verursach\w*|führt(?:e)?\s+(?:damit\s+)?zu|aufgrund|infolge|weil)\b",re.I)
MONTHS=re.compile(r"\b(?:januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember)\b",re.I)
PERSON=re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]{2,}\s+[A-ZÄÖÜ][a-zäöüß]{2,}\b")
ACRONYM=re.compile(r"\b[A-ZÄÖÜ]{2,6}\b")

def numeric_facts(sentence):
    """Normalize decimal comma/point and thousands separators without fetching URLs."""
    values=set()
    for raw in NUMBER.findall(sentence):
        n=re.sub(r"\s+","",raw)
        pct=n.endswith("%")
        n=n.rstrip("%")
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+",n):
            n=n.replace(".","").replace(",","")
        elif re.fullmatch(r"\d+[.,]\d{1,2}",n):
            n=n.replace(",",".")
        values.add(n+("%" if pct else ""))
    return values


def valid_url(value):
    try:
        x=urlsplit(value)
        return x.scheme=="https" and bool(x.hostname) and not (x.username or x.password)
    except (ValueError, TypeError): return False

def topic_family(topic, profile):
    """Match exact subtopic first, then a documented broad parent, never fuzzy guesses."""
    priorities=profile.get("topic_priorities",{})
    aliases=profile.get("topic_aliases",{})
    if topic in priorities: return topic
    if topic in aliases and aliases[topic] in priorities: return aliases[topic]
    t=(topic or "").lower()
    families=(
        (("ki", "künstliche intelligenz"), "KI"),
        (("industrie", "fertigung"), "Industrie & Innovation"),
        (("klima", "energie", "emission"), "Klima & Energie"),
        (("bildung", "forschung"), "Bildung & Forschung"),
        (("fiskal", "wirtschaft", "konjunktur", "inflation"), "Wirtschaft & Fiskalpolitik"),
        (("produktiv", "wettbewerb"), "Produktivität & Wettbewerbsfähigkeit"),
        (("welt", "handel", "geopolit"), "Welthandel & Geopolitik")
    )
    for fragments, parent in families:
        if any(w in t for w in fragments) and parent in priorities: return parent
    return topic


def article_penalty(item, profile):
    """Direct reader feedback affects *that article*, not the whole subject."""
    feedback=profile.get("article_feedback",{}).get(item.get("id"),{})
    rating=feedback.get("rating")
    penalty= -13 if rating=="Nicht relevant" else 0
    reason=feedback.get("reason","").lower()
    if "schon bekannt" in reason: penalty-=7
    # Seen-recently costs 12 points once in score(), equally in both sections.
    return penalty


def score(item, profile, section="Vertiefungen"):
    """Different editorial standards for news and in-depth analysis.

    Neither type uses full-text reachability, length, paywalls or HTTP status.
    Breaking news is ranked by significance, not personal topic popularity.
    """
    if section not in ("Vertiefungen", "Heute wichtig"):
        raise ValueError("unknown editorial section")
    if item.get("novelty_score") is not None and item.get("novelty") is not None:
        if item["novelty_score"] != item["novelty"]:
            raise ValueError("novelty_score conflicts with legacy novelty")
    weights=(("fit",4),("novelty",3),("impact",2),("perspective",1))
    if section=="Heute wichtig":
        weights=(("fit",0),("novelty",3),("impact",5),("perspective",2))
    value=0
    for key,weight in weights:
        x=(item.get("novelty_score") if item.get("novelty_score") is not None else item.get("novelty",0)) if key=="novelty" else item.get(key,0)
        if isinstance(x,bool) or not isinstance(x,(int,float)) or not 0<=x<=5:
            raise ValueError(key+" must be 0..5")
        value+=x*weight
    # Repeats should not crowd out true updates in either section.
    repeated=-12 if item.get("seen_recently") and not item.get("material_update") else 0
    if section=="Heute wichtig":
        return value+repeated
    topic=topic_family(item.get("topic",""), profile)
    base=profile.get("topic_priorities",{}).get(topic,3)
    delta=profile.get("feedback_topic_deltas",{}).get(topic,0)
    if isinstance(base,bool) or not isinstance(base,(int,float)) or not 0<=base<=5: base=3
    if isinstance(delta,bool) or not isinstance(delta,(int,float)): delta=0
    style=profile.get("style_preference_signals") or {}
    # When two or more explicit style critiques agree within a subject,
    # prefer that topic-specific signal over the general editorial preference.
    topic_style=(profile.get("topic_style_signals") or {}).get(topic) or {}
    style={**style,**topic_style}
    novelty_demand=style.get("novelty",0)
    if isinstance(novelty_demand,bool) or not isinstance(novelty_demand,(int,float)):
        novelty_demand=0
    novelty_adjustment=min(2,max(0,novelty_demand))*((item.get("novelty_score") if item.get("novelty_score") is not None else item.get("novelty",0))-2.5)
    # Only genuine, pre-selection editorial assessments based on comparable
    # headline/teaser metadata can be used. Missing values are neutral.
    # Accessible full-text volume is NEVER a quality assessment or proxy.
    def quality_adjustment(signal,key):
        intensity=style.get(signal,0)
        if not isinstance(intensity,(int,float)) or isinstance(intensity,bool):return 0
        quality=item.get(key)
        if quality is None:return 0
        if not isinstance(quality,(int,float)) or isinstance(quality,bool) or not 0<=quality<=5:
            raise ValueError(key+" must be 0..5")
        return min(2,max(0,intensity))*(quality-2.5)
    style_adjustment=(quality_adjustment("analysis","analysis_value")
                      +quality_adjustment("broader_context","context_value")
                      +quality_adjustment("perspectives","perspective"))
    return (value+1.25*(base+max(-2,min(2,delta))-3)
            +article_penalty(item,profile)+novelty_adjustment+style_adjustment)

def normalized_url(value):
    u=urlsplit(value)
    query=urlencode(sorted((k,v) for k,v in parse_qsl(u.query,keep_blank_values=True)
                           if not k.lower().startswith("utm_") and k.lower() not in ("fbclid","gclid")))
    return urlunsplit((u.scheme,u.netloc.lower(),u.path.rstrip("/"),query,""))


def stable_article_id(url):
    """Stable original-article identity for NEW V3 candidates.

    Historical date-based IDs remain valid and untouched. The research agent
    may use this before first capture; feedback is never re-keyed retroactively.
    """
    if not valid_url(url):
        raise ValueError("Invalid original article URL")
    return hashlib.sha256(normalized_url(url).encode("utf-8")).hexdigest()[:16]


def distinct_perspective(a,b):
    """Two separately attributed analytical views can address the same event."""
    return bool(a.get("debate_id") and a.get("debate_id")==b.get("debate_id")
                and a.get("viewpoint") in ("support","oppose")
                and b.get("viewpoint") in ("support","oppose")
                and a["viewpoint"]!=b["viewpoint"]
                and a.get("source")!=b.get("source")
                and a.get("article_type") in ("analysis","opinion","investigation")
                and b.get("article_type") in ("analysis","opinion","investigation"))


def duplicate_story(item, chosen):
    """Conservative cross-publisher detection; uncertain reports remain eligible."""
    if any((x.get("event") and item.get("event") and (x["event"]==item["event"] and not distinct_perspective(item,x)))
           or normalized_url(x["url"])==normalized_url(item["url"])
           for _,x in chosen):
        return True
    def words(title):
        stop={"über","eine","einer","eines","sich","nach","auch","weil","nicht",
              "wird","sind","diese","dieser","steht","steht","sowie","mehr","beim"}
        return set(x for x in re.findall(r"[\wäöüß]{4,}",title.casefold()) if x not in stop)
    t=words(item.get("title",""))
    for _,x in chosen:
        u=words(x.get("title",""))
        if len(t)>=5 and len(u)>=5 and len(t&u)/len(t|u)>=.85 and not distinct_perspective(item,x):
            return True
    return False


def mark_recent_stories(candidates, previous_editions, edition_date, max_age_days=14):
    """Automatically mark already-covered articles/events from recent V3 editions.

    The history must consist of actual saved edition JSONs; no publisher network
    requests or assumptions about article reads. A material update must be
    documented separately, not asserted by a bare boolean.
    """
    if not previous_editions:
        return list(candidates)
    if not isinstance(edition_date,str) or not DATE.fullmatch(edition_date):
        raise ValueError("edition_date required with previous editions")
    current=datetime.strptime(edition_date,"%Y-%m-%d").date()
    recent=[]
    for old in previous_editions:
        if not isinstance(old,dict) or not DATE.fullmatch(str(old.get("date",""))):
            raise ValueError("invalid previous edition")
        day=datetime.strptime(old["date"],"%Y-%m-%d").date()
        if not (0<(current-day).days<=max_age_days):
            continue
        for section in ("articles","headlines"):
            for row in old.get(section,[]):
                if isinstance(row,dict) and isinstance(row.get("url"),str) and row.get("url"):
                    recent.append((0,row))
    enriched=[]
    for item in candidates:
        entry=dict(item)
        if recent and duplicate_story(entry,recent):
            entry["seen_recently"]=True
            old_stories=[row for _,row in recent if duplicate_story(entry,[(0,row)])]
            # Keep previous transmitted facts private in the scoring context.
            entry["known_facts"]=[fact for row in old_stories
                for fact in (row.get("facts") if isinstance(row.get("facts"),list)
                             else [row.get("summary","")]) if isinstance(fact,str) and fact.strip()]
            update=entry.get("update_evidence")
            evidence=update.strip() if isinstance(update,str) else ""
            # An update flag is never enough: demand specific, documented new
            # facts not identical to the text the user already received.
            known={" ".join(f.casefold().split()) for f in entry["known_facts"]}
            entry["material_update"]=bool(entry.get("material_update") and len(evidence)>=15
                and " ".join(evidence.casefold().split()) not in known)
        enriched.append(entry)
    return enriched


def load_edition_history(directory):
    """Read local V3 edition index only; no link testing or HTTP requests."""
    folder=Path(directory)
    idx=folder/"index.json"
    if not idx.is_file():
        raise ValueError("missing V3 history index")
    index=json.loads(idx.read_text(encoding="utf-8"))
    editions=[]
    for day in index.get("dates",[]):
        if not DATE.fullmatch(str(day)):
            raise ValueError("invalid V3 history date")
        file=folder/(day+".json")
        if not file.is_file():
            raise ValueError("missing V3 history edition "+day)
        editions.append(json.loads(file.read_text(encoding="utf-8")))
    return editions


def mix_adjustment(item, chosen, section):
    """Small soft diversity preference, never a mandatory publisher quota."""
    prior=[row for _,row in chosen]
    source=item.get("source","").casefold()
    same_source=sum(row.get("source","").casefold()==source for row in prior)
    score_delta=-1.5*max(0,same_source-1)
    if section=="Vertiefungen":
        genre=str(item.get("article_type") or item.get("kind") or "").casefold()
        if genre:
            n=sum(str(row.get("article_type") or row.get("kind") or "").casefold()==genre
                  for row in prior)
            score_delta-=1.2*max(0,n-2)
        topic=item.get("topic")
        if topic:
            n=sum(row.get("topic")==topic for row in prior)
            score_delta-=1.2*max(0,n-2)
    if section=="Vertiefungen" and any(distinct_perspective(item,row) for row in prior):
        score_delta+=1.5
    return max(-6.0,min(2.0,score_delta))


def select(candidates, profile, limit=None, discovery_slots=2,
           section="Vertiefungen", previous_editions=(), edition_date=None):
    if section not in ("Vertiefungen","Heute wichtig"):
        raise ValueError("unknown editorial section")
    if limit is None:
        limit=20 if section=="Heute wichtig" else 15
    if type(limit) is not int or not 1<=limit<=(20 if section=="Heute wichtig" else 15):
        raise ValueError("limit")
    pool=[]
    required=("id","title","source","url") if section=="Heute wichtig" else ("id","title","source","url","topic")
    for i,item in enumerate(mark_recent_stories(candidates,previous_editions,edition_date)):
        if not all(item.get(k) for k in required): continue
        if not ID.fullmatch(item["id"]) or not valid_url(item["url"]): continue
        pool.append((score(item,profile,section=section),i,item))
    pool.sort(key=lambda x:(-x[0],x[1]))
    chosen=[]
    remaining=list(pool)
    while remaining and len(chosen)<limit:
        available=[x for x in remaining if not duplicate_story(x[2],chosen)]
        if not available:break
        best=available[0][0]
        # Among candidates within six points, prefer editorial variety gently.
        # A weaker report must never displace a much stronger one.
        comparable=[x for x in available if x[0]>=best-6]
        winner=max(comparable,key=lambda x:(x[0]+mix_adjustment(x[2],chosen,section),-x[1]))
        chosen.append((winner[0],winner[2]))
        remaining=[x for x in remaining if x[1]!=winner[1]]
    discoveries=sum(bool(x.get("discovery")) for _,x in chosen)
    # No artificial discovery quota for the public-interest news section.
    if section=="Heute wichtig":
        discovery_slots=0
    if discovery_slots and len(chosen)>=discovery_slots:
        for s,_,item in pool:
            if discoveries>=discovery_slots:break
            if not item.get("discovery") or any(x["id"]==item["id"] for _,x in chosen):continue
            if duplicate_story(item,chosen):continue
            replace=next((i for i in range(len(chosen)-1,-1,-1)
                          if not chosen[i][1].get("discovery") and chosen[i][0]-s<=7.5),None)
            if replace is not None and s>=15:
                chosen[replace]=(s,item);discoveries+=1
        chosen.sort(key=lambda x:-x[0])
    return [x for _,x in chosen]

def missed_candidate_review(pool, selected, profile, section="Vertiefungen",
                            previous_editions=(), edition_date=None, max_suggestions=5):
    """Point to plausible editorial misses; NEVER infer a negative/positive rating.

    Compare the same candidate pool and consistent, preselection metadata.
    No URL checking, no automatic re-ranking, no saving as learning signals.
    """
    if not selected:
        return {"review_candidates":[],"reason":"no_selected_articles",
                "feedback_inferred":False}
    threshold=min(score(x,profile,section=section) for x in selected)
    selected_ids={x["id"] for x in selected}
    considered=[]
    for row in mark_recent_stories(pool,previous_editions,edition_date):
        if not isinstance(row,dict) or row.get("id") in selected_ids:continue
        required=("id","title","source","url") if section=="Heute wichtig" else (
            "id","title","source","url","topic")
        if not all(row.get(k) for k in required):continue
        if not ID.fullmatch(str(row["id"])) or not valid_url(row["url"]):continue
        value=score(row,profile,section=section)
        if value < threshold-6:continue
        same_story=duplicate_story(row,[(0,item) for item in selected])
        considered.append({"id":row["id"],"source":row["source"],
                           "topic":row.get("topic"),"score":round(value,2),
                           "compared_to_lowest_selected":round(value-threshold,2),
                           "review_reason":"alternate_story_coverage" if same_story
                               else "comparable_relevance_but_omitted"})
    considered.sort(key=lambda x:(-x["score"],x["id"]))
    return {"review_candidates":considered[:max_suggestions],
            "considered_near_cutoff":len(considered),
            "review_only":True,"feedback_inferred":False,
            "note":"An omitted candidate is not a user preference. Editorially inspect fit, novelty and distinct new facts; never auto-promote."}


def compare_learning(pool,before,after,new_feedback=False,limit=None,
                     section="Vertiefungen",previous_editions=(),edition_date=None):
    old=[x["id"] for x in select(pool,before,limit,section=section,
                                 previous_editions=previous_editions,edition_date=edition_date)]
    new=[x["id"] for x in select(pool,after,limit,section=section,
                                 previous_editions=previous_editions,edition_date=edition_date)]
    return {"feedback_applied":bool(new_feedback and old!=new),
            "feedback_received":bool(new_feedback),"selection_changed":old!=new,
            "before_ids":old,"after_ids":new,
            "added_ids":[x for x in new if x not in old],
            "removed_ids":[x for x in old if x not in new]}

def ingest_feedback(profile, issues, topics_by_id):
    """Replace genuine edited V3 issue snapshots, never double-count feedback.

    Article quality, general subject interest and explicit requests stay
    distinct. Headlines inform public-interest news, not subject preference.
    """
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
            previous=stored.get(key)
            updated=str(issue.get("updated_at",""))
            if previous and updated<previous.get("updated_at",""):
                continue
            rows=[]
            for row in payload["ratings"][:100]:
                if not isinstance(row,dict) or not ID.fullmatch(str(row.get("id",""))) or row.get("rating") not in ("Sehr relevant","Teilweise relevant","Nicht relevant"):
                    continue
                section=row.get("section","Vertiefungen")
                if section not in ("Vertiefungen","Heute wichtig"):continue
                raw_topic=topics_by_id.get(row["id"],"")
                # A caller may supply an explicit typed article record; keep
                # compatibility with earlier simple string topic maps.
                topic=raw_topic.get("topic","") if isinstance(raw_topic,dict) else raw_topic
                rows.append({"id":row["id"],"rating":row["rating"],
                             "section":section,"reason":str(row.get("reason",""))[:600],
                             "topic":topic if isinstance(topic,str) else ""})
            snapshot={"updated_at":updated,"date":date,"ratings":rows,
                      "comment":str(payload.get("comment",""))[:4000]}
            if stored.get(key)!=snapshot:
                stored[key]=snapshot;processed[key]=snapshot["updated_at"];changed.append(key)
        except (KeyError,TypeError,ValueError):continue
    articles={}
    for issue_number,saved in sorted(stored.items(),
                    key=lambda x:(x[1].get("updated_at",""),int(x[0]))):
        for row in saved.get("ratings",[]):
            articles[row["id"]]={**row,"updated_at":saved.get("updated_at",""),
                                "date":saved.get("date",""),"source_issue":issue_number}
    out["article_feedback"]=dict(list(sorted(articles.items(),
        key=lambda x:x[1].get("updated_at",""),reverse=True))[:1000])
    # The editorial agent must review explicit requests, never execute free
    # text as commands or infer a numerical weight without reader consent.
    out["explicit_reader_requests"]=[
        {"date":saved.get("date",""),"updated_at":saved.get("updated_at",""),
         "issue":issue_number,"text":saved["comment"]}
        for issue_number,saved in sorted(stored.items())
        if isinstance(saved.get("comment"),str) and saved["comment"].strip()
    ][-100:]
    pos,neg=Counter(),Counter()
    exact_evidence={}
    family_evidence={}
    style_by_topic={}
    for row in articles.values():
        if row.get("section","Vertiefungen")!="Vertiefungen":
            continue
        raw_topic=row.get("topic","")
        if not raw_topic:continue
        topic=topic_family(raw_topic,out)
        reason_labels_for_row=reason_labels(row.get("reason",""),row.get("rating"))
        current=exact_evidence.setdefault(topic,Counter())
        current[row["rating"]]+=1
        if row["rating"]=="Sehr relevant":
            pos[topic]+=1
        if row["rating"]=="Nicht relevant" and "topic_dislike" in reason_labels_for_row:
            neg[topic]+=1
        # Do not infer broad interest from geographic metadata or free text.
        aliases=out.get("topic_aliases") or {}
        parent=aliases.get(raw_topic)
        if parent and parent!=topic and parent in out.get("topic_priorities",{}):
            broad=family_evidence.setdefault(parent,Counter())
            broad[row["rating"]]+=1
            if row["rating"]=="Sehr relevant":pos[parent]+=1
            if row["rating"]=="Nicht relevant" and "topic_dislike" in reason_labels_for_row:neg[parent]+=1
        for dimension in reason_labels_for_row:
            if dimension=="topic_dislike":continue
            style_by_topic.setdefault(topic,Counter())[dimension]+=1
    out["topic_evidence"]={t:{"positive":v["Sehr relevant"],"neutral":v["Teilweise relevant"],
                               "negative":v["Nicht relevant"],"total":sum(v.values())}
                           for t,v in sorted(exact_evidence.items())}
    out["topic_family_evidence"]={t:dict(v) for t,v in sorted(family_evidence.items())}
    deltas={}
    for t in set(pos)|set(neg):
        observations=exact_evidence.get(t) or family_evidence.get(t) or {}
        n=sum(observations.values())
        is_family=t in family_evidence and t not in exact_evidence
        threshold=3 if is_family else 2
        if n<threshold:
            deltas[t]=0;continue
        net=pos[t]-neg[t]
        deltas[t]=max(-2,min(2,(net//2 if net>=2 else
                -((-net)//2) if net<=-2 else 0)))
    out["feedback_topic_deltas"]=deltas
    # Global style signals and narrower topical style effects are independent
    # and require repeated EXPLICIT criticism, never negative vote alone.
    scoped={k:v for k,v in articles.items()
            if v.get("section","Vertiefungen")=="Vertiefungen"}
    out["style_preference_signals"]=style_signals(scoped)
    out["topic_style_signals"]={
       topic:{"novelty":min(2,values["already_known"]//2),
              "analysis":min(2,values["too_shallow"]//2),
              "broader_context":min(2,values["too_niche"]//2),
              "perspectives":min(2,values["one_sided"]//2)}
       for topic,values in style_by_topic.items()
       if any(value>=2 for value in values.values())}
    out["feedback_dimensions"]=feedback_dimensions(articles)
    out["editorial_review_queue"]=[
      {"type":"explicit_reader_request",**req,"status":"pending_editorial_review"}
      for req in out["explicit_reader_requests"][-20:]
    ]
    for subject,votes in sorted(exact_evidence.items()):
        if votes["Sehr relevant"] and votes["Nicht relevant"] and sum(votes.values())>=3:
            out["editorial_review_queue"].append({
                "type":"conflicting_topic_feedback","topic":subject,
                "positive":votes["Sehr relevant"],"negative":votes["Nicht relevant"],
                "neutral":votes["Teilweise relevant"],
                "status":"pending_editorial_review",
                "note":"Review which articles, quality and novelty differ; never override an explicit user rule."})
    for aid,row in sorted(articles.items(), key=lambda entry:entry[1].get("updated_at","")):
        labels=reason_labels(row.get("reason",""),row.get("rating"))
        if "more_of_this" in labels or ("topic_dislike" in labels and
            row.get("rating")!="Nicht relevant"):
            out["editorial_review_queue"].append({
                "type":"explicit_article_preference","date":row.get("date"),
                "article_id":aid,"topic":row.get("topic"),
                "section":row.get("section"),"reason":row.get("reason"),
                "status":"pending_editorial_review"})
    out["editorial_review_queue"]=out["editorial_review_queue"][-30:]
    out["feedback_metrics"]=editorial_feedback_metrics(out)
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
            for x in numeric_facts(sentence)-numeric_facts(excerpt):
                warnings.append({"id":key,"code":"NUMBER_MISMATCH","number":x})
            for month in set(MONTHS.findall(sentence.casefold()))-set(MONTHS.findall(excerpt.casefold())):
                warnings.append({"id":key,"code":"DATE_UNCONFIRMED","month":month})
            actors={v for v in PERSON.findall(sentence) if v not in excerpt}
            acronyms={v for v in ACRONYM.findall(sentence) if v not in excerpt}
            for actor in sorted(actors|acronyms):
                warnings.append({"id":key,"code":"ACTOR_UNCONFIRMED","actor":actor[:80]})
            for x in QUOTE.findall(sentence):
                if x not in excerpt:warnings.append({"id":key,"code":"QUOTE_MISMATCH","quote":x[:90]})
            if CAUSE.search(sentence) and not claim.get("causality_verified",False):
                warnings.append({"id":key,"code":"CAUSALITY_UNCONFIRMED","claim":sentence[:90]})
            if level=="headline" and len(sentence.split())>30:
                warnings.append({"id":key,"code":"HEADLINE_ONLY_OVERREACH"})
    return {"status":"warn" if warnings else "pass","warning_count":len(warnings),
            "claims_checked":checked,"warnings":warnings,
            "note":"Mechanical guard only; editorial semantic check remains obligatory"}

def validate_edition(ed,dossier=None,require_dossier=False):
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
            errors.extend(validate_article_metadata(row))
            if section=="articles" and not row.get("topic"):errors.append("missing topic")
            if section=="headlines" and row.get("region") not in ("Österreich","International"):
                errors.append("missing region")
    if ed.get("preview") is False:
        facts=ed.get("fact_audit",{})
        from scripts.morgenzeitung_v3_release import check_public_receipt, check_private_receipt
        errors.extend(check_private_receipt(ed,dossier) if dossier is not None
                      else check_public_receipt(ed))
        if require_dossier and dossier is None:
            errors.append("private dossier required for release")
        if not isinstance(ed.get("selection_audit",{}).get("feedback_applied"),bool):
            errors.append("missing selection audit")
    return errors

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["verify","rank","facts","compare","learn","quality"])
    for a in ("edition","dossier","candidates","profile","before","issues","topic-map"):p.add_argument("--"+a)
    p.add_argument("--new-feedback",action="store_true")
    p.add_argument("--benchmark-edition",help="Optional real published V1 reference JSON; read-only")
    p.add_argument("--section",choices=["Vertiefungen","Heute wichtig"],default="Vertiefungen")
    p.add_argument("--limit",type=int)
    p.add_argument("--history-dir",help="V3 data directory with index and historical editions")
    p.add_argument("--as-of-date",help="YYYY-MM-DD; required if --history-dir used")
    p.add_argument("--require-dossier",action="store_true",
                   help="Require actual private evidence before approving release")
    a=p.parse_args()
    def read(path):
        if not path:raise ValueError("required path missing")
        with open(path,encoding="utf-8") as f:return json.load(f)
    if a.action=="verify":
        out={"errors":validate_edition(read(a.edition),
            read(a.dossier) if a.dossier else None,a.require_dossier)}
    elif a.action=="rank":
        if a.history_dir and not a.as_of_date: p.error("--as-of-date required with --history-dir")
        out=select(read(a.candidates),read(a.profile),limit=a.limit,section=a.section,
                   previous_editions=load_edition_history(a.history_dir) if a.history_dir else (),
                   edition_date=a.as_of_date)
    elif a.action=="quality":
        if a.history_dir and not a.as_of_date: p.error("--as-of-date required with --history-dir")
        pool=read(a.candidates)
        profile=read(a.profile)
        history=load_edition_history(a.history_dir) if a.history_dir else []
        selected=select(pool,profile,limit=a.limit,section=a.section,
                        previous_editions=history,edition_date=a.as_of_date)
        out=editorial_mix_report(pool,selected,section=a.section)
        out["calibration"]=calibration_review(pool,section=a.section)
        if a.section=="Vertiefungen":
            out["depth_review"]=editorial_depth_review(pool,selected)
        out["omitted_candidate_review"]=missed_candidate_review(
            pool,selected,profile,section=a.section,
            previous_editions=history,edition_date=a.as_of_date)
        if a.edition:
            current=read(a.edition)
            out["whole_edition_feedback"]=edition_feedback_review(current,profile)
            out["v1_editorial_quality_benchmark"]=v1_comparison(
                current, read(a.benchmark_edition) if a.benchmark_edition else None)
        if a.section=="Vertiefungen":
            out["optional_reader_comparison_candidates"]=reader_comparison_candidates(
                pool,selected,score,profile,section=a.section)
        if a.before:
            out["rating_calibration"]=calibration_review_from_feedback(
                pool,read(a.before),profile,score,section=a.section)
        if history:
            out["past_edition_feedback"]=edition_series_review(history,profile)
        out["private_only"]=True
        out["feedback_inferred_from_omissions"]=False
    elif a.action=="facts":out=evidence_guard(read(a.edition),read(a.dossier))
    elif a.action=="compare":
        if a.history_dir and not a.as_of_date: p.error("--as-of-date required with --history-dir")
        out=compare_learning(read(a.candidates),read(a.before),read(a.profile),
                             a.new_feedback,limit=a.limit,section=a.section,
                             previous_editions=load_edition_history(a.history_dir) if a.history_dir else (),
                             edition_date=a.as_of_date)
    else:
        out,changed=ingest_feedback(read(a.profile),read(a.issues),read(a.topic_map))
        out["_changed_issue_ids"]=changed
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if (a.action=="verify" and out["errors"]) or (a.action=="facts" and out["status"]=="warn"):
        raise SystemExit(2)

if __name__=="__main__":main()
