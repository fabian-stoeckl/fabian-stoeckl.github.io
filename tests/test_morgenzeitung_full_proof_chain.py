"""Full isolated proof chain: synthetic feedback -> real learner -> selector -> publication matcher.

No synthetic feedback or audit is written to a GitHub profile.
"""
import unittest
from scripts.morgenzeitung_feedback import learn
from scripts.morgenzeitung_selection_audit import compare
from scripts.morgenzeitung_publication_audit import verify

DAY = "2026-11-02"

class FullProofChain(unittest.TestCase):
    def test_full_chain_and_no_feedback_control(self):
        rated = [
            {"id": f"{i:016x}", "topic": topic, "source": "Handelsblatt"}
            for i, topic in enumerate(
                ["Industrie & Rohstoffe", "Industrie & Handelspolitik",
                 "Industrie & Organisation", "Industrie & Welthandel"], 1)]
        issue = {"number": 801, "title": "[Morgenzeitung] Sammelbewertung " + DAY,
                 "updated_at": DAY + "T12:00:00Z",
                 "body": "Ausgabe: " + DAY + "\n" + "".join(
                     "Bereich: Vertiefungen\nArtikel-ID: " + a["id"] +
                     "\nBewertung: " + ("Teilweise relevant" if i == 3 else "Sehr relevant") +
                     "\nBegründung: –\n\n"
                     for i, a in enumerate(rated))}
        profile, report = learn({}, [issue], {DAY: {"articles": rated, "headlines": []}})
        self.assertEqual(report["ratings"], 4)
        self.assertEqual(profile["computed_learning_signals"][0]["topic"], "Industrie")
        pool = [
            {"id": "neutral", "topic": "Sonstiges", "source": "ORF", "verified": True},
            {"id": "industry", "topic": "Industrie & Rohstoffe", "source": "HB", "verified": True}]
        audit = compare(pool, profile, limit=1)
        self.assertEqual(audit["baseline_ids"], ["neutral"])
        self.assertEqual(audit["selected_ids"], ["industry"])
        self.assertEqual(audit["changed_top_n_count"], 1)
        self.assertFalse(audit["editorial_effect_verified"])
        self.assertFalse(audit["publication_verified"])
        index = {"dates": [DAY]}
        published = {"date": DAY, "preview": False, "articles": [{"id": "industry"}]}
        checked = verify(index, published, audit, DAY)
        self.assertTrue(checked["editorial_effect_verified"])
        self.assertTrue(checked["publication_verified"])
        with self.assertRaisesRegex(ValueError, "differ"):
            verify(index, {"date": DAY, "articles": [{"id": "neutral"}]}, audit, DAY)
        without = compare(pool, {}, limit=1)
        self.assertFalse(without["counterfactual_effect_verified"])
        no_effect = verify(index, {"date": DAY, "articles": [{"id": "neutral"}]}, without, DAY)
        self.assertFalse(no_effect["editorial_effect_verified"])

if __name__ == "__main__":
    unittest.main()
