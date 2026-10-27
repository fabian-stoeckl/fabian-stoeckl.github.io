"""Read-only, bounded live GitHub-runner smoke test of pinned FIRST-PARTY feeds.

This smoke must NOT claim a source is verified unless the publisher's own
feed actually responded with valid RSS/Atom. No candidate is invented.
Network restrictions are reported per publisher as ACCESS_BLOCKED, never
treated as a failure of a verified original or a reason to drop a publisher.
"""
import argparse
import json
import urllib.request
from scripts.morgenzeitung_official_feeds import FEEDS, NoRedirect, _bounded_feed, _items

def run():
    opener = urllib.request.build_opener(NoRedirect)
    results=[]
    for source, (urls, hosts) in FEEDS.items():
        attempts=[]
        status="ACCESS_BLOCKED"
        count=0
        worked=None
        for url in urls:
            try:
                root=_bounded_feed(url, opener)
                count=sum(1 for _ in _items(root))
                status="FEED_READABLE" if count else "EMPTY_FEED"
                worked=url
                attempts.append({"url":url,"status":status,"items":count})
                if count:
                    break
            except (ValueError, OSError) as exc:
                attempts.append({"url":url, "status":"INCONCLUSIVE", "reason":str(exc)})
        results.append({"publisher":source,"status":status,"items":count,
                        "working_feed":worked,"attempts":attempts})
    return {"report_type":"real_publisher_first_party_feed_smoke",
            "claim_scope":"GitHub-runner feed XML reachability, not verified article/fulltext",
            "results":results,
            "reachable_publishers":sum(x["status"]=="FEED_READABLE" for x in results),
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
