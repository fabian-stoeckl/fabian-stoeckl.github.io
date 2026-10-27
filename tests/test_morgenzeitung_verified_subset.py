"""Regression tests for optional verified-subset preflight."""
import unittest
from unittest.mock import patch
from scripts.morgenzeitung_source_preflight import preflight
from scripts.morgenzeitung_candidate_triage import triage


class VerifiedSubsetTests(unittest.TestCase):
    def setUp(self):
        self.date = "2026-10-27"
        self.pool = [
            {"id": str(i), "source": ["A", "B", "C"][i % 3],
             "source_url": f"https://example.org/story/{i}",
             "published_at": "2026-10-27T06:00:00+00:00",
             "verified": True}
            for i in range(6)
        ]

    def checker(self, candidates, date, publisher_dates=True):
        item = candidates[0]
        return {"checked": [{
            "original_article_http_verified": item["id"] != "5",
            "publisher_feed_verified": False,
        }]}

    def test_partial_passes_only_verified_subset(self):
        with patch("scripts.morgenzeitung_source_preflight.check_date", return_value="ok"):
            result = preflight(self.pool, self.date, minimum=5,
                               checker=self.checker, allow_partial=True)
        self.assertTrue(result["preflight_passed"])
        self.assertEqual(result["blocked_count"], 1)
        self.assertEqual([x["id"] for x in result["verified_candidates"]],
                         ["0", "1", "2", "3", "4"])

    def test_default_remains_strict(self):
        with patch("scripts.morgenzeitung_source_preflight.check_date", return_value="ok"):
            result = preflight(self.pool, self.date, minimum=5,
                               checker=self.checker)
        self.assertFalse(result["preflight_passed"])

    def test_unverified_flag_is_not_accepted(self):
        self.pool[0]["verified"] = False
        with patch("scripts.morgenzeitung_source_preflight.check_date", return_value="ok"):
            result = preflight(self.pool, self.date, minimum=5,
                               checker=self.checker, allow_partial=True)
        self.assertFalse(result["preflight_passed"])

    def test_editorial_mode_uses_discovery_not_http(self):
        for item in self.pool:
            item["discovery_evidence"] = {
                "method": "search_result",
                "reference": "https://example.org/search/article",
            }
            item["title"] = "A real editorial headline"
        with patch("scripts.morgenzeitung_source_preflight.check_date", return_value="ok"):
            result = preflight(self.pool, self.date, minimum=5,
                               checker=lambda *a, **kw: self.fail("HTTP checker called"),
                               allow_partial=True, editorial_mode=True)
        self.assertTrue(result["preflight_passed"])
        self.assertEqual(result["ready_count"], 6)

    def test_editorial_mode_rejects_missing_discovery(self):
        for item in self.pool:
            item["title"] = "A real editorial headline"
        with patch("scripts.morgenzeitung_source_preflight.check_date", return_value="ok"):
            result = preflight(self.pool, self.date, minimum=1,
                               checker=lambda *a, **kw: self.fail("HTTP checker called"),
                               allow_partial=True, editorial_mode=True)
        self.assertFalse(result["preflight_passed"])

    def test_no_link_tests_preserves_candidates_without_network(self):
        for item in self.pool:
            item["title"] = "A relevant article"
        with patch("scripts.morgenzeitung_source_preflight.check_date",
                   side_effect=AssertionError("date gate called")):
            result = triage(self.pool, self.date, minimum=15,
                            no_link_tests=True,
                            checker=lambda *a, **kw: self.fail("Network checker called"))
        self.assertTrue(result["ready_for_final_preflight"])
        self.assertEqual(result["eligible_count"], 6)

    def test_triage_editorial_mode_without_network(self):
        for item in self.pool:
            item["title"] = "An actual editorial headline"
            item["discovery_evidence"] = {
                "method": "publisher_page",
                "reference": "https://example.org/news",
            }
        with patch("scripts.morgenzeitung_source_preflight.check_date", return_value="ok"):
            result = triage(self.pool, self.date, minimum=5,
                            editorial_mode=True,
                            checker=lambda *a, **kw: self.fail("Network checker called"))
        self.assertTrue(result["ready_for_final_preflight"])
        self.assertEqual(result["eligible_count"], 6)

    def test_unsubstantiated_feed_flag_is_not_accepted(self):
        def forged(candidates, date, publisher_dates=True):
            return {"checked": [{
                "original_article_http_verified": False,
                "publisher_feed_verified": True,
            }]}
        with patch("scripts.morgenzeitung_source_preflight.check_date", return_value="ok"):
            result = preflight(self.pool, self.date, minimum=1,
                               checker=forged, allow_partial=True)
        self.assertFalse(result["preflight_passed"])


if __name__ == "__main__":
    unittest.main()
