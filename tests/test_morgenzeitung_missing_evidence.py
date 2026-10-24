import unittest
from scripts.morgenzeitung_acceptance_report import missing_evidence_report


class MissingEvidenceReportTests(unittest.TestCase):
    def test_partial_verdict(self):
        result = missing_evidence_report("2026-10-24", ["candidates/2026-10-24.json"])
        self.assertEqual(result["verdict"], "PARTIAL")
        self.assertEqual(result["missing_original_evidence"], ["candidates/2026-10-24.json"])

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            missing_evidence_report("2026-10-24", [])

    def test_rejects_unrelated(self):
        with self.assertRaises(ValueError):
            missing_evidence_report("2026-10-24", ["profile.json"])


if __name__ == "__main__":
    unittest.main()
