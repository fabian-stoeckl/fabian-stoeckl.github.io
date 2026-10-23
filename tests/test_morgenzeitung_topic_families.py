"""Conservative topic-family learning from explicit article tags."""
import unittest
from scripts.morgenzeitung_feedback import learn, topic_family
from scripts.morgenzeitung_editorial import select_articles

DAY = "2026-11-01"
def article(i, topic):
    return {"id": "%016x" % i, "topic": topic, "source": "Handelsblatt", "verified": True}
def issue(articles, ratings):
    body = "Ausgabe: " + DAY + "\n"
    for a, rating in zip(articles, ratings):
        body += "Bereich: Vertiefungen\nArtikel-ID: %s\nBewertung: %s\nBegründung: –\n\n" % (a["id"], rating)
    return {"number": 100, "title": "[Morgenzeitung] Sammelbewertung " + DAY,
            "updated_at": DAY + "T12:00:00Z", "body": body}
class FamilyLearning(unittest.TestCase):
    def test_realistic_composite_industry_topics_produce_cautious_signal(self):
        a = [article(1, "Industrie & Handelspolitik"),
             article(2, "Industrie & Rohstoffe"),
             article(3, "Industrie & Welthandel"),
             article(4, "Industrie & Organisation")]
        p, report = learn({}, [issue(a, ["Sehr relevant", "Sehr relevant", "Sehr relevant", "Teilweise relevant"])],
                          {DAY: {"headlines": [], "articles": a}})
        self.assertEqual(report["ratings"], 4)
        self.assertEqual(p["computed_learning_signals"][0]["topic"], "Industrie")
        self.assertEqual(p["computed_learning_signals"][0]["ratings"], 4)
        self.assertEqual(p["computed_learning_signals"][0]["scope"], "explicit_topic_family")
        self.assertEqual(p["topic_family_evidence"][0]["net_score"], 3)
        candidates = [article(5, "Wissenschaft & Gesellschaft"),
                      article(6, "Industrie & Rohstoffe")]
        selected, audit = select_articles(candidates, p, limit=1)
        self.assertEqual(selected[0]["id"], candidates[1]["id"])
        self.assertEqual(audit[0]["learning_direction"], "positive")
        self.assertEqual(p, learn(p, [issue(a, ["Sehr relevant", "Sehr relevant", "Sehr relevant", "Teilweise relevant"])],
                                  {DAY: {"headlines": [], "articles": a}})[0])
    def test_two_votes_are_insufficient_for_broad_family(self):
        a = [article(1, "KI & Kapitalmarkt"), article(2, "KI & Unternehmensfinanzierung")]
        p, _ = learn({}, [issue(a, ["Sehr relevant", "Sehr relevant"])],
                     {DAY: {"headlines": [], "articles": a}})
        self.assertEqual(p["computed_learning_signals"], [])
        self.assertEqual(p["topic_family_evidence"][0]["ratings"], 2)
    def test_opposite_votes_do_not_produce_signal(self):
        a = [article(1, "Industrie & Rohstoffe"), article(2, "Industrie & Handelspolitik"),
             article(3, "Industrie & Welthandel")]
        p, _ = learn({}, [issue(a, ["Sehr relevant", "Nicht relevant", "Teilweise relevant"])],
                     {DAY: {"headlines": [], "articles": a}})
        self.assertEqual(p["computed_learning_signals"], [])
    def test_uncategorized_headlines_do_not_infer_geography(self):
        self.assertIsNone(topic_family(None))
        self.assertEqual(topic_family("Österreich"), "Österreich")
        self.assertEqual(topic_family("Industrie & Rohstoffe"), "Industrie")
        self.assertEqual(topic_family("Zuckerl"), "Zuckerl")
    def test_exact_topic_signal_takes_precedence_over_family(self):
        p = {"computed_learning_signals": [
            {"topic": "Industrie", "direction": "positive", "confidence": "preliminary"},
            {"topic": "Industrie & Rohstoffe", "direction": "negative", "confidence": "preliminary"}]}
        a = [article(1, "Industrie & Rohstoffe"), article(2, "Industrie & Welthandel")]
        selected, audit = select_articles(a, p, limit=2)
        self.assertEqual([x["id"] for x in selected], [a[1]["id"], a[0]["id"]])
if __name__ == "__main__":
    unittest.main()
