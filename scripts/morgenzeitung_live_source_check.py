"""Conservative live source and publication-date checks.

A paywall response is evidence of a reachable publisher, not article verification.
Never follow HTTP redirects automatically (avoid redirect-based SSRF).
"""
import argparse
import datetime as dt
import json
import urllib.error
import urllib.request
from scripts.morgenzeitung_source_evidence import validate_source_url


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check_date(published_at, edition_date, max_age_hours=72):
    if not isinstance(published_at, str):
        raise ValueError("Missing source publication timestamp")
    try:
        stamp = dt.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        edition = dt.date.fromisoformat(edition_date)
    except ValueError as exc:
        raise ValueError("Invalid source or edition date") from exc
    if stamp.tzinfo is None:
        raise ValueError("Publication timestamp needs timezone")
    edition_end = dt.datetime.combine(edition + dt.timedelta(days=1), dt.time.min,
                                      tzinfo=dt.timezone.utc)
    if not (edition_end - dt.timedelta(hours=max_age_hours)
            <= stamp.astimezone(dt.timezone.utc) <= edition_end):
        raise ValueError("Publication date outside edition review window")
    return stamp.isoformat()


def check_http(url, opener=None):
    validate_source_url(url)
    opener = opener or urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "MorgenzeitungSourceCheck/1.0",
                                              "Accept": "text/html,application/xhtml+xml"},
                                 method="HEAD")
    try:
        with opener.open(req, timeout=8) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError("Source network check inconclusive") from exc
    if status in (401, 402, 403):
        return {"status": status, "reachable": True, "paywall_or_access_restricted": True}
    if 200 <= status < 300:
        return {"status": status, "reachable": True, "paywall_or_access_restricted": False}
    raise ValueError("Source URL not confirmed reachable (HTTP " + str(status) + ")")


def check_candidates(candidates, edition_date, opener=None):
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Candidates required")
    results = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Invalid candidate")
        stamp = check_date(candidate.get("published_at"), edition_date)
        response = check_http(candidate.get("source_url"), opener=opener)
        results.append({"id": candidate.get("id"), "published_at": stamp,
                        "http_status": response["status"],
                        "paywall_or_access_restricted": response["paywall_or_access_restricted"]})
    return {"live_source_checks_passed": True, "checked": results,
            "limitation": "HTTP status and declared publication time do not verify article body or independent timestamp."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidates", required=True)
    p.add_argument("--date", required=True)
    args = p.parse_args()
    with open(args.candidates, encoding="utf-8") as file:
        pool = json.load(file)
    print(json.dumps(check_candidates(pool, args.date), ensure_ascii=False))


if __name__ == "__main__":
    main()
