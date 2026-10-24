import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from scripts.morgenzeitung_capture_preselection import PrivateRepo


class ConcurrentCaptureTests(unittest.TestCase):
    def setUp(self):
        self.repo = PrivateRepo("test-token")

    def test_same_content_concurrent_create_is_idempotent(self):
        data = b'{"verified":true}'
        with patch.object(self.repo, "read", side_effect=[None, (data, "sha"), (data, "sha")]), patch.object(
            self.repo, "api", side_effect=urllib.error.HTTPError("url", 409, "Conflict", {}, None)
        ):
            self.repo.put_immutable("candidates/test.json", data)

    def test_conflicting_concurrent_create_fails(self):
        with patch.object(self.repo, "read", side_effect=[None, (b"other", "sha")]), patch.object(
            self.repo, "api", side_effect=urllib.error.HTTPError("url", 422, "Conflict", {}, None)
        ):
            with self.assertRaisesRegex(ValueError, "Conflicting concurrent"):
                self.repo.put_immutable("candidates/test.json", b"expected")

    def test_api_retries_transient_503(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        with patch("scripts.morgenzeitung_capture_preselection.urllib.request.urlopen",
                   side_effect=[urllib.error.HTTPError("url",503,"Unavailable",{},None),Response()]) as fetch, patch(
                   "scripts.morgenzeitung_capture_preselection.json.load", return_value={"ok": True}), patch(
                   "scripts.morgenzeitung_capture_preselection.time.sleep"):
            self.assertEqual(self.repo.api("/contents/x"), {"ok": True})
            self.assertEqual(fetch.call_count, 2)

    def test_api_does_not_retry_conflicts(self):
        with patch("scripts.morgenzeitung_capture_preselection.urllib.request.urlopen",
                   side_effect=urllib.error.HTTPError("url",409,"Conflict",{},None)) as fetch:
            with self.assertRaises(urllib.error.HTTPError):
                self.repo.api("/contents/x", "PUT", {"content":"x"})
            self.assertEqual(fetch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
