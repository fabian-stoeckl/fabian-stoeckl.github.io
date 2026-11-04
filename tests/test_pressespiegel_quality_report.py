"""Check source-diversity advisory signals within editorial sections."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pressespiegel_quality_report import review


class QualitySignals(unittest.TestCase):
    def test_dominant_deep_dive_source_detected_even_if_total_mix_diverse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.json").write_text(json.dumps({"dates": ["2026-11-04"]}))
            issue = {
                "date": "2026-11-04", "preview": False,
                "articles": [{"source": "Research Outlet"} for _ in range(5)] +
                            [{"source": "Another Source"} for _ in range(2)],
                "headlines": [{"source": f"News Source {n}"} for n in range(9)],
            }
            (root / "2026-11-04.json").write_text(json.dumps(issue))
            text = review(root)
            self.assertIn("Vertiefungen: 5/7 pieces from Research Outlet", text)
            self.assertNotIn("All articles draw from one publication", text)

    def test_two_article_sample_does_not_trigger_false_diversity_alarm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.json").write_text(json.dumps({"dates": ["2026-11-04"]}))
            issue = {"date": "2026-11-04", "preview": False,
                     "articles": [{"source": "One"}, {"source": "One"}],
                     "headlines": [{"source": "News A"}, {"source": "News B"}]}
            (root / "2026-11-04.json").write_text(json.dumps(issue))
            self.assertNotIn("Vertiefungen: 2/2", review(root))


if __name__ == "__main__":
    unittest.main()
