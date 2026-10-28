"""Morgenzeitung 3 release guard: private evidence at editorial time, public integrity receipt in CI.

No article network access and no individual URL tests. Public CI can verify a receipt
is bound to an edition, but cannot independently read the private evidence repository.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone

HEX64=re.compile(r"^[a-f0-9]{64}$")
RECEIPT_VERSION=3
LEGACY_RECEIPT_VERSION=2
# One audited edition predates the stronger complete-edition fingerprint.
LEGACY_LAST_DATE="2026-10-28"

def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def edition_hash(edition, version=RECEIPT_VERSION):
    """Versioned receipt hash; the modern version covers ALL public fields.

    Only fact_audit is excluded to avoid a circular self-reference.
    Edition 2026-10-28 keeps its original v2 historical fingerprint.
    """
    if version==LEGACY_RECEIPT_VERSION:
        fields=("id","url","source","title","summary","published_at")
        rows=[{k:entry.get(k) for k in fields}
              for entry in [*edition.get("articles",[]),*edition.get("headlines",[])]]
        payload={"date":edition.get("date"),"items":rows}
    elif version==RECEIPT_VERSION:
        payload={k:v for k,v in edition.items() if k!="fact_audit"}
    else:
        raise ValueError("Unsupported receipt format")
    return hashlib.sha256(canonical(payload)).hexdigest()


def evidence_hash(dossier):
    return hashlib.sha256(canonical(dossier)).hexdigest()

def private_review(edition,dossier,receipt_version=RECEIPT_VERSION):
    if receipt_version!=RECEIPT_VERSION and not (
        receipt_version==LEGACY_RECEIPT_VERSION
        and edition.get("date")<=LEGACY_LAST_DATE):
        raise ValueError("Historic receipt format not allowed for this issue")
    """Requires the actual private dossier, not a self-reported PASS string."""
    from scripts.morgenzeitung_v3_engine import evidence_guard
    report=evidence_guard(edition,dossier)
    if report["status"]!="pass" or report["warning_count"]:
        raise ValueError("Unresolved evidence warnings: "+json.dumps(report["warnings"],ensure_ascii=False))
    review=dossier.get("editorial_review",{})
    if review.get("approved") is not True or not review.get("reviewed_at"):
        raise ValueError("Human/agent editorial semantic review not documented in private dossier")
    try:
        reviewed=datetime.fromisoformat(review["reviewed_at"].replace("Z","+00:00"))
        if reviewed.tzinfo is None:
            raise ValueError("Review timestamp must contain timezone")
    except (ValueError,AttributeError,TypeError):
        raise ValueError("Invalid private review timestamp")
    return {
        "status":"pass","warning_count":0,
        "claims_checked":report["claims_checked"],
        "audit_version":receipt_version,
        "edition_sha256":edition_hash(edition, receipt_version),
        "dossier_sha256":evidence_hash(dossier),
        "reviewed_at":review["reviewed_at"],
        "review_method":"private_dossier_and_editorial_review",
    }

def check_public_receipt(edition):
    """Checks public integrity fields only; not evidence or independent semantic truth."""
    if edition.get("preview") is True: return []
    report=edition.get("fact_audit")
    count=len(edition.get("articles",[]))+len(edition.get("headlines",[]))
    if not isinstance(report,dict):return ["Missing fact audit"]
    errors=[]
    if report.get("status")!="pass" or report.get("warning_count")!=0:
        errors.append("Unresolved fact audit")
    version=report.get("audit_version")
    legacy=(version==LEGACY_RECEIPT_VERSION and isinstance(edition.get("date"),str)
            and edition["date"]<=LEGACY_LAST_DATE)
    if version!=RECEIPT_VERSION and not legacy:
        errors.append("Wrong fact audit version")
    else:
        if report.get("edition_sha256")!=edition_hash(edition,version):
            errors.append("Fact audit not bound to current edition")
    if not HEX64.fullmatch(str(report.get("dossier_sha256",""))):
        errors.append("Missing private evidence dossier fingerprint")
    if type(report.get("claims_checked")) is not int or report["claims_checked"]<count:
        errors.append("Not all entries have evidence claims")
    if report.get("review_method")!="private_dossier_and_editorial_review":
        errors.append("No documented editorial source review")
    try:
        value=datetime.fromisoformat(str(report["reviewed_at"]).replace("Z","+00:00"))
        if value.tzinfo is None:raise ValueError("tz")
    except (KeyError,ValueError,TypeError):
        errors.append("Missing/invalid editorial review timestamp")
    return errors

def check_private_receipt(edition,dossier):
    errors=check_public_receipt(edition)
    if errors:return errors
    try:
        expected=private_review(edition,dossier,receipt_version=edition["fact_audit"]["audit_version"])
    except (ValueError,TypeError) as e:
        return ["Private evidence verification failed: "+str(e)]
    for k,value in expected.items():
        if edition["fact_audit"].get(k)!=value:
            errors.append("Fact audit does not match actual private evidence: "+k)
    return errors

def prepare_edition(edition,candidates,dossier):
    """Export only public metadata, never profiles, scores or source excerpts."""
    import copy
    out=copy.deepcopy(edition)
    rows=candidates if isinstance(candidates,list) else [*candidates.get("articles",[]),*candidates.get("headlines",[])]
    by_id={x["id"]:x for x in rows}
    for item in [*out.get("articles",[]),*out.get("headlines",[])]:
        original=by_id.get(item["id"],{})
        proof=dossier.get("proofs",{}).get(item["id"],{})
        if original.get("url")!=item["url"] or proof.get("source_url")!=item["url"]:
            raise ValueError("Candidate/proof identity mismatch: "+item["id"])
        if proof.get("level") not in ("headline","teaser","read"):
            raise ValueError("Missing documented evidence level")
        item["evidence_level"]=proof["level"]
        for key in ("article_type","source_context","why_selected","novelty_explanation"):
            if original.get(key) is not None:item[key]=original[key]
        item.pop("access",None)
    out.pop("fact_audit",None)
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("prepare","audit","verify"))
    ap.add_argument("--edition",required=True)
    ap.add_argument("--dossier")
    ap.add_argument("--candidates")
    ap.add_argument("--require-dossier",action="store_true")
    args=ap.parse_args()
    with open(args.edition,encoding="utf-8") as f:ed=json.load(f)
    proof=None
    if args.dossier:
        with open(args.dossier,encoding="utf-8") as f:proof=json.load(f)
    if args.action=="prepare":
        if proof is None or not args.candidates:ap.error("prepare requires --dossier and --candidates")
        with open(args.candidates,encoding="utf-8") as f:candidates=json.load(f)
        print(json.dumps(prepare_edition(ed,candidates,proof),ensure_ascii=False,indent=2))
        return
    if args.action=="audit":
        if proof is None:ap.error("audit requires the private evidence dossier")
        print(json.dumps(private_review(ed,proof),ensure_ascii=False,indent=2))
        return
    if args.require_dossier and proof is None:
        problems=["Private dossier required for final editorial release"]
    else:
        problems=check_private_receipt(ed,proof) if proof is not None else check_public_receipt(ed)
    print(json.dumps({"ok":not problems,"errors":problems,
                      "proof_depth":"private" if proof is not None else "public_receipt_only"},
                     ensure_ascii=False,indent=2))
    if problems:raise SystemExit(2)

if __name__=="__main__":
    main()
