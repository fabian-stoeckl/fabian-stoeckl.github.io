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
    def test_later_entry_in_same_issue_replaces_previous(self):
        body = ("Artikel-ID: 1111111111111111\nBewertung: Sehr relevant\nBegründung: –\n\n"
                "Artikel-ID: 1111111111111111\nBewertung: Nicht relevant\nBegründung: Neue Einschätzung")
        profile, report = learn(self.profile, [self.issue(4, body)], self.editions)
        self.assertEqual(report["ratings"], 1)
        self.assertEqual(profile["feedback_observations"][0]["rating"], "Nicht relevant")
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
    def test_real_2026_10_23_uncategorized_feedback_preserved_without_invented_topic(self):
        """Regression for real feedback #6: avoid mistaking geography for a topic."""
        editions = {"2026-10-23": {"headlines": [
            {"id": "451a044c6532f9a7", "title": "Strengere Regeln und neue Kindersätze", "source": "ORF", "region": "Österreich"},
            {"id": "5fb5c9ccbe27ed04", "title": "Gesetz gegen SLAPP-Klagen vorgelegt", "source": "ORF", "region": "Österreich"}], "articles": []}}
        issue = {"number": 6, "title": "[Morgenzeitung] Sammelbewertung 2026-10-23",
                 "updated_at": "2026-10-23T11:39:55Z",
                 "body": "Ausgabe: 2026-10-23\nBereich: Heute wichtig\nArtikel-ID: 451a044c6532f9a7\nBewertung: Sehr relevant\nBegründung: –\n\nBereich: Heute wichtig\nArtikel-ID: 5fb5c9ccbe27ed04\nBewertung: Nicht relevant\nBegründung: So juristische Details interessieren mich nicht wenn es um Randbereiche geht die nicht zentrale Interessen betreffen."}
        result, report = learn(self.profile, [issue], editions)
        self.assertEqual(report["ratings"], 2)
        self.assertEqual(result["processed_feedback"][0]["issue"], 6)
        self.assertEqual(result["computed_learning_signals"], [])
        self.assertEqual(result["topic_evidence"], [])
        self.assertEqual(len(result["feedback_observations"]), 1)
        self.assertIn("juristische Details", result["feedback_observations"][0]["reason"])
        self.assertEqual(result, learn(result, [issue], editions)[0])

    def test_uncategorized_real_feedback_reaches_editorial_queue(self):
        edition = {"2026-10-23": {"headlines": [
            {"id": "451a044c6532f9a7", "title": "Sozialhilfe", "source": "ORF"},
            {"id": "5fb5c9ccbe27ed04", "title": "SLAPP", "source": "ORF"}],
            "articles": []}}
        issue = {"number": 6, "title": "[Morgenzeitung] Sammelbewertung 2026-10-23",
                 "updated_at": "2026-10-23T11:39:55Z",
                 "body": ("Ausgabe: 2026-10-23\n"
                          "Bereich: Heute wichtig\nArtikel-ID: 451a044c6532f9a7\n"
                          "Bewertung: Sehr relevant\nBegründung: –\n\n"
                          "Bereich: Heute wichtig\nArtikel-ID: 5fb5c9ccbe27ed04\n"
                          "Bewertung: Nicht relevant\n"
                          "Begründung: Juristische Randdetails interessieren mich nicht")}
        first, report = learn(self.profile, [issue], edition)
        second, again = learn(first, [issue], edition)
        self.assertEqual(first, second)
        self.assertEqual(report, again)
        self.assertEqual(report["ratings"], 2)
        self.assertEqual(first["computed_learning_signals"], [])
        queue = first["editorial_review_queue"]
        self.assertEqual(len(queue), 2)
        self.assertEqual({item["article_id"] for item in queue},
                         {"451a044c6532f9a7", "5fb5c9ccbe27ed04"})
        self.assertTrue(all(item["topic"] is None for item in queue))
        self.assertTrue(all(item["scope"] == "article_only_no_topic_inference" for item in queue))
        self.assertIn("Juristische Randdetails", queue[1]["reason"])

    def test_tests_excluded(self):
        issue = self.issue(1, "TEST: true")
        _, report = learn(self.profile, [issue], self.editions)
        self.assertEqual(report["issues"], 0)

if __name__ == "__main__":
    unittest.main()
