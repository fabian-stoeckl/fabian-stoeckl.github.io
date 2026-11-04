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
            self.assertIn("2026-11-04, Vertiefungen: 5/7 from Research Outlet", text)
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

    def test_teaser_heavy_features_visible_even_when_news_well_sourced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.json").write_text(json.dumps({"dates": ["2026-11-04"]}))
            issue = {"date": "2026-11-04", "preview": False,
                "articles": [{"source": f"Source {n}", "evidence_level": "teaser"} for n in range(6)] +
                            [{"source": "Deep read", "evidence_level": "read"}],
                "headlines": [{"source": f"News {n}", "evidence_level": "read"} for n in range(9)]}
            (root / "2026-11-04.json").write_text(json.dumps(issue))
            report = review(root)
            self.assertIn("Vertiefungen: 6/7 rely on headline, teaser", report)
            self.assertNotIn("Heute wichtig: 9/9 rely on headline", report)

    def test_outlet_family_variants_are_counted_together_as_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.json").write_text(json.dumps({"dates": ["2026-11-04"]}))
            issue = {"date": "2026-11-04", "preview": False,
                "articles": [{"source": f"Unique {n}", "evidence_level": "read"} for n in range(5)],
                "headlines": [{"source": source, "evidence_level": "read"} for source in
                              ["ORF", "ORF / APA", "ORF / Agenturen", "ORF Science", "ORF / Redaktion", "Reuters"]]}
            (root / "2026-11-04.json").write_text(json.dumps(issue))
            report = review(root)
            self.assertIn("Heute wichtig: 5/6 from ORF", report)

    def test_detects_back_to_back_source_dominance_shift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dates = ["2026-11-04", "2026-11-03"]
            (root / "index.json").write_text(json.dumps({"dates": dates}))
            for date, main in [("2026-11-03", "The Guardian"), ("2026-11-04", "Handelsblatt")]:
                issue = {"date": date, "preview": False,
                    "articles": [{"source": main, "evidence_level": "read"} for _ in range(6)] +
                                [{"source": "Reuters", "evidence_level": "read"}],
                    "headlines": [{"source": f"Independent {n}", "region": "International",
                                   "evidence_level": "read"} for n in range(9)]}
                (root / (date + ".json")).write_text(json.dumps(issue))
            report = review(root)
            self.assertIn("dominant outlet changed from The Guardian", report)
            self.assertIn("to Handelsblatt", report)

    def test_discoveries_not_falsely_expected_before_implementation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            days = ["2026-11-04", "2026-11-03", "2026-11-02", "2026-11-01", "2026-10-31"]
            (root / "index.json").write_text(json.dumps({"dates": days}))
            for date in days:
                ed = {"date": date, "preview": False,
                      "articles": [{"source": "A", "evidence_level": "read"}],
                      "headlines": [{"source": "B", "region": "Österreich", "evidence_level": "read"}]}
                (root / (date + ".json")).write_text(json.dumps(ed))
            self.assertNotIn("Discovery has been empty", review(root))

    def test_ai_clustering_hidden_by_unique_topic_titles_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.json").write_text(json.dumps({"dates": ["2026-11-03"]}))
            issue = {"date": "2026-11-03", "preview": False,
                "articles": [{"source": f"Independent outlet {i}", "evidence_level": "read",
                              "topic": topic} for i, topic in enumerate([
                    "KI im öffentlichen Sektor", "Technologische Souveränität",
                    "Produktivität und Energiepreise", "KI und Bürgerrechte",
                    "Migration und KI", "Österreichische Unternehmen und Osteuropa",
                    "KI und europäische Wettbewerbsfähigkeit", "KI-Governance und Europa",
                    "KI und Energieindustrie",
                ])],
                "headlines": [{"source": "News", "evidence_level": "read", "region": "Österreich"}]}
            (root / "2026-11-03.json").write_text(json.dumps(issue))
            output = review(root)
            self.assertIn("broad topic label 'ki' occurs in 6/9", output)
            self.assertNotIn("from Independent outlet", output)

    def test_discovery_gaps_cannot_break_detection_of_outlet_swings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            days = [f"2026-11-{day:02}" for day in range(5, 10)][::-1]
            (root / "index.json").write_text(json.dumps({"dates": days}))
            for index, day in enumerate(reversed(days)):
                source = "Handelsblatt" if index % 2 else "The Guardian"
                issue = {"date": day, "preview": False,
                    "articles": [{"source": source, "evidence_level": "read",
                                  "topic": "Different subject"} for _ in range(6)] +
                                [{"source": "Another publisher", "evidence_level": "read"}],
                    "headlines": [{"source": "News", "evidence_level": "read",
                                   "region": "Österreich"}]}
                (root / (day + ".json")).write_text(json.dumps(issue))
            report = review(root)
            self.assertIn("Discovery has been empty in at least five", report)
            self.assertIn("dominant outlet changed from The Guardian", report)
            self.assertIn("to Handelsblatt", report)




if __name__ == "__main__":
    unittest.main()
