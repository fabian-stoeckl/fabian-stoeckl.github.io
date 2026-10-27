"""Fail-closed checkpoint reader and recovery decision for Morgenzeitung.

Checkpoints are created *privately*, append-only under
checkpoints/YYYY-MM-DD/attempt-ID/Sx.json, immediately after each verified phase.
This module is deliberately offline: it cannot research articles, claim remote
readback, publish, or fabricate an S7 audit. The scheduled agents must perform
the independent GitHub/HTTPS checks and supply their actual results as JSON.
"""
import argparse
from datetime import date as date_type
import json
from pathlib import Path
import re

PHASES = ("S0", "S1", "S2", "S3", "S4", "S5")
_REQUIRED = {
    "S0": ("public_head", "private_head"),
    "S1": ("issue_versions",),
    "S2": ("profile_blob_sha",),
    "S3": ("window_start", "source_roster_checked"),
    "S4": ("snapshot_commit", "candidate_path", "readback_verified", "preflight_passed"),
    "S5": ("selection_path", "quality_passed"),
}
_SHA = re.compile(r"^[0-9a-f]{40}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _valid_date(value):
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        raise ValueError("Invalid YYYY-MM-DD date")
    try:
        date_type.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid calendar date") from exc


def _valid_phase(record, edition):
    """Only remote-readback-confirmed, stage-specific checkpoints are reusable."""
    if not isinstance(record, dict) or record.get("date") != edition:
        return False
    stage = record.get("stage")
    if stage not in _REQUIRED or record.get("schema") != 1:
        return False
    if record.get("verified") is not True or record.get("remote_readback") is not True:
        return False
    if not isinstance(record.get("attempt"), str) or not record["attempt"].strip():
        return False
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        return False
    for field in _REQUIRED[stage]:
        val = evidence.get(field)
        if val is None or val is False or val == "":
            return False
        if field == "issue_versions" and not isinstance(val, list):
            return False
        if field == "source_roster_checked" and (not isinstance(val, list) or len(val) < 20):
            return False
    if stage in ("S4", "S5"):
        if stage == "S4" and (evidence["preflight_passed"] is not True or evidence["readback_verified"] is not True):
            return False
        if stage == "S5" and evidence["quality_passed"] is not True:
            return False
    for field in ("public_head", "private_head", "profile_blob_sha", "snapshot_commit"):
        if field in evidence and not _SHA.fullmatch(str(evidence[field])):
            return False
    return True


def recovery_plan(edition, checkpoints, public, s7, *, active_pr=None):
    """Return a plan; never confuse CI-green, an open PR, or a claim with HTTPS PASS.

    public is fresh independently read evidence: index_has_date, live_verified,
    ordered_ids_match and public_commit. s7 is independent remote evidence:
    private_run_readback, profile_readback, final_audit_pass and public_commit.
    """
    _valid_date(edition)
    if not isinstance(checkpoints, list) or not isinstance(public, dict) or not isinstance(s7, dict):
        raise ValueError("Checkpoints must be a list; public and s7 must be objects")
    if active_pr is not None and (not isinstance(active_pr, int) or active_pr < 1):
        raise ValueError("active_pr must be a positive pull request number")

    live = (public.get("date") == edition
            and public.get("index_has_date") is True
            and public.get("live_verified") is True
            and public.get("ordered_ids_match") is True
            and isinstance(public.get("public_commit"), str)
            and bool(_SHA.fullmatch(public["public_commit"])))
    if live:
        finished = (s7.get("date") == edition
                    and s7.get("private_run_readback") is True
                    and s7.get("profile_readback") is True
                    and s7.get("final_audit_pass") is True
                    and s7.get("public_commit") == public["public_commit"])
        if finished:
            return {"action": "DONE", "next_stage": "S8",
                    "reason": "Independent HTTPS, ordered IDs and S7 readbacks match"}
        return {"action": "RESUME_S7", "next_stage": "S7",
                "reason": "Today's verified edition is live; finish private learning and audit, do not republish"}

    if active_pr:
        return {"action": "RESUME_PUBLICATION_PR", "next_stage": "S6", "pr": active_pr,
                "reason": "An existing publication PR must be repaired/verified, not duplicated"}

    # Reuse only a contiguous, individually verified phase chain from one attempt.
    by_attempt = {}
    for cp in checkpoints:
        if _valid_phase(cp, edition):
            by_attempt.setdefault(cp["attempt"], {})[cp["stage"]] = cp
    progressed = []
    for attempt, records in by_attempt.items():
        depth = -1
        for n, stage in enumerate(PHASES):
            if stage in records:
                depth = n
            else:
                break
        progressed.append((depth, attempt))
    if progressed:
        depth, attempt = max(progressed, key=lambda v: (v[0], v[1]))
        if depth >= 0:
            next_stage = "S6" if depth == 5 else PHASES[depth + 1]
            return {"action": "RESUME_CHECKPOINT", "next_stage": next_stage,
                    "attempt": attempt, "last_verified_stage": PHASES[depth],
                    "reason": "Resume after last remotely verified private phase; recheck source/feedback freshness"}
    return {"action": "START_OR_RECOVER_RESEARCH", "next_stage": "S0",
            "reason": "No complete trustworthy phase chain; inspect private discovery draft and fresh sources"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--evidence", required=True,
                        help="Private local JSON with checkpoints[], public{}, s7{}, active_pr")
    args = parser.parse_args()
    with Path(args.evidence).open(encoding="utf-8") as fd:
        input_data = json.load(fd)
    result = recovery_plan(args.date, input_data.get("checkpoints", []),
                           input_data.get("public", {}), input_data.get("s7", {}),
                           active_pr=input_data.get("active_pr"))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
