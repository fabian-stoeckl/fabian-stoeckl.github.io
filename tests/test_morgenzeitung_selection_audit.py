"""Counterfactual editorial effect, guardrails, and repeatability."""
import unittest
from scripts.morgenzeitung_selection_audit import compare

def candidate(n, topic, source="ORF", verified=True):
    return {"id": "%016x" % n, "topic": topic, "source": source, "verified": verified}

class CounterfactualAuditTests(unittest.TestCase):
    def setUp(self):
        self.pool = [
            candidate(1, "Unterhaltung", "A"),
            candidate(2, "Sport", "B"),
            candidate(3, "KI", "C"),
            candidate(4, "Industrie", "D"),
            candidate(5, "Wissenschaft", "E")]
        self.profile = {"computed_learning_signals": [
            {"topic": "KI", "direction": "positive", "confidence": "preliminary", "ratings": 3},
            {"topic": "Industrie", "direction": "positive", "confidence": "preliminary", "ratings": 2},
            {"topic": "Unterhaltung", "direction": "negative", "confidence": "preliminary", "ratings": 3}]}
    def test_counterfactual_changes_top_two_and_explains_it(self):
        result = compare(self.pool, self.profile, limit=2)
        self.assertEqual(result["baseline_ids"], [self.pool[0]["id"], self.pool[1]["id"]])
        self.assertEqual(result["selected_ids"], [self.pool[2]["id"], self.pool[3]["id"]])
        self.assertEqual(result["changed_top_n_count"], 2)
        self.assertEqual(len(result["newly_selected_ids"]), 2)
        self.assertEqual(len(result["displaced_ids"]), 2)
        self.assertTrue(result["counterfactual_effect_verified"])
        self.assertFalse(result["publication_verified"])
        self.assertFalse(result["editorial_effect_verified"])
    def test_no_feedback_is_stable(self):
        result = compare(self.pool, {}, limit=2)
        self.assertEqual(result["selected_ids"], result["baseline_ids"])
        self.assertFalse(result["counterfactual_effect_verified"])
    def test_repeatability(self):
        self.assertEqual(compare(self.pool, self.profile, limit=2),
                         compare(self.pool, self.profile, limit=2))
    def test_preliminary_confidence_required(self):
        profile = {"computed_learning_signals": [
            {"topic": "KI", "direction": "positive", "confidence": "insufficient_evidence"}]}
        self.assertFalse(compare(self.pool, profile, limit=2)["counterfactual_effect_verified"])
    def test_unverified_candidate_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "source-verified"):
            compare(self.pool + [candidate(6, "KI", verified=False)], self.profile)
    def test_missing_verification_is_rejected(self):
        item = candidate(6, "KI")
        del item["verified"]
        with self.assertRaisesRegex(ValueError, "source-verified"):
            compare(self.pool + [item], self.profile)
    def test_duplicate_candidate_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            compare(self.pool + [self.pool[0]], self.profile)
    def test_source_diversity_cap_is_preserved(self):
        pool = [candidate(1, "KI", "A"), candidate(2, "KI", "A"), candidate(3, "Industrie", "B")]
        result = compare(pool, self.profile, limit=2, max_per_source=1)
        self.assertEqual(len(result["selected_ids"]), 2)
        self.assertIn(pool[2]["id"], result["selected_ids"])
    def test_neutral_topics_not_inferred_from_location(self):
        pool = [candidate(1, "Österreich", "A"), candidate(2, "KI", "B")]
        result = compare(pool, self.profile, limit=1)
        self.assertEqual(result["selected_ids"], [pool[1]["id"]])
        self.assertEqual(len(result["effective_signals"]), 3)


    def test_actual_twenty_published_stories_can_be_counterfactually_reranked(self):
        import json
        from pathlib import Path
        pool = []
        for day in ("2026-10-22", "2026-10-23"):
            edition = json.loads(Path("Privat/Pressespiegel/data", day + ".json").read_text())
            pool.extend(dict(item, verified=True) for item in edition["articles"])
        pool.sort(key=lambda item: item["id"])
        self.assertEqual(len(pool), 20)
        baseline_topics = {item["topic"] for item in pool[:10]}
        target = next(item for item in pool[10:] if item["topic"] not in baseline_topics)
        profile = {"computed_learning_signals": [
            {"topic": target["topic"], "direction": "positive", "confidence": "preliminary"}]}
        result = compare(pool, profile, limit=10, max_per_source=10)
        self.assertTrue(result["counterfactual_effect_verified"])
        self.assertIn(target["id"], result["newly_selected_ids"])
        self.assertGreaterEqual(result["changed_top_n_count"], 1)
        self.assertFalse(result["editorial_effect_verified"])

    def test_real_industry_family_signal_changes_three_of_ten_in_historical_replay(self):
        """Actual rated topic family, actual Oct 22/23 story metadata; offline only."""
        import json
        from pathlib import Path
        pool = []
        for day in ("2026-10-22", "2026-10-23"):
            edition = json.loads(Path("Privat/Pressespiegel/data", day + ".json").read_text())
            pool.extend(dict(item, verified=True) for item in edition["articles"])
        pool.sort(key=lambda item: item["id"])
        # 4 real Industrie & ... votes: 3 very relevant, 1 neutral.
        profile = {"computed_learning_signals": [
            {"topic": "Industrie", "direction": "positive", "confidence": "preliminary",
             "ratings": 4, "net_score": 3, "scope": "explicit_topic_family"}]}
        result = compare(pool, profile, limit=10, max_per_source=4)
        self.assertEqual(result["candidate_count"], 20)
        self.assertEqual(result["changed_top_n_count"], 3)
        self.assertEqual(len(result["newly_selected_ids"]), 3)
        self.assertEqual(len(result["displaced_ids"]), 3)
        self.assertTrue(result["counterfactual_effect_verified"])
        self.assertFalse(result["publication_verified"])
        self.assertFalse(result["editorial_effect_verified"])

if __name__ == "__main__":
    unittest.main()
