"""Regression tests for the 18 editorial lessons retained from V1 in V3.

No external URLs, no full-text requirements and no V1 file writes.
"""
import copy
import json
import unittest

from scripts.morgenzeitung_v3_engine import (
    stable_article_id, mark_recent_stories, score, select,
    compare_learning, ingest_feedback,
)
from scripts.morgenzeitung_v3_editorial import (
    reason_labels, feedback_dimensions, editorial_depth_review,
)


def candidate(i, topic="Industrie & Innovation", **extra):
    return {
        "id": f"{i:016x}", "url": f"https://example.org/story/{i}",
        "title": f"Story {i}", "source": "Verlag", "topic": topic,
        "fit": 4, "novelty": 3, "impact": 4, "perspective": 3,
        **extra,
    }


def issue(ratings, comment="", when="2026-10-28T12:00:00Z"):
    payload = {
        "date": "2026-10-28", "origin": "website-explicit",
        "ratings": ratings, "comment": comment,
    }
    return {
        "number": 9, "title": "[Morgenzeitung 3] Feedback 2026-10-28",
        "updated_at": when,
        "body": "MORGENZEITUNG_V3_FEEDBACK_V1\n" + json.dumps(payload),
    }


class V1TransferTests(unittest.TestCase):
    def test_rating_reason_works_at_every_level(self):
        for rating in ("Sehr relevant", "Teilweise relevant", "Nicht relevant"):
            self.assertIn("too_shallow", reason_labels("zu oberflächlich", rating))
            self.assertIn("already_known", reason_labels("schon bekannt", rating))
        self.assertEqual(reason_labels("zu oberflächlich", None), ())
        self.assertIn("topic_dislike", reason_labels(
            "Thema interessiert mich nicht", "Nicht relevant"))

    def test_partial_quality_feedback_is_not_a_direct_downvote(self):
        first = candidate(1, analysis_value=4, context_value=5)
        second = candidate(2, analysis_value=1, context_value=1)
        before = {"topic_priorities":{"Industrie & Innovation":3}}
        rows = [
            {"id":first["id"], "section":"Vertiefungen", "rating":"Teilweise relevant",
             "reason":"zu oberflächlich"},
            {"id":second["id"], "section":"Vertiefungen", "rating":"Teilweise relevant",
             "reason":"zu oberflächlich"},
        ]
        after,changed = ingest_feedback(before,[issue(rows)],
            {r["id"]:"Industrie & Innovation" for r in rows})
        self.assertEqual(changed,["9"])
        self.assertEqual(after["feedback_topic_deltas"],{})
        self.assertEqual(after["style_preference_signals"]["analysis"],1)
        self.assertEqual(after["topic_style_signals"]["Industrie & Innovation"]["analysis"],1)
        self.assertGreater(score(first,after)-score(first,before),
                           score(second,after)-score(second,before))
        self.assertEqual(feedback_dimensions(after["article_feedback"])["counts"]["too_shallow"],2)

    def test_explicit_reader_requests_are_preserved_on_edits(self):
        orig=issue([],comment="Mehr Analysen zu Produktivität")
        p,_=ingest_feedback({},[orig],{})
        self.assertEqual(p["explicit_reader_requests"][0]["text"],
                         "Mehr Analysen zu Produktivität")
        again, changed=ingest_feedback(p,[orig],{})
        self.assertEqual(changed,[])
        self.assertEqual(len(again["explicit_reader_requests"]),1)
        changed_issue=issue([],comment="Bessere Analysen zu Industrie",
                            when="2026-10-28T13:00:00Z")
        edited,_=ingest_feedback(again,[changed_issue],{})
        self.assertEqual(len(edited["explicit_reader_requests"]),1)
        self.assertEqual(edited["explicit_reader_requests"][0]["text"],
                         "Bessere Analysen zu Industrie")
        self.assertEqual(edited["editorial_review_queue"][0]["status"],
                         "pending_editorial_review")

    def test_headline_votes_cannot_rewrite_personal_topic(self):
        a,b=candidate(1),candidate(2)
        rows=[
            {"id":a["id"],"rating":"Sehr relevant","section":"Heute wichtig","reason":""},
            {"id":b["id"],"rating":"Sehr relevant","section":"Heute wichtig","reason":""}
        ]
        p,_=ingest_feedback({},[issue(rows)],{a["id"]:a["topic"],b["id"]:b["topic"]})
        self.assertNotIn(a["topic"],p["feedback_topic_deltas"])
        self.assertEqual(len(p["article_feedback"]),2)
        self.assertEqual(p["feedback_metrics"]["days"][0]["ratings"],2)

    def test_unreasoned_negative_does_not_reject_entire_topic(self):
        rows=[{"id":f"{i:016x}","rating":"Nicht relevant","reason":""} for i in range(1,6)]
        p,_=ingest_feedback({},[issue(rows)],{r["id"]:"Klima & Energie" for r in rows})
        self.assertEqual(p["feedback_topic_deltas"],{})

    def test_topic_evidence_counts_conflicting_and_neutral_signals(self):
        rows=[
            {"id":f"{i:016x}","rating":rating,"reason":reason} for i,rating,reason in [
                (1,"Sehr relevant",""),(2,"Sehr relevant",""),
                (3,"Nicht relevant","Thema interessiert mich nicht"),
                (4,"Teilweise relevant","")
            ]
        ]
        p,_=ingest_feedback({},[issue(rows)],{r["id"]:"Industrie & Innovation" for r in rows})
        evidence=p["topic_evidence"]["Industrie & Innovation"]
        self.assertEqual((evidence["positive"],evidence["neutral"],evidence["negative"]),(2,1,1))
        self.assertEqual(p["feedback_topic_deltas"]["Industrie & Innovation"],0)

    def test_stable_ids_canonicalize_tracking_without_rewriting_history(self):
        base="https://example.org/industrial-analysis"
        self.assertEqual(stable_article_id(base),stable_article_id(base+"?utm_source=mail"))
        self.assertEqual(len(stable_article_id(base)),16)
        self.assertNotEqual(stable_article_id(base),stable_article_id(base+"/other"))

    def test_repeated_story_keeps_sent_knowledge_and_requires_update_evidence(self):
        old={"date":"2026-10-27","articles":[
            {"id":"a"*16,"url":"https://example.org/story/1",
             "title":"Story 1","facts":["A known project produces 50 units."],
             "summary":"A known project produces 50 units."}
        ],"headlines":[]}
        base=candidate(1,material_update=True,
                       update_evidence="A known project produces 50 units.")
        without=mark_recent_stories([base],[old],"2026-10-28")[0]
        self.assertTrue(without["seen_recently"])
        self.assertFalse(without["material_update"])
        self.assertEqual(without["known_facts"][0],
                         "A known project produces 50 units.")
        new=copy.deepcopy(base)
        new["update_evidence"]="The project has now increased production to 75 units."
        with_update=mark_recent_stories([new],[old],"2026-10-28")[0]
        self.assertTrue(with_update["material_update"])
        # This is evidence of a documented change, not a semantic truth check.
        self.assertEqual(len(mark_recent_stories([candidate(1)],[],"2026-10-28")),1)

    def test_compare_replays_original_selection_not_fabricated_feedback(self):
        pool=[candidate(1,"Industrie"),candidate(2,"Klima")]
        before={"topic_priorities":{"Industrie":3,"Klima":3}}
        after={"topic_priorities":{"Industrie":3,"Klima":3},
               "feedback_topic_deltas":{"Industrie":-2,"Klima":2}}
        diff=compare_learning(pool,before,after,new_feedback=True,limit=2)
        self.assertEqual(diff["before_ids"],
                         [x["id"] for x in select(pool,before,limit=2)])
        self.assertEqual(diff["after_ids"],
                         [x["id"] for x in select(pool,after,limit=2)])
        self.assertTrue(diff["selection_changed"])

    def test_short_depth_is_editorial_warning_not_fulltext_gate(self):
        a=candidate(1,summary="Kurzer Bericht.",access="teaser")
        b=candidate(2,summary="Kurzer Bericht.",access="full")
        review=editorial_depth_review([a,b],[a,b])
        self.assertFalse(review["release_blocked"])
        self.assertEqual(review["review"][0]["issue"],
                         "missing_analytical_quality_assessment")
        self.assertEqual(len([x for x in review["review"]
                              if x["issue"]=="check_incremental_insight"]),2)


if __name__=="__main__":
    unittest.main()
