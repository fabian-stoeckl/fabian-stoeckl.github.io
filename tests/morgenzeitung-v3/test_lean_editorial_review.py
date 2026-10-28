"""Regression tests for editorial review, not technical article-link verification."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.morgenzeitung_v3_editorial import (
    calibration_review, edition_feedback_review, edition_series_review
)
from scripts.morgenzeitung_v3_engine import select, missed_candidate_review


def article(n, publisher="Publisher A", topic="Industrie", fit=4):
    return {"id":f"{n:016x}","source":publisher,"topic":topic,
            "title":f"Actual independent analysis {n}",
            "url":f"https://example.org/article/{n}",
            "fit":fit,"novelty":4,"impact":4,"perspective":3}


def votes(date, entries, issue="1", updated="2026-10-28T10:00:00Z"):
    return {str(issue):{"date":date,"updated_at":updated,
            "ratings":[{"id":i,"rating":v} for i,v in entries]}}


def edition(date, ids, preview=False):
    return {"date":date,"preview":preview,
            "articles":[article(i) for i in ids],
            "headlines":[]}


class LeanV3ReviewTests(unittest.TestCase):
    def test_omitted_articles_are_not_inferred_reader_feedback(self):
        rows=[article(i) for i in range(1,6)]
        chosen=select(rows,{},limit=2,discovery_slots=0)
        report=missed_candidate_review(rows,chosen,{},max_suggestions=3)
        self.assertFalse(report["feedback_inferred"])
        self.assertTrue(report["review_candidates"])
        self.assertTrue(all(x["id"] not in [a["id"] for a in chosen]
                            for x in report["review_candidates"]))
        self.assertTrue(all(x["review_reason"] in (
            "alternate_story_coverage","comparable_relevance_but_omitted")
                            for x in report["review_candidates"]))
        self.assertEqual(select(rows,{},limit=2,discovery_slots=0),chosen)

    def test_low_scoring_missing_candidates_do_not_force_extra_publication(self):
        strong=article(1,fit=5)
        weak=article(2,fit=0)
        weak.update(novelty=0,impact=0,perspective=0)
        chosen=select([strong,weak],{},limit=1,discovery_slots=0)
        review=missed_candidate_review([strong,weak],chosen,{})
        self.assertEqual(review["review_candidates"],[])
        self.assertFalse(review["feedback_inferred"])

    def test_calibration_uses_anchors_and_ignores_access(self):
        rows=[article(1),article(2)]
        original=calibration_review(rows)
        self.assertIn("incremental insight",original["rubric"]["fit"])
        modified=copy.deepcopy(rows)
        modified[0].update(paywall=True,http_status=403,fulltext="",access="blocked")
        modified[1].update(paywall=False,http_status=200,fulltext="word "*999,access="read")
        self.assertEqual(original,calibration_review(modified))
        self.assertFalse(original["release_blocked"])
        invalid=calibration_review([{"source":"X","fit":True,"novelty":6,"impact":3}])
        self.assertEqual(invalid["invalid"]["fit"],1)
        self.assertEqual(invalid["invalid"]["novelty"],1)
        self.assertEqual(invalid["missing"]["perspective"],1)

    def test_source_level_variance_is_only_a_question_not_an_algorithmic_bonus(self):
        rows=[article(i,"A",fit=5) for i in range(1,4)]
        rows.extend(article(i,"B",fit=1) for i in range(4,7))
        report=calibration_review(rows)
        self.assertTrue(report["review_notes"])
        self.assertEqual(report["source_fit_means_for_review_only"],{"A":5.0,"B":1.0})
        self.assertTrue(report["no_access_based_adjustments"])
        self.assertFalse(report["release_blocked"])

    def test_whole_edition_only_counts_real_votes_for_published_ids(self):
        day="2026-10-28"
        ed=edition(day,range(1,13))
        data=votes(day,[(f"{i:016x}","Sehr relevant" if i<=5 else "Nicht relevant")
                        for i in range(1,7)])
        data["2"]={"date":day,"updated_at":"2026-10-28T11:00:00Z",
                   "ratings":[{"id":f"{1:016x}","rating":"Teilweise relevant"},
                              {"id":f"{99:016x}","rating":"Nicht relevant"}]}
        data["3"]={"date":"2026-10-27","updated_at":"2026-10-28T12:00:00Z",
                   "ratings":[{"id":f"{2:016x}","rating":"Nicht relevant"}]}
        result=edition_feedback_review(ed,{"feedback_by_issue":data})
        self.assertEqual(result["rated"],6)
        self.assertEqual(result["unrated"],6)
        self.assertEqual(result["ratings"]["Sehr relevant"],4)
        self.assertEqual(result["ratings"]["Teilweise relevant"],1)
        self.assertEqual(result["ratings"]["Nicht relevant"],1)
        self.assertEqual(result["assessment"],"descriptive")
        self.assertFalse(result["learning_applied"])
        self.assertFalse(result["causal_improvement_proven"])
        self.assertEqual(result["topics_published"],{"Industrie":12})
        self.assertEqual(edition_feedback_review({**ed,"preview":True},
                       {"feedback_by_issue":data})["assessment"],"insufficient_real_feedback")

    def test_absence_of_ratings_is_not_dislike_or_negative_selection_signal(self):
        ed=edition("2026-10-28",range(1,13))
        result=edition_feedback_review(ed,{"feedback_by_issue":{}})
        self.assertEqual(result["rated"],0)
        self.assertEqual(result["ratings"]["Nicht relevant"],0)
        self.assertEqual(result["assessment"],"insufficient_real_feedback")
        self.assertIsNone(result["very_relevant_share_of_rated"])

    def test_daily_trend_is_descriptive_only_not_proof_of_learning(self):
        dates=["2026-10-27","2026-10-28"]
        editions=[edition(d,range(k,k+12)) for k,d in zip((1,21),dates)]
        feedback={}
        for j,date in enumerate(dates):
            feedback[str(j)]={"date":date,"updated_at":date+"T12:00:00Z",
                "ratings":[{"id":f"{i:016x}",
                            "rating":"Sehr relevant" if i < (3 if j==0 else 26)
                                else "Teilweise relevant"}
                           for i in range(1 if j==0 else 21,7 if j==0 else 27)]}
        trend=edition_series_review(editions,{"feedback_by_issue":feedback})
        self.assertEqual(trend["trend"],"descriptive_only")
        self.assertGreater(trend["change_in_positive_share_among_rated"],0)
        self.assertFalse(trend["causal_improvement_proven"])
        self.assertFalse(trend["learning_applied"])

    def test_quality_cli_runs_without_network_and_uses_existing_command(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            rows=[article(i) for i in range(1,7)]
            ed=edition("2026-10-28",range(1,5))
            (p/"candidates.json").write_text(json.dumps(rows))
            (p/"profile.json").write_text(json.dumps({"feedback_by_issue":{}}))
            (p/"edition.json").write_text(json.dumps(ed))
            result=subprocess.run([
                sys.executable,"-m","scripts.morgenzeitung_v3_engine","quality",
                "--candidates",str(p/"candidates.json"),
                "--profile",str(p/"profile.json"),
                "--edition",str(p/"edition.json"),
                "--section","Vertiefungen","--limit","4",
            ],capture_output=True,text=True,check=True)
            parsed=json.loads(result.stdout)
            self.assertIn("calibration",parsed)
            self.assertIn("omitted_candidate_review",parsed)
            self.assertIn("whole_edition_feedback",parsed)
            self.assertFalse(parsed["feedback_inferred_from_omissions"])
            self.assertTrue(parsed["private_only"])
            self.assertFalse(parsed["release_blocked"])


if __name__=="__main__":
    unittest.main()
