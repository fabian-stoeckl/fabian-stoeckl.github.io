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
RECEIPT_VERSION=2

def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def edition_hash(edition):
    fields=("id","url","source","title","summary","published_at")
    rows=[{k:entry.get(k) for k in fields}
          for entry in [*edition.get("articles",[]),*edition.get("headlines",[])]]
    return hashlib.sha256(canonical({"date":edition.get("date"),"items":rows})).hexdigest()

def evidence_hash(dossier):
    return hashlib.sha256(canonical(dossier)).hexdigest()

def private_review(edition,dossier):
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
        "audit_version":RECEIPT_VERSION,
        "edition_sha256":edition_hash(edition),
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
    if report.get("audit_version")!=RECEIPT_VERSION:
        errors.append("Wrong fact audit version")
    if report.get("edition_sha256")!=edition_hash(edition):
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
        expected=private_review(edition,dossier)
    except (ValueError,TypeError) as e:
        return ["Private evidence verification failed: "+str(e)]
    for k,value in expected.items():
        if edition["fact_audit"].get(k)!=value:
            errors.append("Fact audit does not match actual private evidence: "+k)
    return errors

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("audit","verify"))
    ap.add_argument("--edition",required=True)
    ap.add_argument("--dossier")
    ap.add_argument("--require-dossier",action="store_true")
    args=ap.parse_args()
    with open(args.edition,encoding="utf-8") as f:ed=json.load(f)
    proof=None
    if args.dossier:
        with open(args.dossier,encoding="utf-8") as f:proof=json.load(f)
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
