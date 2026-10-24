import unittest
import urllib.error
from scripts.morgenzeitung_live_source_check import check_date, check_http, check_candidates


class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): pass


class Opener:
    def __init__(self, status): self.status = status
    def open(self, req, timeout):
        if self.status != 200:
            raise urllib.error.HTTPError(req.full_url, self.status, "test", {}, None)
        return Response()


class LiveSourceTests(unittest.TestCase):
    def test_freshness(self):
        self.assertTrue(check_date("2026-10-24T10:00:00Z", "2026-10-24"))
        for value in ("2026-10-19T00:00:00Z", "2026-10-27T00:00:00Z",
                      "2026-10-24T10:00:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                check_date(value, "2026-10-24")

    def test_accessible(self):
        self.assertEqual(check_http("https://example.org/story", Opener(200))["status"], 200)

    def test_paywall_not_treated_as_body_verified(self):
        result = check_http("https://example.org/story", Opener(403))
        self.assertTrue(result["paywall_or_access_restricted"])

    def test_dead_and_redirect_sources_fail(self):
        for status in (301, 302, 404, 500):
            with self.subTest(status=status), self.assertRaises(ValueError):
                check_http("https://example.org/story", Opener(status))

    def test_candidate_aggregate(self):
        pool = [{"id": "a", "source_url": "https://example.org/story",
                 "published_at": "2026-10-24T06:00:00Z"}]
        result = check_candidates(pool, "2026-10-24", Opener(200))
        self.assertTrue(result["live_source_checks_passed"])
        self.assertEqual(len(result["checked"]), 1)


if __name__ == "__main__":
    unittest.main()
