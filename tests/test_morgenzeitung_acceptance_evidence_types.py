import unittest
from scripts.morgenzeitung_acceptance_report import acceptance


class AcceptanceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.audit = {
            "date": "2026-10-24",
            "candidate_pool_sha256": "a" * 64,
            "profile_sha256": "b" * 64,
            "issue_versions": [],
            "selection_parameters": {"limit": 10, "max_per_source": 4},
        }

    def test_zero_feedback_issues_still_proves_snapshot_presence(self):
        self.assertEqual(acceptance(self.audit)["checks"]["preselection_evidence"]["status"], "PASS")

    def test_invalid_sha_rejected(self):
        self.audit["profile_sha256"] = "not-a-sha"
        self.assertEqual(acceptance(self.audit)["checks"]["preselection_evidence"]["status"], "PARTIAL")

    def test_boolean_parameter_rejected(self):
        self.audit["selection_parameters"]["limit"] = True
        self.assertEqual(acceptance(self.audit)["checks"]["preselection_evidence"]["status"], "PARTIAL")

    def test_missing_issue_snapshot_rejected(self):
        del self.audit["issue_versions"]
        self.assertEqual(acceptance(self.audit)["checks"]["preselection_evidence"]["status"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
