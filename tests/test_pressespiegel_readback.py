"""Deterministic tests for public HTTPS readback (no external requests)."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from scripts.check_pressespiegel_live import check

class Response(io.BytesIO):
    status = 200
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()

class ReadbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.issue = {"date": "2026-11-04", "preview": False, "articles": [], "headlines": [{"id": "abcd"}]}
        self.index = {"dates": ["2026-11-04"]}
        (self.root / "index.json").write_text(json.dumps(self.index))
        (self.root / "2026-11-04.json").write_text(json.dumps(self.issue))
    def tearDown(self):
        self.tmp.cleanup()
    def opener(self, payloads):
        def open_request(request, timeout=12):
            url = request.full_url
            payload = payloads[url]
            return Response(payload if isinstance(payload, bytes) else json.dumps(payload).encode())
        return open_request
    def payloads(self):
        base = "https://test.example/Privat/Pressespiegel"
        return base, {
            base + "/data/index.json": self.index,
            base + "/data/2026-11-04.json": self.issue,
            base + "/": b"<html><title>Pressespiegel</title></html>"
        }
    def test_matching_live_edition(self):
        base, pages = self.payloads()
        self.assertEqual(check(base, self.root, self.opener(pages)), "2026-11-04")
    def test_stale_index_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/data/index.json"] = {"dates": ["2026-11-03"]}
        with self.assertRaisesRegex(RuntimeError, "stale"):
            check(base, self.root, self.opener(pages))
    def test_wrong_edition_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/data/2026-11-04.json"] = {**self.issue, "preview": True}
        with self.assertRaisesRegex(RuntimeError, "differs"):
            check(base, self.root, self.opener(pages))
    def test_missing_reader_marker_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/"] = b"<html><title>Other page</title></html>"
        with self.assertRaisesRegex(RuntimeError, "marker"):
            check(base, self.root, self.opener(pages))

if __name__ == "__main__":
    unittest.main()
