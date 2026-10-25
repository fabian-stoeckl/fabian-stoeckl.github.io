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


def check_date(published_at, edition_date, max_age_hours=72, *, as_of=None):
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
    now = as_of if as_of is not None else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Verification time needs timezone")
    latest = min(edition_end, now.astimezone(dt.timezone.utc) + dt.timedelta(minutes=5))
    if not (edition_end - dt.timedelta(hours=max_age_hours)
            <= stamp.astimezone(dt.timezone.utc) <= latest):
        raise ValueError("Publication date outside edition review window")
    return stamp.isoformat()


def _same_article_publisher_redirect(original_url, location):
    """Permit only publisher-controlled canonical redirects to the IDENTICAL article path.

    In particular, Der Standard uses .de and .at frontends with the same story
    path. Never auto-follow to login, tracking, another article, or another host.
    """
    from urllib.parse import urljoin, urlsplit
    if not location or not isinstance(location, str):
        raise ValueError("Publisher redirect lacks a Location")
    target = urljoin(original_url, location)
    validate_source_url(target)
    before, after = urlsplit(original_url), urlsplit(target)
    a, b = before.hostname.lower(), after.hostname.lower()
    standard = {'www.derstandard.de', 'www.derstandard.at',
                'derstandard.de', 'derstandard.at'}
    same_publisher = (a == b or (a in standard and b in standard))
    if (not same_publisher or before.path != after.path
            or before.query != after.query or before.port != after.port):
        raise ValueError("Publisher redirect changes host or article identity")
    return target


def check_http(url, opener=None, *, retries=2, sleep=time.sleep):
    validate_source_url(url)
    opener = opener or urllib.request.build_opener(NoRedirect)
    current = url
    method = "HEAD"
    retries_used = 0
    redirects = 0
    while True:
        headers = {"User-Agent": "MorgenzeitungSourceCheck/1.0",
                   "Accept": "text/html,application/xhtml+xml"}
        if method == "GET":
            headers["Range"] = "bytes=0-0"
        req = urllib.request.Request(current, headers=headers, method=method)
        location = None
        try:
            with opener.open(req, timeout=8) as response:
                status = response.status
                location = response.headers.get('Location')
        except urllib.error.HTTPError as exc:
            status = exc.code
            location = exc.headers.get('Location') if exc.headers else None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if retries_used >= retries:
                raise ValueError("Source network check inconclusive after retries") from exc
            retries_used += 1
            sleep(retries_used)
            continue
        if status in (301, 302, 307, 308):
            if redirects >= 2:
                raise ValueError("Publisher redirect exceeds safe limit")
            current = _same_article_publisher_redirect(current, location)
            redirects += 1
            # Restart with HEAD at the validated SAME-ARTICLE target.
            method = "HEAD"
            continue
        if status in (401, 403, 405, 501) and method == "HEAD":
            # A HEAD error can be legitimate even when GET serves public HTML.
            # GET 401/403 remains a hard failure.
            method = "GET"
            continue
        if status in (429, 500, 502, 503, 504) and retries_used < retries:
            retries_used += 1
            sleep(retries_used)
            continue
        break
    if status in (401, 402, 403):
        raise ValueError("Publisher access restricted: article existence unverified (HTTP " + str(status) + ")")
    if status == 200 or (method == "GET" and status == 206):
        return {"status": status, "reachable": True, "paywall_or_access_restricted": False,
                "method": method, "verified_url": current,
                "redirects": redirects}
    raise ValueError("Source URL not confirmed reachable (HTTP " + str(status) + ")")


def check_candidates(candidates, edition_date, opener=None, *, publisher_dates=False):
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Candidates required")
    results = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Invalid candidate")
        stamp = check_date(candidate.get("published_at"), edition_date)
        try:
            response = check_http(candidate.get("source_url"), opener=opener)
        except ValueError as exc:
            raise ValueError("Source check failed for " + candidate["source_url"] + ": " + str(exc)) from exc
        record = {"id": candidate.get("id"), "published_at": stamp,
                  "http_status": response["status"],
                  "paywall_or_access_restricted": response["paywall_or_access_restricted"]}
        if publisher_dates:
            from scripts.morgenzeitung_publisher_date_evidence import fetch_publisher_metadata
            record["publisher_date_evidence"] = fetch_publisher_metadata(
                candidate["source_url"], stamp, opener=opener)
            if record["publisher_date_evidence"]["status"] in ("mismatch", "conflict"):
                raise ValueError("Publisher publication metadata contradict archived date")
        results.append(record)
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
