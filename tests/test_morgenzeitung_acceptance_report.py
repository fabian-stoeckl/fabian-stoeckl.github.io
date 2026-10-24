import unittest
from scripts.morgenzeitung_acceptance_report import acceptance


class AcceptanceReportTests(unittest.TestCase):
    def test_missing_evidence_is_partial(self):
        result = acceptance({"date": "2026-10-24", "statuses": {}})
        self.assertEqual(result["verdict"], "PARTIAL")
        self.assertEqual(result["checks"]["preselection_evidence"]["status"], "PARTIAL")

    def test_live_pass_alone_does_not_imply_learning(self):
        result = acceptance({"statuses": {"live_publication": "PASS"},
                             "publication_audit": {"publication_verified": True}})
        self.assertEqual(result["verdict"], "PARTIAL")
        self.assertEqual(result["checks"]["live_publication"]["status"], "PASS")

    def test_explicit_failure_is_failure(self):
        result = acceptance({"statuses": {"live_publication": "FAIL"}})
        self.assertEqual(result["verdict"], "FAIL")

    def test_all_independent_evidence_can_pass(self):
        result = acceptance({
            "candidate_pool_sha256": "a" * 64, "profile_sha256": "b" * 64,
            "issue_versions": [{"number": 3, "updated_at": "2026-10-24"}],
            "selection_parameters": {"limit": 10, "max_per_source": 4},
            "statuses": {"feedback": "PASS", "profile_learning": "PASS",
                         "counterfactual_effect": "PASS", "live_publication": "PASS"},
            "publication_audit": {"publication_verified": True},
            "selection_comparison": {"counterfactual_effect_verified": True},
            "publication_commit_verified": True,
            "private_run_persistence_verified": True,
        })
        self.assertEqual(result["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
