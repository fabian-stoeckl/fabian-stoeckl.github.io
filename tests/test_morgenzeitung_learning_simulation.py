"""Isolated multi-cycle simulation: never submits synthetic votes to GitHub."""
import unittest
from scripts.morgenzeitung_feedback import learn

TOPICS = ("KI & Produktivität", "Industriepolitik", "Promi-News", "Juristische Randdetails")
PREFER = {TOPICS[0]: 1, TOPICS[1]: 1, TOPICS[2]: -1, TOPICS[3]: -1}

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
        body = "Ausgabe: %s\\n" % date
        for a in articles:
            vote = "Sehr relevant" if PREFER[a["topic"]] > 0 else "Nicht relevant"
            body += "Bereich: Vertiefungen\\nArtikel-ID: %s\\nBewertung: %s\\nBegründung: –\\n\\n" % (a["id"], vote)
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
        self.assertEqual(len(profile["computed_learning_signals"]), 4)
        self.assertEqual(len(profile["editorial_review_queue"]), 4)
        self.assertTrue(all(h["ratings"] == h["round"] * 4 for h in history))

if __name__ == "__main__":
    unittest.main()
