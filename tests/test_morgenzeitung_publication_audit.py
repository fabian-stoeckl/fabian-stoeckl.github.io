"""A real published edition must match the private counterfactual exactly."""
import unittest
from scripts.morgenzeitung_publication_audit import verify

DATE = "2026-10-24"
INDEX = {"dates": [DATE, "2026-10-23"]}
EDITION = {"date": DATE, "preview": False,
           "articles": [{"id": "new"}, {"id": "old"}]}
AUDIT = {"selected_ids": ["new", "old"],
         "baseline_ids": ["old", "replaced"],
         "counterfactual_effect_verified": True,
         "changed_top_n_count": 1,
         "newly_selected_ids": ["new"],
         "displaced_ids": ["replaced"],
         "effective_signals": [{"topic": "Industrie", "direction": "positive"}]}

class PublicationAudit(unittest.TestCase):
    def test_matching_live_publication_confirms_effect(self):
        result = verify(INDEX, EDITION, AUDIT, DATE)
        self.assertTrue(result["publication_verified"])
        self.assertTrue(result["editorial_effect_verified"])
        self.assertEqual(result["changed_top_n_count"], 1)
    def test_same_publication_without_learning_not_effect(self):
        result = verify(INDEX, EDITION, dict(AUDIT, counterfactual_effect_verified=False), DATE)
        self.assertTrue(result["publication_verified"])
        self.assertFalse(result["editorial_effect_verified"])
    def test_unpublished_edition_is_not_evidence(self):
        with self.assertRaisesRegex(ValueError, "not listed"):
            verify({"dates": []}, EDITION, AUDIT, DATE)
    def test_preview_not_accepted(self):
        with self.assertRaisesRegex(ValueError, "preview"):
            verify(INDEX, dict(EDITION, preview=True), AUDIT, DATE)
    def test_mismatched_article_order_not_accepted(self):
        with self.assertRaisesRegex(ValueError, "differ"):
            verify(INDEX, dict(EDITION, articles=list(reversed(EDITION["articles"]))), AUDIT, DATE)
    def test_mismatched_article_id_not_accepted(self):
        with self.assertRaisesRegex(ValueError, "differ"):
            verify(INDEX, dict(EDITION, articles=[{"id": "fake"}, {"id": "old"}]), AUDIT, DATE)
    def test_missing_counterfactual_signal_rejected(self):
        with self.assertRaisesRegex(ValueError, "No effective"):
            verify(INDEX, EDITION, dict(AUDIT, effective_signals=[]), DATE)
    def test_inconsistent_change_count_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            verify(INDEX, EDITION, dict(AUDIT, changed_top_n_count=2), DATE)
    def test_duplicate_selected_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verify(INDEX, EDITION, dict(AUDIT, selected_ids=["new", "new"]), DATE)

if __name__ == "__main__":
    unittest.main()
