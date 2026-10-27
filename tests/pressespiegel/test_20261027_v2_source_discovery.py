"""Regression: 27 Oct v2 preserves owner feedback and exposes new-source trials."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class NewSourceTrialRegression(unittest.TestCase):
    def test_public_source_trial_and_existing_rated_ids(self):
        edition = json.loads((ROOT / "Privat/Pressespiegel/data/2026-10-27.json").read_text())
        self.assertEqual(edition["snapshot_version"], "v2")
        self.assertEqual(len(edition["articles"]), 15)
        self.assertEqual(len(edition["headlines"]), 19)
        feature_ids = {item["id"] for item in edition["articles"]}
        news_ids = {item["id"] for item in edition["headlines"]}
        self.assertTrue({
            "27a0000000000003", "27a000000000000d", "27a0000000000001",
            "27a0000000000002", "27a0000000000005", "27a0000000000007",
            "27a0000000000008", "27a000000000000a", "27a000000000000b",
            "27a000000000000f"
        }.issubset(feature_ids))
        self.assertTrue({
            "27b0000000000001", "27b0000000000002", "27b0000000000003",
            "27b0000000000004", "27b0000000000006", "27b0000000000007",
            "27b0000000000008", "27b0000000000009", "27b000000000000a",
            "27b000000000000b", "27b000000000000c", "27b000000000000d",
            "27b000000000000e", "27b000000000000f", "27b0000000000010",
            "27b0000000000013"
        }.issubset(news_ids))
        self.assertEqual(len(feature_ids | news_ids), 34)
        trials = edition["new_sources"]
        self.assertEqual(len(trials), 1)
        self.assertEqual(trials[0]["name"], "Le Monde")
        self.assertTrue(trials[0]["example_url"].startswith("https://www.lemonde.fr/"))
        self.assertIn("Testquelle", trials[0]["why"])

    def test_trial_ui_is_optional_and_uses_safe_links(self):
        html = (ROOT / "Privat/Pressespiegel/index.html").read_text()
        js = (ROOT / "Privat/Pressespiegel/app.js").read_text()
        self.assertIn('id="new-sources"', html)
        self.assertIn("discovery.hidden=trials.length===0", js)
        self.assertIn("link(source.name,source.example_url)", js)
        self.assertNotIn("discovery.innerHTML", js)


if __name__ == "__main__":
    unittest.main()
