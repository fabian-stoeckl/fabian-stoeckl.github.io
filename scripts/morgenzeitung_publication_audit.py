"""Verify that a private editorial counterfactual matches a *live HTTPS* edition.

Do not publish private audits. This tool only proves that a documented
counterfactual selection was actually published, not that all journalism
or feedback processing was correct.
"""
import argparse
import json
import re
import urllib.request
from pathlib import Path

PUBLIC_BASE = "https://www.fabian-stoeckl.com/Privat/Pressespiegel/data/"

def verify(index, edition, audit, date):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("Invalid date")
    if date not in index.get("dates", []):
        raise ValueError("Edition not listed in live index")
    if edition.get("date") != date or edition.get("preview"):
        raise ValueError("Edition date mismatch or preview")
    published = [a.get("id") for a in edition.get("articles", [])]
    selected = audit.get("selected_ids", [])
    if not selected or len(selected) != len(set(selected)):
        raise ValueError("Missing or duplicate selected IDs")
    if published != selected:
        raise ValueError("Published article order/IDs differ from audited selection")
    if not audit.get("counterfactual_effect_verified"):
        return {"date": date, "publication_verified": True,
                "editorial_effect_verified": False, "changed_top_n_count": 0,
                "note": "Live edition matches audit, but feedback caused no documented selection change"}
    if not audit.get("newly_selected_ids") or audit.get("changed_top_n_count") != len(audit["newly_selected_ids"]):
        raise ValueError("Counterfactual change evidence incomplete")
    if not audit.get("effective_signals"):
        raise ValueError("No effective learning signals")
    return {"date": date, "publication_verified": True,
            "editorial_effect_verified": True,
            "changed_top_n_count": audit["changed_top_n_count"],
            "newly_selected_ids": audit["newly_selected_ids"],
            "note": "Live HTTPS article IDs match the documented learned selection; compare audit with genuine feedback provenance separately"}

def live_json(filename):
    request = urllib.request.Request(PUBLIC_BASE + filename,
        headers={"User-Agent": "Morgenzeitung-publication-learning-audit/1.0",
                 "Cache-Control": "no-cache"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.geturl().split("?", 1)[0] != PUBLIC_BASE + filename:
            raise ValueError("Unexpected HTTPS redirect")
        return json.load(response)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--private-selection-audit", required=True)
    parser.add_argument("--private-output", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        parser.error("Date must be YYYY-MM-DD")
    audit = json.loads(Path(args.private_selection_audit).read_text())
    result = verify(live_json("index.json"), live_json(args.date + ".json"), audit, args.date)
    Path(args.private_output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"publication_verified": result["publication_verified"],
                      "editorial_effect_verified": result["editorial_effect_verified"],
                      "changed_top_n_count": result["changed_top_n_count"]}))

if __name__ == "__main__":
    main()
