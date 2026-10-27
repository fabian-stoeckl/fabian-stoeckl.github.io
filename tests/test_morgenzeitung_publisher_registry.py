"""Fail-closed, publisher-independent registry regression tests."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.morgenzeitung_official_feeds import FEEDS, load_publisher_registry, verify_official_feed


class PublisherRegistryTests(unittest.TestCase):
    def test_registry_contains_requested_publishers(self):
        self.assertIn("Bloomberg", FEEDS)
        self.assertIn("POLITICO Europe", FEEDS)
        self.assertIn("Der Standard", FEEDS)
        self.assertGreaterEqual(len(FEEDS["Bloomberg"][0]), 3)
        self.assertGreaterEqual(len(FEEDS["Der Standard"][0]), 3)
        self.assertEqual(FEEDS["POLITICO Europe"][0], ())

    def test_no_false_politico_us_evidence(self):
        with self.assertRaises(ValueError):
            verify_official_feed({"source": "POLITICO Europe",
                "source_url": "https://www.politico.eu/article/test-story/",
                "title": "An example story with a real title",
                "published_at": "2026-10-27T10:00:00+00:00"})

    def test_reject_external_feed(self):
        data = {"schema_version": 1, "publishers": {"New Source": {
            "article_hosts": ["publisher.example"],
            "feeds": ["https://evil.example/rss"]}}}
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "registry.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_publisher_registry(p)

    def test_new_publisher_without_code_change(self):
        data = {"schema_version": 1, "publishers": {"New Source": {
            "article_hosts": ["publisher.example"],
            "feeds": ["https://publisher.example/rss"]}}}
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "registry.json"
            p.write_text(json.dumps(data), encoding="utf-8")
            self.assertIn("New Source", load_publisher_registry(p))


if __name__ == "__main__":
    unittest.main()
