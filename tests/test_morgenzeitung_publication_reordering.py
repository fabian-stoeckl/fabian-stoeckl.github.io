import unittest
from scripts.morgenzeitung_publication_audit import verify


class PublicationReorderTests(unittest.TestCase):
    def setUp(self):
        self.date = "2026-10-24"
        self.index = {"dates": [self.date]}
        self.edition = {"date": self.date, "articles": [{"id": "b"}, {"id": "a"}]}
        self.audit = {
            "selected_ids": ["b", "a"],
            "baseline_ids": ["a", "b"],
            "counterfactual_effect_verified": True,
            "effective_signals": [{"topic": "Industrie", "direction": "positive"}],
            "newly_selected_ids": [],
            "displaced_ids": [],
            "changed_top_n_count": 0,
        }

    def test_rank_only_change_is_a_real_counterfactual(self):
        result = verify(self.index, self.edition, self.audit, self.date)
        self.assertTrue(result["publication_verified"])
        self.assertTrue(result["editorial_effect_verified"])
        self.assertTrue(result["ranking_only_change"])
        self.assertEqual(result["changed_top_n_count"], 0)

    def test_forged_addition_rejected(self):
        self.audit["newly_selected_ids"] = ["b"]
        with self.assertRaisesRegex(ValueError, "Counterfactual change evidence"):
            verify(self.index, self.edition, self.audit, self.date)

    def test_unchanged_baseline_rejected(self):
        self.audit["baseline_ids"] = ["b", "a"]
        with self.assertRaisesRegex(ValueError, "Counterfactual change evidence"):
            verify(self.index, self.edition, self.audit, self.date)


if __name__ == "__main__":
    unittest.main()
