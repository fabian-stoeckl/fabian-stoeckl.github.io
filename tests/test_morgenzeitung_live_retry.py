import io
import json
import unittest
import urllib.error
from unittest.mock import patch
from scripts.morgenzeitung_publication_audit import live_json, PUBLIC_BASE


class Response(io.BytesIO):
    def __init__(self, data, url):
        super().__init__(json.dumps(data).encode())
        self.url = url
    def geturl(self):
        return self.url


class RetryTests(unittest.TestCase):
    @patch("scripts.morgenzeitung_publication_audit.urllib.request.urlopen")
    def test_transient_404_then_success(self, urlopen):
        urlopen.side_effect = [
            urllib.error.HTTPError(PUBLIC_BASE + "index.json", 404, "not deployed", {}, None),
            Response({"dates": ["2026-10-24"]}, PUBLIC_BASE + "index.json"),
        ]
        waits = []
        self.assertEqual(live_json("index.json", delay=1, sleep=waits.append)["dates"],
                         ["2026-10-24"])
        self.assertEqual(waits, [1])

    @patch("scripts.morgenzeitung_publication_audit.urllib.request.urlopen")
    def test_permission_denied_not_retried(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(PUBLIC_BASE + "index.json", 403, "denied", {}, None)
        with self.assertRaises(urllib.error.HTTPError):
            live_json("index.json", sleep=lambda _: None)
        self.assertEqual(urlopen.call_count, 1)

    @patch("scripts.morgenzeitung_publication_audit.urllib.request.urlopen")
    def test_redirect_not_retried(self, urlopen):
        urlopen.return_value = Response({}, "https://example.org/")
        with self.assertRaisesRegex(ValueError, "redirect"):
            live_json("index.json", sleep=lambda _: None)
        self.assertEqual(urlopen.call_count, 1)

    def test_rejects_arbitrary_path(self):
        with self.assertRaises(ValueError):
            live_json("../private.json")


if __name__ == "__main__":
    unittest.main()
