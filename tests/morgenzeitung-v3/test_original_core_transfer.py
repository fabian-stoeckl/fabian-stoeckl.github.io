"""Editorial lessons from the original newspaper, without importing its technical gates."""
import copy
import json
import unittest

from scripts.morgenzeitung_v3_engine import score, select, ingest_feedback, compare_learning
from scripts.morgenzeitung_v3_editorial import (
    reason_labels, style_signals, editorial_feedback_metrics, research_window,
)


def story(n, topic="Industrie", fit=3, novelty=3, impact=3, perspective=3):
    return {
        "id":f"{n:016x}", "title":f"Story {n}", "source":"Verlag",
        "url":f"https://example.org/story/{n}", "topic":topic,
        "fit":fit,"novelty":novelty,"impact":impact,"perspective":perspective,
    }


def issue(n,date,ratings,updated=None):
    return {
        "number":n,"title":"[Morgenzeitung 3] Feedback "+date,
        "updated_at":updated or date+"T10:00:00Z",
        "body":"MORGENZEITUNG_V3_FEEDBACK_V1\n"+json.dumps({
            "origin":"website-explicit","date":date,"ratings":ratings
        })
    }


class OriginalCoreTransferTests(unittest.TestCase):
    def test_major_public_news_does_not_depend_on_private_topics(self):
        significant=story(1,topic="Politik",fit=0,novelty=4,impact=5,perspective=4)
        personalized=story(2,topic="Industrie",fit=5,novelty=3,impact=1,perspective=2)
        profile={"topic_priorities":{"Industrie":5,"Politik":0},
                 "article_feedback":{significant["id"]:{"rating":"Nicht relevant","reason":""}}}
        self.assertEqual(select([significant,personalized],profile,section="Heute wichtig")[0]["id"],significant["id"])
        self.assertEqual(select([significant,personalized],profile,section="Vertiefungen")[0]["id"],personalized["id"])
        # V1 breaking headlines deliberately do not have a personal topic field.
        headline=story(3,topic="Politik",fit=0,novelty=5,impact=5,perspective=5)
        headline.pop("topic")
        self.assertEqual(select([headline,personalized],profile,section="Heute wichtig")[0]["id"],headline["id"])
        self.assertEqual(len(select([headline,personalized],profile,section="Heute wichtig")),2)
        self.assertEqual(len(select([headline,personalized],profile,section="Vertiefungen")),1)

    def test_quality_reason_is_not_topic_rejection(self):
        labels=reason_labels("Schon bekannt und zu oberflächlich","Nicht relevant")
        self.assertIn("already_known",labels)
        self.assertIn("too_shallow",labels)
        self.assertNotIn("topic_dislike",labels)
        self.assertEqual(reason_labels("Schon bekannt","Sehr relevant"),())
        first=issue(11,"2026-10-26",[{"id":"a"*16,"rating":"Nicht relevant","reason":"Schon bekannt"}])
        second=issue(12,"2026-10-27",[{"id":"b"*16,"rating":"Nicht relevant","reason":"Schon bekannt"}])
        profile,_=ingest_feedback({},[first,second],{"a"*16:"Industrie","b"*16:"Industrie"})
        self.assertEqual(profile["feedback_topic_deltas"],{})
        self.assertEqual(profile["style_preference_signals"]["novelty"],1)
        self.assertEqual(profile["style_preference_signals"]["analysis"],0)
        low=story(1,novelty=1);high=story(2,novelty=5)
        old_profile={"topic_priorities":{"Industrie":3}}
        new_profile={**old_profile,"style_preference_signals":profile["style_preference_signals"]}
        self.assertGreater(score(high,new_profile)-score(low,new_profile),
                           score(high,old_profile)-score(low,old_profile))

    def test_depth_is_guidance_not_access_proxy(self):
        rows={
            "a":{"rating":"Nicht relevant","reason":"Zu oberflächlich"},
            "b":{"rating":"Nicht relevant","reason":"Zu oberflächlich"},
            "c":{"rating":"Nicht relevant","reason":"Zu speziell, zu viele juristische Details"},
        }
        signals=style_signals(rows)
        self.assertEqual(signals["analysis"],1)
        self.assertEqual(signals["broader_context"],0)
        a=story(1);b=story(2)
        a.update(access="metadata",paywall=True,fulltext_available=False)
        b.update(access="read",paywall=False,fulltext_available=True)
        profile={"topic_priorities":{"Industrie":3},"style_preference_signals":signals}
        self.assertEqual(score(a,profile),score(b,profile))
        self.assertEqual([x["id"] for x in select([a,b],profile)],
                         [x["id"] for x in select([b,a],profile)][::-1])

    def test_explicit_topic_dislike_needs_repetition(self):
        first=issue(11,"2026-10-26",[{"id":"a"*16,"rating":"Nicht relevant","reason":"Thema interessiert mich nicht"}])
        profile,_=ingest_feedback({},[first],{"a"*16:"Fiskalpolitik"})
        self.assertEqual(profile["feedback_topic_deltas"].get("Fiskalpolitik"),0)
        second=issue(12,"2026-10-27",[{"id":"b"*16,"rating":"Nicht relevant","reason":"Thema interessiert mich nicht"}])
        learned,_=ingest_feedback(profile,[second],{"a"*16:"Fiskalpolitik","b"*16:"Fiskalpolitik"})
        self.assertEqual(learned["feedback_topic_deltas"]["Fiskalpolitik"],-1)

    def test_access_metadata_never_changes_candidates(self):
        a=story(1);b=story(2,fit=4)
        profile={"topic_priorities":{"Industrie":4},"style_preference_signals":{"novelty":2}}
        selected=[x["id"] for x in select([a,b],profile)]
        variant=copy.deepcopy([a,b])
        for item in variant:
            item.update(access="blocked",paywall=True,http_status=403,fulltext="",
                        summary_length=0)
        self.assertEqual(selected,[x["id"] for x in select(variant,profile)])

    def test_no_unproven_causal_learning_claim(self):
        p={"feedback_by_issue":{}}
        self.assertEqual(editorial_feedback_metrics(p)["trend_status"],"insufficient_feedback")
        samples={}
        for i,day in enumerate(("2026-10-26","2026-10-27")):
            samples[str(i)]={"date":day,"updated_at":day+"T10:00:00Z",
                             "ratings":[{"id":f"{j+i*10:016x}","rating":"Sehr relevant" if j<i+1 else "Teilweise relevant"}
                                        for j in range(5)]}
        metric=editorial_feedback_metrics({"feedback_by_issue":samples})
        self.assertEqual(metric["trend_status"],"descriptive_only")
        self.assertEqual(metric["causal_quality_improvement_proven"],False)
        self.assertGreater(metric["very_relevant_share_change"],0)

    def test_previous_research_gap_not_lost(self):
        old={"preview":False,"window_end":"2026-10-26T05:00:00Z"}
        window=research_window(old,"2026-10-28T05:00:00Z")
        self.assertTrue(window["extended_for_gap"])
        self.assertEqual(window["window_start"],old["window_end"])
        start=research_window({"preview":True,"window_end":"2026-10-26T05:00:00Z"},
                              "2026-10-28T05:00:00Z")
        self.assertEqual(start["reference"],"initial_24h")
        with self.assertRaises(ValueError):
            research_window({"preview":False,"window_end":"2026-10-29T05:00:00Z"},
                            "2026-10-28T05:00:00Z")

    def test_legacy_issue_cannot_fake_new_v3_learning(self):
        old={"number":44,"title":"[Morgenzeitung] Sammelbewertung 2026-10-27",
             "updated_at":"2026-10-27T10:00:00Z","body":"old data"}
        new_profile,changed=ingest_feedback({},[old],{})
        self.assertEqual(changed,[])
        self.assertEqual(new_profile["article_feedback"],{})
        self.assertEqual(new_profile["feedback_metrics"]["days"],[])


if __name__=="__main__":
    unittest.main()
