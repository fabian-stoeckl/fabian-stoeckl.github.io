"""Isolated multi-edition causal replay; never writes to private production data.

Each iteration creates a new dated edition and a new synthetic issue, relearns
from the full history, and compares the same verified candidate pool with and
without learned preferences. A reversal phase proves the learner can unlearn.
"""
import copy
import unittest
from datetime import date, timedelta

from scripts.morgenzeitung_feedback import learn
from scripts.morgenzeitung_selection_audit import compare

TOPICS = ("Industrie & Rohstoffe", "Industrie & Organisation",
          "KI & Forschung", "Wissenschaft & Bildung",
          "Klima & Energie", "Produktivität & Arbeit")
SOURCES = ("FAZ", "Handelsblatt", "ORF", "SZ", "Die Presse", "Der Standard")

def article(cycle, index):
    return {
        "id": f"{cycle * 1000 + index:016x}",
        "topic": TOPICS[index % len(TOPICS)],
        "source": SOURCES[index % len(SOURCES)],
        "verified": True,
    }

def edition(cycle, day):
    pool = [article(cycle, index) for index in range(24)]
    return {"date": day, "headlines": [], "articles": pool}, pool

def issue(cycle, day, items):
    entries = []
    for item, rating in items:
        entries.extend([
            "Bereich: Vertiefungen",
            f"Artikel-ID: {item['id']}",
            f"Bewertung: {rating}",
            "Begründung: –",
            "",
        ])
    return {
        "number": cycle + 10,
        "title": f"[Morgenzeitung] Sammelbewertung {day}",
        "updated_at": f"{day}T23:00:00Z",
        "body": f"Typ: Sammelbewertung\\nAusgabe: {day}\\n\\n" + "\\n".join(entries),
    }

class MultiCycleCausalReplay(unittest.TestCase):
    def test_36_cycles_learning_reversal_and_idempotence(self):
        profile, issues, editions = {}, [], {}
        trajectory = []
        for cycle in range(36):
            day = (date(2026, 1, 1) + timedelta(days=cycle)).isoformat()
            day_edition, pool = edition(cycle, day)
            editions[day] = day_edition
            # First half rewards industrial topics; second half reverses them.
            # Always rate four explicitly tagged industrial articles each day.
            votes = [(item, "Sehr relevant" if cycle < 18 else "Nicht relevant")
                     for item in pool if item["topic"].startswith("Industrie")][:4]
            issues.append(issue(cycle, day, votes))
            profile, report = learn(profile, issues, editions)
            repeat, repeated_report = learn(copy.deepcopy(profile), issues, editions)
            self.assertEqual(profile, repeat, "Replay must be idempotent")
            self.assertEqual(report, repeated_report)
            self.assertEqual(report["ratings"], 4 * (cycle + 1))
            audit = compare(pool, profile, limit=10, max_per_source=3)
            self.assertFalse(audit["publication_verified"])
            self.assertFalse(audit["editorial_effect_verified"])
            trajectory.append((cycle, report["signals"], audit["selection_changed"],
                               [s["direction"] for s in profile["computed_learning_signals"]
                                if s["topic"] == "Industrie"]))
        # After accumulating positive ratings, preferences alter actual ranking.
        self.assertEqual(trajectory[3][3], ["positive"])
        self.assertTrue(trajectory[3][2])
        # Balanced positive and negative ratings cancel; no unjustified signal.
        self.assertEqual(trajectory[35][3], [])
        # No evidence of publication is ever claimed from synthetic replay.
        self.assertEqual(len(issues), 36)

    def test_independent_negative_training_reorders_verified_pool(self):
        day = "2026-02-01"
        day_edition, pool = edition(100, day)
        negatives = [(item, "Nicht relevant") for item in pool
                     if item["topic"].startswith("Industrie")][:4]
        profile, report = learn({}, [issue(100, day, negatives)], {day: day_edition})
        self.assertEqual(report["ratings"], 4)
        family = [s for s in profile["computed_learning_signals"] if s["topic"] == "Industrie"]
        self.assertEqual(len(family), 1)
        self.assertEqual(family[0]["direction"], "negative")
        audit = compare(pool, profile, limit=10, max_per_source=3)
        self.assertTrue(audit["counterfactual_effect_verified"])
        self.assertFalse(audit["editorial_effect_verified"])

    def test_revised_rating_does_not_double_count(self):
        day = "2026-03-01"
        day_edition, pool = edition(200, day)
        first = issue(200, day, [(pool[0], "Sehr relevant")])
        corrected = issue(201, day, [(pool[0], "Nicht relevant")])
        corrected["updated_at"] = "2026-03-01T23:59:59Z"
        profile, report = learn({}, [first, corrected], {day: day_edition})
        self.assertEqual(report["ratings"], 1)
        evidence = [e for e in profile["topic_evidence"] if e["topic"] == pool[0]["topic"]]
        self.assertEqual(evidence[0]["positive"], 0)
        self.assertEqual(evidence[0]["negative"], 1)

if __name__ == "__main__":
    unittest.main()
