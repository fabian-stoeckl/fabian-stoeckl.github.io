"""Optional public metadata contract for V3 candidates and editions.

Old editions retain numeric novelty; the modern story also has a separate
novelty_score (0..5) and novelty_explanation (text).
Missing optional evidence is never an access or quality penalty.
"""
GENRES = frozenset({"analysis", "investigation", "report", "explainer",
                    "opinion", "interview", "feature"})
EVIDENCE_LEVELS = frozenset({"headline", "teaser", "read"})


def validate_article_metadata(article):
    """Explicitly typed optional fields, backwards compatible with old public JSON."""
    errors=[]
    if not isinstance(article, dict):
        return ["article is not an object"]
    number=article.get("novelty_score",article.get("novelty"))
    if number is not None and (
        isinstance(number,bool) or not isinstance(number,(int,float))
        or not 0<=number<=5
    ):
        errors.append("novelty score must be a number from 0 to 5")
    if (article.get("novelty_score") is not None and article.get("novelty") is not None
        and article["novelty_score"]!=article["novelty"]):
        errors.append("novelty and novelty_score conflict")
    for key in ("novelty_explanation","why_selected","event","update_evidence"):
        if key in article and article[key] is not None and (
            not isinstance(article[key],str) or len(article[key])>1500
        ):
            errors.append(key+" must be short descriptive text")
    if article.get("article_type") is not None and article["article_type"] not in GENRES:
        errors.append("unknown article_type")
    if article.get("evidence_level") is not None and article["evidence_level"] not in EVIDENCE_LEVELS:
        errors.append("unknown evidence_level")
    for key in ("analysis_value","context_value"):
        x=article.get(key)
        if x is not None and (isinstance(x,bool) or not isinstance(x,(int,float)) or not 0<=x<=5):
            errors.append(key+" must be a number from 0 to 5")
    return errors


def validate_candidate(article):
    errors=validate_article_metadata(article)
    if not isinstance(article,dict):
        return errors
    for key in ("id","url","title","source","fit","impact","perspective"):
        if article.get(key) is None:errors.append("missing candidate "+key)
    for key in ("fit","impact","perspective"):
        x=article.get(key)
        if x is not None and (isinstance(x,bool) or not isinstance(x,(int,float)) or not 0<=x<=5):
            errors.append(key+" must be a number from 0 to 5")
    return errors
