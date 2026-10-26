"""Explicit event identities prevent repeated publisher coverage in one edition."""
import unittest
from scripts.morgenzeitung_editorial import select_articles
from scripts.morgenzeitung_selection_audit import compare


def item(identifier, event, topic="Wirtschaft & Fiskalpolitik", source="ORF"):
    return {"id": identifier, "event": event, "topic": topic,
            "source": source, "verified": True}


class EventDedupTests(unittest.TestCase):
    def test_duplicate_event_skipped_and_replaced(self):
        pool = [item("a", "brazil", source="ORF"),
                item("b", "brazil", source="The Guardian"),
                item("c", "serbia", source="WirtschaftsWoche"),
                item("d", "eu-budget", source="ORF")]
        chosen, audit = select_articles(pool, {}, limit=3)
        self.assertEqual([x["id"] for x in chosen], ["a", "c", "d"])
        self.assertEqual(len(audit), 3)

    def test_missing_and_unique_legacy_urls_are_unchanged(self):
        pool = [item("a", "https://one.example/a"),
                item("b", "https://two.example/b"),
                item("c", None)]
        chosen, _ = select_articles(pool, {}, limit=3)
        self.assertEqual([x["id"] for x in chosen], ["a", "b", "c"])

    def test_learning_can_change_membership_without_duplicate_event(self):
        pool = [item(str(i), "neutral-" + str(i), source="ORF") for i in range(10)]
        pool += [item("industry", "mercedes", topic="Industrie & Innovation",
                      source="WirtschaftsWoche")]
        profile = {"computed_learning_signals": [{
            "topic": "Industrie", "direction": "positive", "confidence": "preliminary"
        }]}
        result = compare(pool, profile, limit=10, max_per_source=10)
        self.assertIn("industry", result["newly_selected_ids"])
        self.assertTrue(result["counterfactual_effect_verified"])


if __name__ == "__main__":
    unittest.main()
