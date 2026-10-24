import unittest
from scripts.morgenzeitung_publication_audit import verify_live_with_retry


class StalePagesRetryTests(unittest.TestCase):
    def setUp(self):
        self.date = "2026-10-24"
        self.audit = {"selected_ids": ["a"], "counterfactual_effect_verified": False}

    def test_stale_index_recovers(self):
        calls = []
        def fetch(name):
            calls.append(name)
            if name == "index.json":
                return {"dates": [] if calls.count("index.json") == 1 else [self.date]}
            return {"date": self.date, "articles": [{"id": "a"}]}
        result = verify_live_with_retry(self.audit, self.date, attempts=2, delay=0,
                                        fetch=fetch, sleep=lambda _: None)
        self.assertTrue(result["publication_verified"])
        self.assertEqual(calls.count("index.json"), 2)

    def test_stale_edition_recovers(self):
        calls = []
        def fetch(name):
            calls.append(name)
            if name == "index.json":
                return {"dates": [self.date]}
            return {"date": self.date, "articles": [{"id": "old" if calls.count(name) == 1 else "a"}]}
        result = verify_live_with_retry(self.audit, self.date, attempts=2, delay=0,
                                        fetch=fetch, sleep=lambda _: None)
        self.assertTrue(result["publication_verified"])

    def test_persistent_mismatch_fails_closed(self):
        def fetch(name):
            if name == "index.json":
                return {"dates": [self.date]}
            return {"date": self.date, "articles": [{"id": "wrong"}]}
        with self.assertRaisesRegex(ValueError, "differ"):
            verify_live_with_retry(self.audit, self.date, attempts=2, delay=0,
                                   fetch=fetch, sleep=lambda _: None)

    def test_invalid_preview_is_not_retried(self):
        calls = []
        def fetch(name):
            calls.append(name)
            return {"dates": [self.date]} if name == "index.json" else {
                "date": self.date, "preview": True, "articles": [{"id": "a"}]}
        with self.assertRaisesRegex(ValueError, "preview"):
            verify_live_with_retry(self.audit, self.date, attempts=3, delay=0,
                                   fetch=fetch, sleep=lambda _: None)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
