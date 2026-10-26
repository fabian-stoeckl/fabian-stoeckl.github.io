import unittest
from scripts.morgenzeitung_source_diversity import audit_source_diversity, require_source_diversity


class DiversityTests(unittest.TestCase):
    def test_reuters_single_source_failure_detected(self):
        pool = [{"source": "Reuters"}] * 15 + [{"source": "Der Standard"}]
        report = audit_source_diversity(pool)
        self.assertFalse(report["diversity_passed"])
        self.assertEqual(report["largest_source_count"], 15)
        with self.assertRaisesRegex(ValueError, "concentration"):
            require_source_diversity(pool)

    def test_diverse_research_passes(self):
        pool = [{"source": name} for name in ["Reuters", "AP", "Handelsblatt", "ORF", "FT", "FAZ"]]
        self.assertTrue(require_source_diversity(pool)["diversity_passed"])

    def test_empty_and_malformed_pool_rejected(self):
        for pool in ([], [{"source": ""}], [{"source": 3}]):
            with self.subTest(pool=pool), self.assertRaises(ValueError):
                audit_source_diversity(pool)


if __name__ == "__main__":
    unittest.main()
