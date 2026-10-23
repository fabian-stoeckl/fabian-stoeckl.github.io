"""Offline replay: actual published article pool, synthetic feedback."""
import json
import unittest
from pathlib import Path
from scripts.morgenzeitung_feedback import learn

class ResearchReplay(unittest.TestCase):
    def test_feedback_changes_real_story_ranking(self):
        editions = {day: json.loads(Path("Privat/Pressespiegel/data", day + ".json").read_text())
                    for day in ("2026-10-22", "2026-10-23")}
        pool = [a for d in editions.values() for a in d["articles"]]
        self.assertEqual(len(pool), 20)
        good = ("Industrie", "KI", "Produktivität", "Infrastruktur")
        bad = ("Klima", "Wissenschaft", "Kreislaufwirtschaft")
        def quality(a):
            return 1 if any(k in a["topic"] for k in good) else (-1 if any(k in a["topic"] for k in bad) else 0)
        profile, issues, history = {}, [], []
        for cycle in range(1, 9):
            signal = {s["topic"]: s["direction"] for s in profile.get("computed_learning_signals", [])}
            ranked = sorted(pool, key=lambda a: (-({"positive": 4, "negative": -4}.get(signal.get(a["topic"]), 0)), a["id"]))
            history.append(sum(quality(a) == 1 for a in ranked[:10]))
            day = "2026-11-%02d" % cycle
            editions[day] = {"articles": [], "headlines": []}
            body = "Ausgabe: " + day + "\n"
            for idx, article in enumerate(pool):
                a = dict(article, id="%016x" % (cycle * 1000 + idx))
                editions[day]["articles"].append(a)
                rating = "Sehr relevant" if quality(a) == 1 else ("Nicht relevant" if quality(a) == -1 else "Teilweise relevant")
                body += "Bereich: Vertiefungen\nArtikel-ID: %s\nBewertung: %s\nBegründung: –\n\n" % (a["id"], rating)
            issues.append({"number": cycle, "title": "[Morgenzeitung] Sammelbewertung " + day,
                           "body": body, "updated_at": day + "T12:00:00Z"})
            profile, report = learn(profile, issues, editions)
        self.assertGreater(history[-1], history[0])
        self.assertEqual(report["ratings"], 160)
        self.assertEqual(len(profile["processed_feedback"]), 8)
