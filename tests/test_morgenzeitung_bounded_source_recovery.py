import copy
import unittest

from scripts.morgenzeitung_bounded_source_recovery import recover

DATE = "2026-10-27"


def raw_pool():
    names = ["ORF", "Handelsblatt", "FAZ", "NZZ", "BBC News"]
    return [
        {"id": str(i), "source": names[i % 5], "topic": "Wirtschaft",
         "title": "Original verified economic article " + str(i),
         "source_url": "https://example.org/original-" + str(i),
         "published_at": "2026-10-27T06:00:00Z", "verified": True}
        for i in range(20)
    ]


class BoundedRecoveryTests(unittest.TestCase):
    def test_transient_403_recovers_with_real_evidence_then_separate_preflight(self):
        raw = raw_pool()
        unchanged = copy.deepcopy(raw)
        calls = {}

        def checker(items, date, publisher_dates):
            item = items[0]
            ident = item["id"]
            calls[ident] = calls.get(ident, 0) + 1
            if ident == "2":
                if calls[ident] == 1:
                    raise ValueError("HTTP 403 and official feed temporarily unavailable")
                return {"checked": [{
                    "original_article_http_verified": False,
                    "publisher_feed_verified": True,
                    "publisher_feed_evidence": {
                        "publisher_feed_verified": True,
                        "original_url": item["source_url"],
                        "publication_time": "2026-10-27T06:00:00Z"}}]}
            return {"checked": [{"original_article_http_verified": True}]}

        result = recover(raw, DATE, checker=checker)
        self.assertTrue(result["ready_for_private_capture"])
        self.assertTrue(result["final_preflight"]["preflight_passed"])
        self.assertEqual(result["eligible_count"], 20)
        self.assertEqual(result["retry_counts"]["2"], 1)
        self.assertEqual(result["needs_research"], [])
        self.assertEqual(raw, unchanged)
        self.assertGreaterEqual(calls["2"], 3)  # initial, retry, final preflight

    def test_persistent_403_stops_after_two_retries_and_keeps_healthy_pool(self):
        calls = {}

        def checker(items, date, publisher_dates):
            ident = items[0]["id"]
            calls[ident] = calls.get(ident, 0) + 1
            if ident == "2":
                raise ValueError("HTTP 403 and no identical official publisher feed")
            return {"checked": [{"original_article_http_verified": True}]}

        result = recover(raw_pool(), DATE, checker=checker)
        self.assertTrue(result["ready_for_private_capture"])
        self.assertEqual(result["eligible_count"], 19)
        self.assertEqual(result["retry_counts"]["2"], 2)
        self.assertEqual(calls["2"], 3)
        self.assertEqual(result["needs_research"][0]["id"], "2")

    def test_too_few_verified_never_produces_publishable_pool(self):
        def checker(items, date, publisher_dates):
            if int(items[0]["id"]) < 10:
                raise ValueError("HTTP 403; feed inaccessible")
            return {"checked": [{"original_article_http_verified": True}]}

        result = recover(raw_pool(), DATE, checker=checker)
        self.assertFalse(result["ready_for_private_capture"])
        self.assertEqual(result["eligible"], [])
        self.assertEqual(result["eligible_count"], 10)
        self.assertEqual(len(result["needs_research"]), 10)
        self.assertFalse(result["final_preflight"]["preflight_passed"])

    def test_forged_feed_boolean_never_becomes_verified(self):
        def checker(items, date, publisher_dates):
            if items[0]["id"] == "2":
                return {"checked": [{"original_article_http_verified": False,
                                     "publisher_feed_verified": True}]}
            return {"checked": [{"original_article_http_verified": True}]}

        result = recover(raw_pool(), DATE, checker=checker)
        self.assertNotIn("2", [x["id"] for x in result["eligible"]])
        self.assertEqual(result["retry_counts"]["2"], 2)

    def test_bad_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "max_retries"):
            recover(raw_pool(), DATE, max_retries=3)
        with self.assertRaisesRegex(ValueError, "unique"):
            rows = raw_pool()
            rows[1]["id"] = rows[0]["id"]
            recover(rows, DATE, checker=lambda *a, **kw: {})


if __name__ == "__main__":
    unittest.main()
