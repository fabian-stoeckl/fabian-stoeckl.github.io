"""Isolated 26 Oct v6 preview checks; never change the regular edition or ETF."""
import json
import unittest
from datetime import datetime
from pathlib import Path

from scripts.check_morgenzeitung import validate

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "Privat" / "Pressespiegel"


class V6PreviewContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.edition = json.loads((BASE / "previews" / "2026-10-26-v6.json").read_text(encoding="utf-8"))
        cls.index = json.loads((BASE / "data" / "index.json").read_text(encoding="utf-8"))

    def test_preview_schema_and_counts(self):
        self.assertTrue(validate(self.edition))
        self.assertTrue(self.edition["preview"])
        self.assertEqual(self.edition["date"], "2026-10-26")
        self.assertEqual(self.edition["snapshot_version"], "v6")
        self.assertEqual(len(self.edition["articles"]), 10)
        self.assertEqual(len(self.edition["headlines"]), 15)

    def test_chronology_and_unique_events(self):
        start = datetime.fromisoformat(self.edition["window_start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(self.edition["window_end"].replace("Z", "+00:00"))
        self.assertLess(start, end)
        events = set()
        for item in self.edition["articles"] + self.edition["headlines"]:
            stamp = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
            self.assertLessEqual(start, stamp, item["title"])
            self.assertLessEqual(stamp, end, item["title"])
            self.assertNotIn(item["event"], events, item["title"])
            events.add(item["event"])

    def test_isolation_and_private_data(self):
        self.assertIn("2026-10-26", self.index["dates"])
        self.assertEqual(self.index["dates"], sorted(self.index["dates"], reverse=True))
        self.assertEqual(len(self.index["dates"]), len(set(self.index["dates"])))
        self.assertIn(json.loads((BASE / "data" / "2026-10-26.json").read_text())["snapshot_version"], ("v2", "v7", "v8"))
        self.assertEqual(json.loads((BASE / "previews" / "2026-10-26-v3.json").read_text())["snapshot_version"], "v3")
        html = (BASE / "previews" / "2026-10-26-v6.html").read_text(encoding="utf-8")
        self.assertIn("2026-10-26-v6.json", html)
        self.assertIn("keine reguläre tagesausgabe", html.lower())
        payload = json.dumps(self.edition, ensure_ascii=False).lower()
        self.assertNotIn("processed_feedback", payload)
        self.assertNotIn("feedback_observations", payload)
        self.assertNotIn("private_snapshot", payload)


if __name__ == "__main__":
    unittest.main()
