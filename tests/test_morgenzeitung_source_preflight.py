import unittest
from scripts.morgenzeitung_source_preflight import preflight


def candidates():
    return [{"id": str(i), "source": ["ORF", "Reuters", "Handelsblatt", "AP"][i % 4],
             "source_url": "https://example.com/" + str(i),
             "published_at": "2026-10-26T06:00:00+00:00", "verified": True} for i in range(20)]


class PreflightTests(unittest.TestCase):
    def test_diverse_pool_passes_with_independent_evidence(self):
        def checker(items, date, publisher_dates):
            return {"checked": [{"original_article_http_verified": True}]}
        result = preflight(candidates(), "2026-10-26", checker=checker)
        self.assertTrue(result["preflight_passed"])
        self.assertEqual(result["ready_count"], 20)

    def test_reuters_401_requires_more_research(self):
        def checker(items, date, publisher_dates):
            if items[0]["source"] == "Reuters":
                raise ValueError("Publisher access restricted (HTTP 401)")
            return {"checked": [{"original_article_http_verified": True}]}
        result = preflight(candidates(), "2026-10-26", checker=checker)
        self.assertEqual(result["ready_count"], 15)
        self.assertEqual(result["blocked_count"], 5)
        self.assertFalse(result["preflight_passed"], "A pool with 15 verified and 5 blocked must never be archived")
        self.assertTrue(all("401" in x["reason"] for x in result["blocked"]))
        self.assertNotIn("Reuters", [x["source"] for x in result["blocked"] if "401" not in x["reason"]])

    def test_reuters_dominance_is_not_ready(self):
        pool = candidates()
        for x in pool[:18]:
            x["source"] = "Reuters"
        def checker(items, date, publisher_dates):
            return {"checked": [{"original_article_http_verified": True}]}
        result = preflight(pool, "2026-10-26", checker=checker)
        self.assertFalse(result["preflight_passed"])

    def test_future_dated_article_is_blocked(self):
        pool = candidates()
        pool[0]["published_at"] = "2026-11-30T06:00:00+00:00"
        def checker(items, date, publisher_dates):
            return {"checked": [{"original_article_http_verified": True}]}
        result = preflight(pool, "2026-10-26", checker=checker)
        self.assertEqual(result["blocked_count"], 1)
        self.assertFalse(result["preflight_passed"], "Even one future-dated candidate blocks full-pool capture")
        self.assertIn("date", result["blocked"][0]["reason"].lower())

    def test_consent_wall_is_not_pass(self):
        def checker(items, date, publisher_dates):
            return {"checked": [{"original_article_http_verified": False}]}
        result = preflight(candidates(), "2026-10-26", checker=checker)
        self.assertFalse(result["preflight_passed"])
        self.assertEqual(result["blocked_count"], 20)


if __name__ == "__main__":
    unittest.main()
