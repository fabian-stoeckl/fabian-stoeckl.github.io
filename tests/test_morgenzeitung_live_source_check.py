import unittest
import datetime as dt
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

    def test_future_today_is_rejected_at_morning_publication(self):
        morning = dt.datetime(2026, 10, 24, 6, 45, tzinfo=dt.timezone.utc)
        with self.assertRaisesRegex(ValueError, "outside edition review window"):
            check_date("2026-10-24T15:00:00Z", "2026-10-24", as_of=morning)
        self.assertTrue(check_date("2026-10-24T06:47:00Z", "2026-10-24", as_of=morning))
        with self.assertRaises(ValueError):
            check_date("2026-10-24T06:51:00Z", "2026-10-24", as_of=morning)

    def test_naive_verification_clock_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Verification time needs timezone"):
            check_date("2026-10-24T06:00:00Z", "2026-10-24",
                       as_of=dt.datetime(2026, 10, 24, 7))

    def test_accessible(self):
        self.assertEqual(check_http("https://example.org/story", Opener(200))["status"], 200)

    def test_paywall_not_treated_as_body_verified(self):
        for status in (401, 402, 403):
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "existence unverified"):
                check_http("https://example.org/story", Opener(status))

    def test_dead_and_redirect_sources_fail(self):
        for status in (204, 301, 302, 404, 500):
            with self.subTest(status=status), self.assertRaises(ValueError):
                check_http("https://example.org/story", Opener(status))

    def test_head_not_allowed_falls_back_to_get(self):
        class HeadBlocked:
            methods = []
            def open(self, req, timeout):
                self.methods.append(req.get_method())
                if req.get_method() == "HEAD":
                    raise urllib.error.HTTPError(req.full_url, 405, "no HEAD", {}, None)
                self.assert_range = req.get_header("Range")
                return Response()
        opener = HeadBlocked()
        result = check_http("https://example.org/story", opener)
        self.assertEqual(opener.methods, ["HEAD", "GET"])
        self.assertEqual(opener.assert_range, "bytes=0-0")
        self.assertEqual(result["method"], "GET")

    def test_head_fallback_does_not_accept_paywall(self):
        class Blocked:
            def open(self, req, timeout):
                code = 501 if req.get_method() == "HEAD" else 403
                raise urllib.error.HTTPError(req.full_url, code, "blocked", {}, None)
        with self.assertRaisesRegex(ValueError, "existence unverified"):
            check_http("https://example.org/story", Blocked())

    def test_transient_http_recovery(self):
        class Flaky:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                if self.calls < 3:
                    raise urllib.error.HTTPError(req.full_url, 503, "busy", {}, None)
                return Response()
        opener = Flaky()
        delays = []
        result = check_http("https://example.org/story", opener, sleep=delays.append)
        self.assertEqual(result["status"], 200)
        self.assertEqual(opener.calls, 3)
        self.assertEqual(delays, [1, 2])

    def test_persistent_transient_failure(self):
        delays = []
        with self.assertRaises(ValueError):
            check_http("https://example.org/story", Opener(503), sleep=delays.append)
        self.assertEqual(delays, [1, 2])

    def test_network_recovery(self):
        class Flaky:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                if self.calls == 1:
                    raise urllib.error.URLError("temporary")
                return Response()
        self.assertEqual(check_http("https://example.org/story", Flaky(),
                                    sleep=lambda _: None)["status"], 200)

    def test_permanent_error_no_retry(self):
        class Counting:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                raise urllib.error.HTTPError(req.full_url, 404, "missing", {}, None)
        opener = Counting()
        with self.assertRaises(ValueError):
            check_http("https://example.org/story", opener, sleep=lambda _: None)
        self.assertEqual(opener.calls, 1)

    def test_candidate_aggregate(self):
        pool = [{"id": "a", "source_url": "https://example.org/story",
                 "published_at": "2026-10-24T06:00:00Z"}]
        result = check_candidates(pool, "2026-10-24", Opener(200))
        self.assertTrue(result["live_source_checks_passed"])
        self.assertEqual(len(result["checked"]), 1)


if __name__ == "__main__":
    unittest.main()
