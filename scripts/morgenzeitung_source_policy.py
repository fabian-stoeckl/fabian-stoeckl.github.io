"""Fail-closed source verification policy with bounded publisher-access uncertainty.

A live source outage must never be misrepresented as positive verification.
Only a specific, expected failure of a rolling publisher feed may be recorded
as INCONCLUSIVE after validating an immutable originally researched candidate.
Other errors (404, metadata contradictions, source swaps, redirects) remain fatal.

Prepublication checks are about faithful reproduction of archived editorial
selection; independent publisher checks are reported separately, never forged.
"""
from urllib.parse import urlsplit
from scripts.morgenzeitung_source_evidence import validate_source_url

STANDARD_HOSTS = frozenset(("derstandard.at", "www.derstandard.at",
                            "derstandard.de", "www.derstandard.de"))
ROLLING_FEED_MISSING = "Article identity not independently present in publisher RSS"
ROLLING_FEED_UNREACHABLE = "Publisher RSS independently unreachable"


def classify_inconclusive(candidate, exc):
    """Return an explicit uncertainty record only for an already-source-checked consent wall.

    The Der Standard article endpoint must already have produced a first-party
    consent redirect, followed by this publisher-RSS error. Never infer 200.
    A missing result from the *current* RSS feed is not evidence that an older
    article does not exist. The published item can remain with a bounded,
    audited caveat; a genuine contradiction must still stop publication.
    """
    reason = str(exc)
    if not any(s in reason for s in (ROLLING_FEED_MISSING, ROLLING_FEED_UNREACHABLE)):
        return None
    if not isinstance(candidate, dict) or candidate.get("verified") is not True:
        return None
    if candidate.get("source") != "Der Standard" or not candidate.get("title"):
        return None
    validate_source_url(candidate.get("source_url"))
    source = urlsplit(candidate["source_url"])
    if source.hostname not in STANDARD_HOSTS or not source.path.startswith("/story/"):
        return None
    return {
        "id": candidate.get("id"),
        "source_verification": "INCONCLUSIVE",
        "original_article_http_verified": False,
        "publisher_feed_verified": False,
        "publisher_access_restricted": True,
        "reason": "rolling_publisher_feed_unavailable",
        "original_url": candidate["source_url"],
        "limitation": ("Publisher's consent page and rolling RSS did not independently "
                       "verify the article. This is NOT a publisher-source PASS."),
    }


def check_inconclusive_budget(records, *, limit=2):
    """Let minor access uncertainty be visible; reject excessive unverifiable sources."""
    failures = [r for r in records if r.get("source_verification") == "INCONCLUSIVE"]
    if len(failures) > limit:
        raise ValueError(
            "Too many independently unverified sources: "
            + str(len(failures)) + " > " + str(limit))
    return failures
