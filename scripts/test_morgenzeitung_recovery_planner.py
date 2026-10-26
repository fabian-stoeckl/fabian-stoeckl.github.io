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

    def test_duplicate_original_url_is_not_selected_twice(self):
        with patch("scripts.morgenzeitung_recovery_planner.preflight") as pre:
            pre.return_value = {"ready_count": 1, "blocked": [], "preflight_passed": True,
                                "diversity": {"diversity_passed": True}, "next_action": "capture"}
            repeated = candidate("2")
            repeated["source_url"] = candidate("1")["source_url"]
            result = plan_recovery([candidate("1")], [repeated], "2026-10-26",
                                   minimum=1, checker=fake_checker)
            self.assertTrue(result["recovered"])
            self.assertEqual(len(result["candidates"]), 1)
            self.assertTrue(any("Duplicate" in x["reason"] for x in result["blocked"]))

    def test_access_restricted_and_date_conflict_are_excluded(self):
        def checker(items, date, publisher_dates=True):
            if items[0]["id"] in ("reuters-403", "bbc-date-conflict"):
                raise ValueError("Publisher original unverified or date conflict")
            return {"checked": [{"original_article_http_verified": True}]}
        with patch("scripts.morgenzeitung_recovery_planner.preflight") as pre:
            pre.return_value = {"ready_count": 3, "blocked": [], "preflight_passed": True,
                                "diversity": {"diversity_passed": True}, "next_action": "capture"}
            result = plan_recovery([candidate("reuters-403"), candidate("bbc-date-conflict")],
                                   [candidate("1", "ORF"), candidate("2", "FAZ"),
                                    candidate("3", "AP")], "2026-10-26",
                                   minimum=3, checker=checker)
            self.assertTrue(result["recovered"])
            self.assertEqual(len(result["blocked"]), 2)
            self.assertEqual([x["id"] for x in result["candidates"]], ["1", "2", "3"])

    def test_date_window_blocks_future_article(self):
        future = candidate("future")
        future["published_at"] = "2030-01-01T08:00:00Z"
        result = plan_recovery([future], [], "2026-10-26", minimum=1,
                               checker=fake_checker)
        self.assertFalse(result["recovered"])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["blocked"][0]["id"], "future")

    def test_no_original_url_fails_closed(self):
        item = candidate("missing-url")
        item.pop("source_url")
        with patch("scripts.morgenzeitung_recovery_planner.preflight") as pre:
            result = plan_recovery([item], [], "2026-10-26", minimum=1,
                                   checker=fake_checker)
            self.assertFalse(result["recovered"])
            self.assertTrue(any("Missing canonical" in x["reason"] for x in result["blocked"]))
            pre.assert_not_called()

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            plan_recovery({}, [], "2026-10-26")
        with self.assertRaises(ValueError):
            plan_recovery([], [], "2026-10-26", minimum=0)


if __name__ == "__main__":
    unittest.main()
