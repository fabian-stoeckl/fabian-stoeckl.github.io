"""Isolated multi-cycle simulation: never submits synthetic votes to GitHub."""
import unittest
from scripts.morgenzeitung_feedback import learn

TOPICS = ("Promi-News", "KI & Produktivität", "Juristische Randdetails", "Industriepolitik")
PREFER = {"KI & Produktivität": 1, "Industriepolitik": 1, "Promi-News": -1, "Juristische Randdetails": -1}

def simulate(rounds=12):
    profile = {"computed_learning_signals": [], "processed_feedback": []}
    editions, issues, history = {}, [], []
    for day in range(1, rounds + 1):
        date = "2026-11-%02d" % day
        signals = {s["topic"]: s for s in profile.get("computed_learning_signals", [])}
        # Separate simulated editor: consumes actual learner signals.
        ranking = sorted(TOPICS, key=lambda t: (-(
            (3 if signals.get(t, {}).get("direction") == "positive" else
             -3 if signals.get(t, {}).get("direction") == "negative" else 0)
        ), TOPICS.index(t)))
        # Include all topics for exploration, ensuring negatives remain measurable.
        articles = [{"id": ("%016x" % (day * 100 + i)), "topic": topic,
                     "title": "Synthetic %s" % topic}
                    for i, topic in enumerate(ranking)]
        editions[date] = {"articles": articles, "headlines": []}
        body = "Ausgabe: %s\n" % date
        for a in articles:
            vote = "Sehr relevant" if PREFER[a["topic"]] > 0 else "Nicht relevant"
            body += "Bereich: Vertiefungen\nArtikel-ID: %s\nBewertung: %s\nBegründung: –\n\n" % (a["id"], vote)
        issues.append({"number": day, "title": "[Morgenzeitung] Sammelbewertung " + date,
                       "body": body, "updated_at": date + "T12:00:00Z"})
        profile, report = learn(profile, issues, editions)
        history.append({"round": day, "top_two": ranking[:2],
                        "positive_top_two": sum(PREFER[t] > 0 for t in ranking[:2]),
                        "ratings": report["ratings"],
                        "signals": len(profile["computed_learning_signals"])})
    return profile, history

class ClosedLoopSimulation(unittest.TestCase):
    def test_learning_improves_ranked_selection_without_real_feedback(self):
        profile, history = simulate()
        self.assertEqual(history[0]["positive_top_two"], 1)
        self.assertEqual(history[-1]["positive_top_two"], 2)
        self.assertEqual(history[-1]["ratings"], 48)
        self.assertEqual(len(profile["computed_learning_signals"]), 5)
        self.assertEqual(len(profile["editorial_review_queue"]), 5)
        self.assertEqual(sum(s.get("scope") == "explicit_topic_family" for s in profile["computed_learning_signals"]), 1)
        self.assertTrue(all(h["ratings"] == h["round"] * 4 for h in history))

    def test_changed_preferences_reverse_signals_after_sufficient_new_votes(self):
        # A strong historical preference must not flip after a single contrary vote.
        from scripts.morgenzeitung_feedback import learn
        editions, issues = {}, []
        for day in range(1, 13):
            date = "2026-12-%02d" % day
            article_id = "%016x" % (9000 + day)
            editions[date] = {"articles": [{"id": article_id, "topic": "KI & Produktivität"}], "headlines": []}
            vote = "Sehr relevant" if day <= 3 else "Nicht relevant"
            issues.append({"number": 100 + day, "title": "[Morgenzeitung] Sammelbewertung " + date,
                           "updated_at": date + "T12:00:00Z",
                           "body": "Ausgabe: %s\nArtikel-ID: %s\nBewertung: %s\nBegründung: –" %
                                   (date, article_id, vote)})
        p = {}
        for n in range(1, 13):
            p, report = learn(p, issues[:n], editions)
            if n == 3:
                self.assertEqual(p["computed_learning_signals"][0]["direction"], "positive")
            if n == 4:
                self.assertEqual(p["computed_learning_signals"][0]["direction"], "positive")
        self.assertEqual(p["computed_learning_signals"][0]["direction"], "negative")
        self.assertEqual(report["ratings"], 12)
        self.assertEqual(p, learn(p, issues, editions)[0])

    def test_test_issue_is_excluded_and_does_not_change_learning(self):
        date = "2026-12-15"
        article_id = "0000000000009999"
        editions = {date: {"articles": [{"id": article_id, "topic": "Industriepolitik"}], "headlines": []}}
        fake = {"number": 999, "title": "[Morgenzeitung] Sammelbewertung " + date,
                "updated_at": date + "T12:00:00Z",
                "body": "Ausgabe: %s\nTEST: true\nArtikel-ID: %s\nBewertung: Nicht relevant\nBegründung: –" % (date, article_id)}
        p, report = learn({}, [fake], editions)
        self.assertEqual(report["ratings"], 0)
        self.assertEqual(p["computed_learning_signals"], [])
        self.assertEqual(p["editorial_review_queue"], [])

if __name__ == "__main__":
    unittest.main()
