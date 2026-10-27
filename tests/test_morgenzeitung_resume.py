"""Regression tests for safe recovery of ChatGPT-scheduled Morgenzeitung runs."""
import unittest
from scripts.morgenzeitung_resume import recovery_plan


DATE = "2026-10-27"
SHA1 = "a" * 40
SHA2 = "b" * 40


def cp(stage, attempt="a", **evidence):
    base = {
        "S0": {"public_head": SHA1, "private_head": SHA2},
        "S1": {"issue_versions": []},
        "S2": {"profile_blob_sha": SHA1},
        "S3": {"window_start": "2026-10-26T12:00:00Z",
               "source_roster_checked": ["publisher-%02d" % i for i in range(20)]},
        "S4": {"snapshot_commit": SHA2, "candidate_path": "candidates/2026-10-27.json",
               "readback_verified": True, "preflight_passed": True},
        "S5": {"selection_path": "audits/2026-10-27-selection.json",
               "quality_passed": True},
    }[stage]
    return {"schema": 1, "date": DATE, "attempt": attempt, "stage": stage,
            "verified": True, "remote_readback": True,
            "evidence": dict(base, **evidence)}


def lived():
    return {"date": DATE, "index_has_date": True, "live_verified": True,
            "ordered_ids_match": True, "public_commit": SHA1}


def audited():
    return {"date": DATE, "private_run_readback": True, "profile_readback": True,
            "final_audit_pass": True, "public_commit": SHA1}


class RecoveryTests(unittest.TestCase):
    def test_no_checkpoint_starts_research(self):
        p = recovery_plan(DATE, [], {}, {})
        self.assertEqual(p["action"], "START_OR_RECOVER_RESEARCH")
        self.assertEqual(p["next_stage"], "S0")

    def test_initial_research_checkpoint_resumes_in_ingest(self):
        p = recovery_plan(DATE, [cp("S0")], {}, {})
        self.assertEqual(p["next_stage"], "S1")

    def test_research_checkpoint_resumes_without_rearchiving(self):
        chain = [cp(s) for s in ("S0", "S1", "S2", "S3", "S4")]
        p = recovery_plan(DATE, chain, {}, {})
        self.assertEqual(p["next_stage"], "S5")

    def test_completed_selection_resumes_publication(self):
        p = recovery_plan(DATE, [cp(s) for s in ("S0", "S1", "S2", "S3", "S4", "S5")], {}, {})
        self.assertEqual(p["next_stage"], "S6")

    def test_missing_middle_checkpoint_not_skipped(self):
        p = recovery_plan(DATE, [cp("S0"), cp("S1"), cp("S3"), cp("S4")], {}, {})
        self.assertEqual(p["next_stage"], "S2")

    def test_do_not_mix_checkpoints_across_attempts(self):
        p = recovery_plan(DATE, [cp("S0", "a"), cp("S1", "b"), cp("S2", "b")], {}, {})
        self.assertEqual(p["next_stage"], "S1")

    def test_remote_readback_required(self):
        p = recovery_plan(DATE, [cp("S0", remote_readback=False)], {}, {})
        self.assertEqual(p["next_stage"], "S0")

    def test_invalid_archive_preflight_fails_closed(self):
        chain = [cp(s) for s in ("S0", "S1", "S2", "S3")]
        chain.append(cp("S4", preflight_passed=False))
        p = recovery_plan(DATE, chain, {}, {})
        self.assertEqual(p["next_stage"], "S4")

    def test_not_enough_sources(self):
        chain = [cp(s) for s in ("S0", "S1", "S2")]
        chain.append(cp("S3", source_roster_checked=["Reuters"]))
        p = recovery_plan(DATE, chain, {}, {})
        self.assertEqual(p["next_stage"], "S3")

    def test_live_edition_trumps_open_pr_and_skips_republishing(self):
        p = recovery_plan(DATE, [], lived(), {}, active_pr=188)
        self.assertEqual(p["action"], "RESUME_S7")

    def test_real_active_publication_pr_is_resumed(self):
        p = recovery_plan(DATE, [], {}, {}, active_pr=185)
        self.assertEqual(p["action"], "RESUME_PUBLICATION_PR")
        self.assertEqual(p["pr"], 185)

    def test_green_ci_does_not_prove_publication(self):
        p = recovery_plan(DATE, [], {"date": DATE, "ci_green": True}, audited())
        self.assertEqual(p["action"], "START_OR_RECOVER_RESEARCH")

    def test_incomplete_live_evidence_blocks_s7(self):
        public = lived()
        public["ordered_ids_match"] = False
        p = recovery_plan(DATE, [], public, audited())
        self.assertNotEqual(p["action"], "DONE")
        self.assertNotEqual(p["action"], "RESUME_S7")

    def test_live_but_missing_s7_remains_pending(self):
        p = recovery_plan(DATE, [], lived(), {"date": DATE, "private_run_readback": True})
        self.assertEqual(p["action"], "RESUME_S7")

    def test_end_to_end_done_requires_matching_public_commit(self):
        proof = audited()
        proof["public_commit"] = SHA2
        self.assertEqual(recovery_plan(DATE, [], lived(), proof)["action"], "RESUME_S7")
        self.assertEqual(recovery_plan(DATE, [], lived(), audited())["action"], "DONE")

    def test_no_cross_day_or_unverified_checkpoint(self):
        record = cp("S0")
        record["date"] = "2026-10-26"
        self.assertEqual(recovery_plan(DATE, [record], {}, {})["next_stage"], "S0")

    def test_bad_date_and_pr_rejected(self):
        with self.assertRaises(ValueError):
            recovery_plan("2026-10-99", [], {}, {})
        with self.assertRaises(ValueError):
            recovery_plan(DATE, [], {}, {}, active_pr=0)


if __name__ == "__main__":
    unittest.main()
