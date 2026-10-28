"""Small editorial policies retained from the original Morgenzeitung.

This module intentionally contains no networking, publisher URL probes or
publication gates. Reader feedback is data, never an instruction to execute.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

NEGATIVE = "Nicht relevant"
POSITIVE = "Sehr relevant"
NEUTRAL = "Teilweise relevant"
RATINGS = {NEGATIVE, POSITIVE, NEUTRAL}

# Each reason has a distinct meaning. A dislike of presentation or repetition
# must never be generalized to disliking the subject itself.
REASON_PATTERNS = {
    "already_known": ("schon bekannt", "kannte ich schon", "nichts neues", "bereits bekannt"),
    "too_shallow": ("zu oberflächlich", "wenig tiefgang", "mehr analyse", "zu wenig analyse"),
    "too_niche": ("zu speziell", "randbereich", "randthema", "juristische details"),
    "one_sided": ("einseitig", "gegenposition", "andere perspektiv"),
    "more_of_this": ("mehr davon", "mehr von solchen", "mehr zu diesem thema"),
    "topic_dislike": ("thema interessiert mich nicht", "thema nicht interessant",
                      "weniger über", "grundsätzlich uninteressant"),
}


def reason_labels(reason, rating):
    """Label explicit criticism, never guess a topic from free text alone."""
    # Reasons are meaningful at ALL rating levels: a partly relevant article
    # may fit the topic perfectly while lacking depth or new information.
    if rating not in RATINGS or not isinstance(reason, str):
        return ()
    text = " ".join(reason.casefold().split())
    return tuple(label for label, fragments in REASON_PATTERNS.items()
                 if any(fragment in text for fragment in fragments))


def style_signals(article_feedback):
    """Two matching independent observations before adjusting broad styling."""
    counts = Counter()
    for row in article_feedback.values():
        if not isinstance(row, dict):
            continue
        labels = reason_labels(row.get("reason"), row.get("rating"))
        for label in labels:
            if label not in ("topic_dislike", "more_of_this"):
                counts[label] += 1
    return {
        "novelty": min(2, counts["already_known"] // 2),
        # Editorial planning advice only: must NOT be used to favor full-text access.
        "analysis": min(2, counts["too_shallow"] // 2),
        "broader_context": min(2, counts["too_niche"] // 2),
        "perspectives": min(2, counts["one_sided"] // 2),
    }



def feedback_dimensions(article_feedback):
    """Private descriptive evidence: separate subject interest from article quality.

    A label is an explicit reader statement, never inferred from access, length,
    the publication, an unclicked article, or a rating without a reason.
    """
    by_dimension = Counter()
    samples = {}
    for article_id, row in article_feedback.items():
        if not isinstance(row, dict):
            continue
        for dimension in reason_labels(row.get("reason"), row.get("rating")):
            by_dimension[dimension] += 1
            samples.setdefault(dimension, []).append(article_id)
    return {"counts": dict(by_dimension),
            "examples": {k: v[:5] for k, v in samples.items()},
            "status": "explicit_reader_reasons_only"}


def editorial_depth_review(candidates, selected):
    """An editorial quality prompt, not a length/HTTP/full-text gate."""
    gaps = []
    for article in selected:
        if not isinstance(article, dict):
            continue
        analysis = article.get("analysis_value")
        context = article.get("context_value")
        if analysis is None or context is None:
            gaps.append({"id": article.get("id"), "issue": "missing_analytical_quality_assessment",
                         "missing": [k for k in ("analysis_value", "context_value")
                                     if article.get(k) is None]})
        # Summary length by itself never proves insight, but very short
        # descriptive snippets should prompt a check for actual mechanisms.
        summary = str(article.get("summary") or "")
        if len(summary.split()) < 20:
            gaps.append({"id": article.get("id"), "issue": "check_incremental_insight",
                         "note": "Show an evidenced mechanism, figure, trade-off or consequence if available; never invent detail."})
    return {"review": gaps, "release_blocked": False,
            "note": "Evidence quality and substance, not word count or full-text availability, determine selection."}


def editorial_feedback_metrics(profile, min_votes=5):
    """Descriptive real V3 vote trend, NEVER claims a causal learning improvement."""
    snapshots = profile.get("feedback_by_issue") or {}
    latest = {}
    for issue_id, issue in snapshots.items():
        if not isinstance(issue, dict):
            continue
        date, updated = issue.get("date"), issue.get("updated_at", "")
        if not isinstance(date, str):
            continue
        for row in issue.get("ratings", []):
            if not isinstance(row, dict) or row.get("rating") not in RATINGS:
                continue
            key = (date, row.get("id"))
            if not isinstance(key[1], str):
                continue
            if key not in latest or (updated, str(issue_id)) > latest[key][0]:
                latest[key] = ((updated, str(issue_id)), row["rating"])
    by_date = {}
    for (date, _), (_, rating) in latest.items():
        by_date.setdefault(date, Counter())[rating] += 1
    days = []
    for date in sorted(by_date):
        row = by_date[date]
        n = sum(row.values())
        days.append({"date": date, "ratings": n,
                     "very_relevant": row[POSITIVE],
                     "partly_relevant": row[NEUTRAL],
                     "not_relevant": row[NEGATIVE],
                     "very_relevant_share": round(row[POSITIVE] / n, 4)})
    sufficient = [x for x in days if x["ratings"] >= min_votes]
    return {
        "days": days,
        "trend_status": "descriptive_only" if len(sufficient) >= 2 else "insufficient_feedback",
        "latest_two_comparable_dates": [x["date"] for x in sufficient[-2:]],
        "very_relevant_share_change": (
            round(sufficient[-1]["very_relevant_share"] - sufficient[-2]["very_relevant_share"], 4)
            if len(sufficient) >= 2 else None),
        "causal_quality_improvement_proven": False,
    }


def research_window(last_successful, started_at):
    """Cover elapsed time since previous real editorial cutoff, including missed days.

    A preview is never evidence of completed research. Timestamps must be
    timezone-aware; no network call or article freshness gate is performed.
    """
    def aware(value):
        parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Research timestamps need a timezone")
        return parsed.astimezone(timezone.utc)
    now=aware(started_at)
    reference=None
    if isinstance(last_successful,dict) and last_successful.get("preview") is False:
        reference=last_successful.get("window_end") or last_successful.get("researched_at")
    start=aware(reference) if reference else now-timedelta(hours=24)
    if start>now:
        raise ValueError("Previous coverage cannot end after new research starts")
    return {
        "window_start":start.isoformat().replace("+00:00","Z"),
        "window_end":now.isoformat().replace("+00:00","Z"),
        "extended_for_gap":(now-start)>timedelta(hours=24),
        "reference":"last_independent_research" if reference else "initial_24h",
    }


def editorial_mix_report(candidates, selected, section="Vertiefungen"):
    """Non-blocking prompt for broader editorial search, not a quota or gate."""
    if not isinstance(candidates,list) or not isinstance(selected,list):
        raise ValueError("expected candidate and selected lists")
    def names(rows,key):
        return Counter(str(row.get(key,"")).strip() for row in rows
                       if isinstance(row,dict) and row.get(key))
    sources=names(selected,"source")
    candidate_sources=names(candidates,"source")
    topics=names(selected,"topic")
    genres=names(selected,"article_type")
    if not genres:
        genres=names(selected,"kind")
    recommendations=[]
    n=len(selected)
    if n>=5 and sources and sources.most_common(1)[0][1]/n >.55 and len(candidate_sources)>=3:
        recommendations.append("Publisher concentration: search additional independent reporting; do not enforce quotas")
    if n>=5 and section=="Vertiefungen":
        if topics and topics.most_common(1)[0][1]/n >.65 and len(names(candidates,"topic"))>=3:
            recommendations.append("Thematic repetition: look for relevant original mechanisms in other subjects")
        if genres and genres.most_common(1)[0][1]/n >.65 and len(names(candidates,"article_type") or names(candidates,"kind"))>=3:
            recommendations.append("Similar article types: consider investigation, explanation and analysis mix")
    debates={}
    for row in selected:
        if not isinstance(row,dict):continue
        debate=row.get("debate_id")
        stance=row.get("viewpoint")
        if debate and stance in ("support","oppose","mixed"):
            debates.setdefault(debate,set()).add(stance)
    if any(len(views)==1 and "mixed" not in views for views in debates.values()):
        recommendations.append("Contested topic: search credible counter-perspectives where available; no forced balance")
    return {
        "section":section,"candidate_count":len(candidates),
        "selected_count":len(selected),
        "candidate_publishers":len(candidate_sources),
        "selected_publishers":len(sources),
        "selected_source_distribution":dict(sources),
        "selected_article_types":dict(genres),
        "recommendations":recommendations,
        "release_blocked":False,
        "note":"Editorial warnings only; do not reward or penalize paywalls, publisher accessibility, or URL response codes.",
    }


# Stable anchors for human editorial assessments. They are intentionally
# qualitative: code cannot infer analysis quality from the amount of full text.
EDITORIAL_ANCHORS = {
    "fit": "0 no useful new insight; 2 peripheral; 3 concrete useful fact; 4 explains relevant mechanisms or trade-offs; 5 exceptional incremental insight",
    "novelty": "0 repeated without update; 2 familiar angle; 3 fresh factual development; 4 new interpretation or substantive update; 5 major genuinely new finding",
    "impact": "0 negligible; 2 limited sector effect; 3 material consequence; 4 broad consequences; 5 systemic or exceptionally consequential",
    "perspective": "0 no useful angle; 2 ordinary framing; 3 independent useful view; 4 substantive additional context; 5 rare well-grounded perspective",
    "analysis_value": "0 unsupported/none; 2 descriptive; 3 explains a mechanism; 4 substantial evidence-based analysis; 5 unusually strong mechanism and alternatives",
    "context_value": "0 isolated detail; 2 limited context; 3 explains relevance; 4 connects to broader implications; 5 exceptional structural context",
}


def calibration_review(candidates, section="Vertiefungen"):
    """Private, non-blocking consistency questions for HUMAN scores.

    Never derives scoring from HTTP access, paywall, length or publisher brand.
    Source averages are review hints, not a source bonus or penalty.
    """
    if section not in ("Vertiefungen", "Heute wichtig"):
        raise ValueError("unknown section")
    mandatory=("novelty","impact","perspective") if section=="Heute wichtig" else (
        "fit","novelty","impact","perspective")
    per_source={}
    absent=Counter()
    invalid=Counter()
    valid=Counter()
    for row in candidates:
        if not isinstance(row,dict):continue
        source=row.get("source")
        for key in mandatory:
            value=row.get(key)
            if value is None:
                absent[key]+=1
            elif type(value) not in (int,float) or not 0<=value<=5:
                invalid[key]+=1
            else:
                valid[key]+=1
        if isinstance(source,str) and source and type(row.get("fit")) in (int,float):
            if 0<=row["fit"]<=5:
                per_source.setdefault(source,[]).append(row["fit"])
    sufficient={k:round(sum(v)/len(v),2) for k,v in per_source.items() if len(v)>=3}
    potential=[]
    if len(sufficient)>=2 and max(sufficient.values())-min(sufficient.values())>=2:
        potential.append("Check consistent use of incremental-insight anchors across publishers, without adjusting scores by source.")
    if any(absent.values()) or any(invalid.values()):
        potential.append("Assess missing or invalid scoring fields from comparable publisher titles and teasers; never fabricate a value to fill a quota.")
    return {"section":section,"candidate_count":len(candidates),
            "rubric":{key:EDITORIAL_ANCHORS[key] for key in mandatory},
            "optional_rubric":{key:EDITORIAL_ANCHORS[key] for key in ("analysis_value","context_value")},
            "present":dict(valid),"missing":dict(absent),"invalid":dict(invalid),
            "source_fit_means_for_review_only":sufficient,
            "review_notes":potential,"release_blocked":False,
            "no_access_based_adjustments":True}


def edition_feedback_review(edition,profile,min_votes=5):
    """Actual ratings for ONE published V3 edition, not delivery or click metrics.

    Aggregate an entire newspaper's reader response, not only isolated stories.
    Do not confuse non-response with dislike, or statistical trend with causality.
    """
    if not isinstance(edition,dict) or not isinstance(profile,dict):
        raise ValueError("edition and profile required")
    date=edition.get("date")
    items=[x for section in ("articles","headlines") for x in edition.get(section,[])
           if isinstance(x,dict) and isinstance(x.get("id"),str)]
    by_id={x["id"]:x for x in items}
    current={}
    for issue_id,record in (profile.get("feedback_by_issue") or {}).items():
        if not isinstance(record,dict) or record.get("date")!=date:continue
        updated=record.get("updated_at") or ""
        for vote in record.get("ratings",[]):
            if not isinstance(vote,dict) or vote.get("rating") not in RATINGS:continue
            aid=vote.get("id")
            if aid not in by_id:continue
            key=(str(updated),str(issue_id))
            if aid not in current or key>=current[aid][0]:
                current[aid]=(key,vote)
    ratings=Counter(v["rating"] for _,v in current.values())
    topic_counts=Counter(by_id[aid].get("topic") for aid in current
                         if by_id[aid].get("topic"))
    all_topics=Counter(x.get("topic") for x in items if x.get("topic"))
    source_counts=Counter(x.get("source") for x in items if x.get("source"))
    n=len(current)
    enough=(edition.get("preview") is False and
            n>=min_votes and n>=max(1,int(len(by_id)*.25)))
    review_hints=[]
    if enough:
        for topic,count in topic_counts.items():
            if count>=3:
                misses=sum(1 for aid,(_,v) in current.items()
                           if by_id[aid].get("topic")==topic and
                           v["rating"]==NEGATIVE)
                if misses>=2:
                    review_hints.append("Review story choice, novelty and depth within topic: "+str(topic))
    return {
        "date":date,"preview":edition.get("preview"),
        "published":len(by_id),"rated":n,"unrated":max(0,len(by_id)-n),
        "ratings":{key:ratings[key] for key in (POSITIVE,NEUTRAL,NEGATIVE)},
        "very_relevant_share_of_rated":round(ratings[POSITIVE]/n,4) if n else None,
        "rated_fraction":round(n/max(1,len(by_id)),4),
        "topics_published":dict(all_topics),
        "publishers_published":dict(source_counts),
        "topics_with_explicit_feedback":dict(topic_counts),
        "assessment":"descriptive" if enough else "insufficient_real_feedback",
        "editorial_hints":review_hints,
        "learning_applied":False,
        "causal_improvement_proven":False,
        "note":"Only rated published articles count. Unrated, unselected, unread and preview records are not negative signals.",
    }


def edition_series_review(editions,profile):
    """Compare whole-edition feedback cautiously, never auto-edit user interests."""
    reports=[edition_feedback_review(e,profile) for e in editions
             if isinstance(e,dict) and e.get("preview") is False]
    reports.sort(key=lambda r:r.get("date") or "")
    comparable=[x for x in reports if x["assessment"]=="descriptive"]
    change=None
    if len(comparable)>=2:
        change=round(comparable[-1]["very_relevant_share_of_rated"]-
                     comparable[-2]["very_relevant_share_of_rated"],4)
    return {"editions":reports[-14:],
            "comparable_edition_dates":[x["date"] for x in comparable[-2:]],
            "change_in_positive_share_among_rated":change,
            "trend":"descriptive_only" if change is not None else "insufficient_real_feedback",
            "causal_improvement_proven":False,
            "learning_applied":False}
