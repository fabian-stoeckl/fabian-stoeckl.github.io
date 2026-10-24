"""Conservative live source and publication-date checks.

A paywall response is NOT proof that an article exists.
Never follow HTTP redirects automatically (avoid redirect-based SSRF).
"""
import argparse
import datetime as dt
import json
import time
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


def check_http(url, opener=None, *, retries=2, sleep=time.sleep):
    validate_source_url(url)
    opener = opener or urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "MorgenzeitungSourceCheck/1.0",
                                              "Accept": "text/html,application/xhtml+xml"},
                                 method="HEAD")
    for attempt in range(retries + 1):
        try:
            with opener.open(req, timeout=8) as response:
                status = response.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == retries:
                raise ValueError("Source network check inconclusive after retries") from exc
            sleep(attempt + 1)
            continue
        if status in (429, 500, 502, 503, 504) and attempt < retries:
            sleep(attempt + 1)
            continue
        break
    if status in (401, 402, 403):
        raise ValueError("Publisher access restricted: article existence unverified (HTTP " + str(status) + ")")
    if status == 200:
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
            "limitation": "HEAD 200 and a declared publication time do not verify article body or independent timestamp. Access-restricted sources are rejected until independently verified."}


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
