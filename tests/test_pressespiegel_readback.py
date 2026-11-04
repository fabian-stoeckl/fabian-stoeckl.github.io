"""Deterministic tests for public HTTPS readback (no external requests)."""
import io
from datetime import date
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
        self.assets = self.root / "reader"
        self.assets.mkdir()
        (self.assets / "app.js").write_text("console.log('new')")
        (self.assets / "style.css").write_text("body{}")
        self.reader_html = ('<html><title>Pressespiegel</title>'
            '<link rel="stylesheet" href="./style.css?v=test1">'
            '<script src="./app.js?v=test1"></script></html>')
        (self.assets / "index.html").write_text(self.reader_html)
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
            base + "/": self.reader_html.encode(),
            base + "/app.js?v=test1": b"console.log('new')",
            base + "/style.css?v=test1": b"body{}",
        }
    def check_reader(self, base, pages, **kwargs):
        return check(base, self.root, self.opener(pages), assets_root=self.assets, **kwargs)
    def test_matching_live_edition(self):
        base, pages = self.payloads()
        self.assertEqual(self.check_reader(base, pages), "2026-11-04")
    def test_daily_check_accepts_today_in_vienna(self):
        base, pages = self.payloads()
        self.assertEqual(self.check_reader(base, pages,
                               require_today=True, local_today=date(2026, 11, 4)), "2026-11-04")
    def test_daily_check_rejects_stale_date_even_when_site_matches(self):
        base, pages = self.payloads()
        with self.assertRaisesRegex(RuntimeError, "No edition for local Vienna date"):
            self.check_reader(base, pages,
                  require_today=True, local_today=date(2026, 11, 5))

    def test_stale_index_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/data/index.json"] = {"dates": ["2026-11-03"]}
        with self.assertRaisesRegex(RuntimeError, "stale"):
            self.check_reader(base, pages)
    def test_wrong_edition_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/data/2026-11-04.json"] = {**self.issue, "preview": True}
        with self.assertRaisesRegex(RuntimeError, "differs"):
            self.check_reader(base, pages)
    def test_missing_reader_marker_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/"] = b"<html><title>Other page</title></html>"
        with self.assertRaisesRegex(RuntimeError, "marker"):
            self.check_reader(base, pages)

    def test_stale_reader_javascript_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/app.js?v=test1"] = b"console.log('cached old')"
        with self.assertRaisesRegex(RuntimeError, "asset differs"):
            self.check_reader(base, pages)

    def test_stale_html_cache_version_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/"] = self.reader_html.replace("app.js?v=test1", "app.js?v=older").encode()
        with self.assertRaisesRegex(RuntimeError, "asset version is stale"):
            self.check_reader(base, pages)

    def test_stale_stylesheet_is_failure(self):
        base, pages = self.payloads()
        pages[base + "/style.css?v=test1"] = b"old-style{}"
        with self.assertRaisesRegex(RuntimeError, "asset differs"):
            self.check_reader(base, pages)

if __name__ == "__main__":
    unittest.main()
