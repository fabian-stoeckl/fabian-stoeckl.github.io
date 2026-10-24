"""Conservative, machine-readable acceptance summary of a real private live audit.

A technical audit is not itself proof of productive feedback learning.
"""
import json
from pathlib import Path


def missing_evidence_report(date, missing_paths):
    """Report missing original snapshots without claiming a real learning result."""
    required = ("candidates/", "snapshots/")
    missing = sorted(set(missing_paths))
    if not missing or not all(p.startswith(required) for p in missing):
        raise ValueError("Missing genuine preselection paths required")
    return {"date": date, "verdict": "PARTIAL",
            "missing_original_evidence": missing,
            "note": "Original preselection evidence absent; cannot establish productive learning. Do not reconstruct."}

def acceptance(audit):
    statuses = audit.get("statuses") or {}
    checks = {
        "preselection_evidence": {
            "status": "PASS" if all(audit.get(k) for k in (
                "candidate_pool_sha256", "profile_sha256", "issue_versions",
                "selection_parameters")) else "PARTIAL",
            "reason": "Immutable candidate, profile, issue-version and parameter evidence required",
        },
        "live_publication": {
            "status": "PASS" if statuses.get("live_publication") == "PASS"
                and (audit.get("publication_audit") or {}).get("publication_verified") is True
                else "PARTIAL",
            "reason": "Independent live HTTPS publication comparison required",
        },
        "counterfactual_effect": {
            "status": "PASS" if statuses.get("counterfactual_effect") == "PASS"
                and (audit.get("selection_comparison") or {}).get("counterfactual_effect_verified") is True
                else "PARTIAL",
            "reason": "Same-pool selection must demonstrably differ due to real feedback",
        },
        "feedback_provenance": {
            "status": "PASS" if statuses.get("feedback") == "PASS" else "PARTIAL",
            "reason": "Real feedback origin and processing must be independently established",
        },
        "profile_learning": {
            "status": "PASS" if statuses.get("profile_learning") == "PASS" else "PARTIAL",
            "reason": "Verified profile update from real feedback required",
        },
        "production_provenance": {
            "status": "PASS" if audit.get("publication_commit_verified") is True
                and audit.get("private_run_persistence_verified") is True else "PARTIAL",
            "reason": "Published commit and private run persistence require separate verification",
        },
    }
    verdict = "PASS" if all(c["status"] == "PASS" for c in checks.values()) else "PARTIAL"
    if any(value == "FAIL" for value in statuses.values()):
        verdict = "FAIL"
    return {"date": audit.get("date"), "verdict": verdict, "checks": checks,
            "note": "Never infer productive PASS from tests, simulated ratings, or incomplete evidence."}


def write_report(audit_path, report_path):
    report = acceptance(json.loads(Path(audit_path).read_text()))
    destination = Path(report_path)
    if destination.exists():
        raise FileExistsError("Refusing to overwrite immutable acceptance report")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report
