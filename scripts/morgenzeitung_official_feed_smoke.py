"""Read-only, bounded live GitHub-runner smoke test of pinned FIRST-PARTY feeds.

This smoke must NOT claim a source is verified unless the publisher's own
feed actually responded with valid RSS/Atom. No candidate is invented.
Network restrictions are reported per publisher as ACCESS_BLOCKED, never
treated as a failure of a verified original or a reason to drop a publisher.
"""
import argparse
import json
import urllib.request
from urllib.parse import urlsplit,parse_qsl
from scripts.morgenzeitung_official_feeds import FEEDS, NoRedirect, _bounded_feed, _items, _stamp, verify_official_feed

def run():
    opener = urllib.request.build_opener(NoRedirect)
    results=[]
    for source, (urls, hosts) in FEEDS.items():
        attempts=[]
        status="ACCESS_BLOCKED"
        count=0
        worked=None
        identity_status="NOT_CHECKED"
        sample_formats=[]
        for url in urls:
            try:
                root=_bounded_feed(url, opener)
                items=list(_items(root))
                count=len(items)
                status="FEED_READABLE" if count else "EMPTY_FEED"
                worked=url
                # Only sanitized protocol/field-shape diagnostics.
                for _title,_link,_date in items[:2]:
                    _parsed=urlsplit(_link)
                    sample_formats.append({
                        "scheme":_parsed.scheme,
                        "host":_parsed.hostname,
                        "query_keys":[x[0] for x in parse_qsl(_parsed.query)],
                        "has_fragment":bool(_parsed.fragment),
                        "time_repr":repr(_date)[:105],
                        "link_is_html":_parsed.path.endswith(".html"),
                    })
                # Live match of actual publisher data against the production
                # identity verifier. This checks the real RSS schema and exact
                # article URLs/timestamps, never the article's full text.
                errors=[]
                for title, article_url, published_at in items[:5]:
                    try:
                        stamp=_stamp(published_at).isoformat()
                        evidence=verify_official_feed({
                            "source":source,"source_url":article_url,
                            "title":title,"published_at":stamp},opener=opener)
                        if evidence["publisher_feed_verified"]:
                            identity_status="LIVE_IDENTITY_MATCH"
                            break
                    except (ValueError, TypeError) as exc:
                        errors.append(str(exc))
                if identity_status!="LIVE_IDENTITY_MATCH":
                    identity_status="NO_SAMPLE_MATCH"
                    attempts.append({"identity_errors":errors[:2]})
                attempts.append({"url":url,"status":status,"items":count})
                if count:
                    break
            except (ValueError, OSError) as exc:
                attempts.append({"url":url, "status":"INCONCLUSIVE", "reason":str(exc)})
        results.append({"publisher":source,"status":status,"items":count,
                        "identity_status":identity_status,
                        "sample_formats":sample_formats,
                        "working_feed":worked,"attempts":attempts})
    return {"report_type":"real_publisher_first_party_feed_smoke",
            "claim_scope":"GitHub-runner feed XML reachability, not verified article/fulltext",
            "results":results,
            "reachable_publishers":sum(x["status"]=="FEED_READABLE" for x in results),
            "live_identity_verified_publishers":sum(x["identity_status"]=="LIVE_IDENTITY_MATCH" for x in results),
            "tested_publishers":len(results)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    result=run()
    with open(args.output,"w",encoding="utf-8") as out:
        json.dump(result,out,ensure_ascii=False,indent=2)
        out.write("\n")
    print(json.dumps(result,ensure_ascii=False))
    # Diagnostic only: access restriction may legitimately differ by runner.


if __name__=="__main__":
    main()
