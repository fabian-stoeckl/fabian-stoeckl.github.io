import unittest
from scripts.morgenzeitung_feedback import learn

class LearningTests(unittest.TestCase):
    def setUp(self):
        self.profile = {"topics": {"KI": 5}, "learning_signals": [], "processed_feedback": []}
        self.editions = {"2026-10-22": {"headlines": [], "articles": [
            {"id": "1111111111111111", "topic": "KI", "title": "A"},
            {"id": "2222222222222222", "topic": "KI", "title": "B"}]}}
    def issue(self, number, body, updated="2026-10-22T10:00:00Z"):
        return {"number": number, "title": "[Morgenzeitung] Sammelbewertung 2026-10-22",
                "body": "Ausgabe: 2026-10-22\n" + body, "updated_at": updated}
    def test_idempotence_and_signal(self):
        body = "Bereich: Vertiefungen\nArtikel-ID: 1111111111111111\nBewertung: Sehr relevant\nBegründung: –\n\nBereich: Vertiefungen\nArtikel-ID: 2222222222222222\nBewertung: Sehr relevant\nBegründung: –\n"
        issues = [self.issue(4, body)]
        first, report = learn(self.profile, issues, self.editions)
        second, again = learn(first, issues, self.editions)
        self.assertEqual(first, second)
        self.assertEqual(report, again)
        self.assertEqual(first["computed_learning_signals"][0]["direction"], "positive")
        self.assertEqual(first["editorial_review_queue"][0]["status"], "pending_editorial_review")
    def test_revisions_replace_not_add(self):
        a = self.issue(4, "Artikel-ID: 1111111111111111\nBewertung: Sehr relevant\nBegründung: –")
        b = self.issue(5, "Artikel-ID: 1111111111111111\nBewertung: Nicht relevant\nBegründung: –", "2026-10-22T11:00:00Z")
        _, report = learn(self.profile, [a,b], self.editions)
        self.assertEqual(report["ratings"], 1)
    def test_unknown_id_fails(self):
        with self.assertRaises(ValueError):
            learn(self.profile, [self.issue(4, "Artikel-ID: ffffffffffffffff\nBewertung: Sehr relevant\nBegründung: –")], self.editions)
    def test_uncategorized_news_does_not_become_region_preference(self):
        edition = {"2026-10-22": {"headlines": [
            {"id": "3333333333333333", "region": "Österreich", "title": "News"},
            {"id": "4444444444444444", "region": "Österreich", "title": "News 2"}], "articles": []}}
        body = "Bereich: Heute wichtig\nArtikel-ID: 3333333333333333\nBewertung: Nicht relevant\nBegründung: –\n\nBereich: Heute wichtig\nArtikel-ID: 4444444444444444\nBewertung: Nicht relevant\nBegründung: –"
        profile, report = learn(self.profile, [self.issue(5, body)], edition)
        self.assertEqual(profile["computed_learning_signals"], [])
        self.assertEqual(report["ratings"], 2)
    def test_free_text_is_preserved_idempotently(self):
        issue = self.issue(4, "Artikel-ID: 1111111111111111\nBewertung: Keine Auswahl\nBegründung: Mehr Industriepolitik bitte")
        first, report = learn(self.profile, [issue], self.editions)
        second, again = learn(first, [issue], self.editions)
        self.assertEqual(first, second)
        self.assertEqual(report, again)
        self.assertEqual(report["text_feedback"], 1)
        self.assertEqual(first["feedback_observations"][0]["reason"], "Mehr Industriepolitik bitte")
    def test_tests_excluded(self):
        issue = self.issue(1, "TEST: true")
        _, report = learn(self.profile, [issue], self.editions)
        self.assertEqual(report["issues"], 0)

if __name__ == "__main__":
    unittest.main()
