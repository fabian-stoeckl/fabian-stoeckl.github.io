import json
import unittest
from scripts.morgenzeitung_editorial import select_articles
from scripts.morgenzeitung_acceptance_report import acceptance
from scripts.morgenzeitung_capture_preselection import verify_existing


class Repo:
    def __init__(self):
        self.data = {
            "candidates/2026-10-25.json": json.dumps([{"id":"a","topic":"Industrie","source":"Handelsblatt","verified":True}]).encode(),
            "snapshots/2026-10-25-profile.json": b'{}',
            "snapshots/2026-10-25-issues.json": b'[]',
            "snapshots/2026-10-25-selection-parameters.json": b'{"limit":true,"max_per_source":4}',
        }

    def read(self, path):
        return (self.data[path], "sha") if path in self.data else None


class HardeningTests(unittest.TestCase):
    def test_boolean_snapshot_limit_rejected(self):
        with self.assertRaises(ValueError):
            verify_existing(Repo(), "2026-10-25")

    def test_zero_source_cap_rejected(self):
        with self.assertRaises(ValueError):
            select_articles([{"id":"a","topic":"Industrie","source":"Handelsblatt","verified":True}], {}, max_per_source=0)

    def test_boolean_limit_rejected(self):
        with self.assertRaises(ValueError):
            select_articles([], {}, limit=True)

    def test_any_explicit_fail_propagates(self):
        result = acceptance({"statuses":{"feedback":"FAIL"}})
        self.assertEqual(result["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
