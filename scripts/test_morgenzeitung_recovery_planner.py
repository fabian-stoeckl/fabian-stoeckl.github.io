"""Regression tests for fail-closed source recovery."""
import unittest
from unittest.mock import patch
from scripts.morgenzeitung_recovery_planner import plan_recovery


def candidate(n, source="A"):
    return {"id": str(n), "source": source, "source_url": "https://example.org/" + str(n),
            "published_at": "2026-10-26T08:00:00Z", "verified": True}


def fake_checker(items, date, publisher_dates=True):
    item = items[0]
    if item["id"] in {"bad", "wrong-date"}:
        raise ValueError("Publisher metadata mismatch")
    return {"checked": [{"original_article_http_verified": True}]}


class RecoveryPlannerTests(unittest.TestCase):
    def test_replaces_invalid_original_with_verified_reserve(self):
        with patch("scripts.morgenzeitung_recovery_planner.preflight") as pre:
            pre.return_value = {"ready_count": 2, "blocked": [], "preflight_passed": True,
                                "diversity": {"diversity_passed": True}, "next_action": "capture"}
            result = plan_recovery([candidate("1"), candidate("bad")], [candidate("2")],
                                   "2026-10-26", minimum=2, checker=fake_checker)
            self.assertTrue(result["recovered"])
            self.assertEqual([x["id"] for x in result["candidates"]], ["1", "2"])
            self.assertEqual(result["blocked"][0]["id"], "bad")

    def test_insufficient_pool_fails_closed(self):
        with patch("scripts.morgenzeitung_recovery_planner.preflight") as pre:
            pre.return_value = {"ready_count": 1, "blocked": [], "preflight_passed": False,
                                "diversity": {"diversity_passed": False}, "next_action": "research"}
            result = plan_recovery([candidate("1")], [], "2026-10-26", minimum=15,
                                   checker=fake_checker)
            self.assertFalse(result["recovered"])
            self.assertEqual(result["candidates"], [])

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            plan_recovery({}, [], "2026-10-26")
        with self.assertRaises(ValueError):
            plan_recovery([], [], "2026-10-26", minimum=0)


if __name__ == "__main__":
    unittest.main()
