"""Tests for the eight V3.5 improvements; no publisher network calls."""
import json
from pathlib import Path
import unittest

from scripts.morgenzeitung_v3_engine import score
from scripts.morgenzeitung_v3_quality import (
    editorial_snapshot, v1_comparison,
    calibration_review_from_feedback, reader_comparison_candidates,
)


def story(n, **kwargs):
    return {
        "id": f"{n:016x}", "title": f"Report {n}",
        "url": f"https://example.org/real/{n}", "source": "Example",
        "published_at": "2026-10-28T07:00:00Z",
        "summary": "Verified change in the relevant industry.",
        "topic": "Industrie & Innovation", "fit": 5 if n == 1 else 3,
        "novelty": 4, "impact": 4, "perspective": 3,
        **kwargs,
    }


class EditorialQualityV35Tests(unittest.TestCase):
    def test_v1_vs_v3_comparison_uses_real_read_only_editions(self):
        root=Path("Privat")
        v1=json.loads((Path("services/morgenzeitung-v3/fixtures/v1-reference-2026-10-27.json")).read_text())
        v3=json.loads((root/"Persoenliche-Zeitung/data/2026-10-28.json").read_text())
        report=v1_comparison(v3,v1)
        self.assertEqual(report["v1_reference"]["articles"],15)
        self.assertEqual(report["v3"]["articles"],12)
        self.assertEqual(report["v3"]["article_genre_identified"],0)
        self.assertEqual(report["v3"]["headlines_from_austria"],1)
        self.assertGreater(report["v1_reference"]["articles_with_documented_facts"],0)
        self.assertTrue(report["summary_length_is_not_quality"])
        self.assertFalse(report["release_blocked"])

    def test_editorial_snapshot_reports_unknown_not_fabricated_fulltext(self):
        d={"date":"2026-10-28",
           "articles":[story(1,article_type="analysis",evidence_level="teaser"),
                       story(2,article_type="explainer",access="full")],
           "headlines":[{"region":"Österreich"},{"region":"International"}]}
        s=editorial_snapshot(d)
        self.assertEqual(s["article_genre_identified"],2)
        self.assertEqual(s["source_evidence_levels"]["unknown"],1)
        self.assertEqual(s["source_evidence_levels"]["teaser"],1)
        self.assertEqual(s["headlines_from_austria"],1)
        self.assertEqual(s["articles_with_selection_reason"],0)

    def test_calibration_requires_real_frozen_pre_feedback_snapshot(self):
        rows=[story(1),story(2),story(3),story(4),story(5)]
        before={"topic_priorities":{"Industrie & Innovation":3}}
        observed={"article_feedback":{
            row["id"]:{"rating":"Nicht relevant" if i==0 else "Sehr relevant",
                       "reason":"Zu oberflächlich" if i==0 else "",
                       "section":"Vertiefungen"}
            for i,row in enumerate(rows)}}
        self.assertEqual(calibration_review_from_feedback(rows,None,observed,score)
                         ["status"],"missing_frozen_profile")
        output=calibration_review_from_feedback(rows,before,observed,score)
        self.assertEqual(output["observed_ratings"],5)
        self.assertTrue(output["highest_pre_feedback_scored_negative_examples"])
        self.assertFalse(output["automatic_weight_changes"])
        self.assertFalse(output["out_of_sample_quality_proven"])
        self.assertNotIn("access",output)

    def test_calibration_preserves_access_neutrality(self):
        a=story(1,access="full")
        b=story(1,access="blocked")
        p={"topic_priorities":{"Industrie & Innovation":4}}
        self.assertEqual(score(a,p),score(b,p))

    def test_optional_alternatives_only_editorial_review_never_autopublish(self):
        pool=[story(1),story(2),story(3),story(4)]
        report=reader_comparison_candidates(pool,[pool[0],pool[1]],score,
                                            {"topic_priorities":{}})
        self.assertFalse(report["automatic_publication"])
        self.assertEqual(len(report["private_editorial_suggestions"]),2)
        self.assertNotIn(pool[0]["id"],[x["id"] for x in
                                      report["private_editorial_suggestions"]])
        self.assertTrue(all(x["review_required"] for x in
                            report["private_editorial_suggestions"]))

    def test_austrian_coverage_is_diagnostic_not_publisher_quota(self):
        d={"date":"2026-10-28","articles":[story(1)],
           "headlines":[{"region":"International"}]*16}
        report=v1_comparison(d)
        self.assertTrue(any("Austrian" in line for line in report["editorial_review"]))
        self.assertFalse(report["release_blocked"])


if __name__=="__main__":
    unittest.main()
