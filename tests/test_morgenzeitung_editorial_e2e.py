"""Full offline research -> ratings -> learning -> editorial selection loop."""
import json
import unittest
from pathlib import Path
from scripts.morgenzeitung_feedback import learn
from scripts.morgenzeitung_editorial import select_articles

class EditorialEndToEnd(unittest.TestCase):
    def test_research_replay_changes_production_selector(self):
        original = [json.loads(Path("Privat/Pressespiegel/data", d + ".json").read_text())
                    for d in ("2026-10-22", "2026-10-23")]
        pool = [dict(a) for edition in original for a in edition["articles"]]
        self.assertEqual(len(pool), 20)
        # Research simulation reuses published, verified articles as candidate pool.
        # Fixed deterministic order prevents the test from passing by lucky input ordering.
        pool.sort(key=lambda a: a["id"])
        positive = ("Industrie", "KI", "Produktivität", "Infrastruktur")
        negative = ("Klima", "Wissenschaft", "Kreislaufwirtschaft")
        def preference(article):
            topic = article["topic"]
            return 1 if any(k in topic for k in positive) else (-1 if any(k in topic for k in negative) else 0)
        baseline, _ = select_articles(pool, {}, limit=10, max_per_source=10)
        editions, issues, profile = {}, [], {}
        for cycle in range(1, 9):
            date = "2026-11-%02d" % cycle
            articles, body = [], "Ausgabe: " + date + "\n"
            for idx, article in enumerate(pool):
                clone = dict(article, id="%016x" % (cycle * 1000 + idx))
                articles.append(clone)
                vote = "Sehr relevant" if preference(clone) > 0 else ("Nicht relevant" if preference(clone) < 0 else "Teilweise relevant")
                body += "Bereich: Vertiefungen\nArtikel-ID: %s\nBewertung: %s\nBegründung: –\n\n" % (clone["id"], vote)
            editions[date] = {"articles": articles, "headlines": []}
            issues.append({"number": cycle, "title": "[Morgenzeitung] Sammelbewertung " + date,
                           "updated_at": date + "T12:00:00Z", "body": body})
            profile, report = learn(profile, issues, editions)
        final, audit = select_articles(pool, profile, limit=10, max_per_source=10)
        self.assertEqual(report["ratings"], 160)
        self.assertGreater(sum(preference(a) > 0 for a in final),
                           sum(preference(a) > 0 for a in baseline))
        self.assertTrue(any(a["learning_direction"] == "positive" for a in audit))
        self.assertEqual(len(audit), 10)
    def test_unverified_candidates_and_source_caps(self):
        candidates = [
            {"id": "1", "topic": "KI", "source": "A", "verified": False},
            {"id": "2", "topic": "KI", "source": "A"},
            {"id": "3", "topic": "KI", "source": "A"},
            {"id": "4", "topic": "KI", "source": "B"}]
        p = {"computed_learning_signals": [{"topic": "KI", "direction": "positive", "confidence": "preliminary"}]}
        chosen, audit = select_articles(candidates, p, limit=3, max_per_source=1)
        self.assertEqual([a["id"] for a in chosen], ["2", "4"])
        self.assertEqual(len(audit), 2)
