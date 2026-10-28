"""Content-focused V3 selection tests. No publisher link checks or external networks."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.morgenzeitung_v3_editorial import style_signals
from scripts.morgenzeitung_v3_engine import (
    score, select, mark_recent_stories, compare_learning, load_edition_history
)


def item(i, topic="Industrie", fit=4):
    return {"id":f"{i:016x}", "url":f"https://example.org/news/{i}",
            "source":"Example Publisher", "title":f"Editorial story {i}",
            "topic":topic, "fit":fit, "novelty":3, "impact":4, "perspective":3}


class EditorialQualityAndMemoryTests(unittest.TestCase):
    def test_personal_fit_means_added_insight_not_access(self):
        # Candidate 1 is topically familiar but does not add much.
        shallow=item(1,fit=1)
        insightful=item(2,fit=5)
        profile={"topic_priorities":{"Industrie":5}}
        self.assertEqual(select([shallow,insightful],profile)[0]["id"],insightful["id"])
        changed=copy.deepcopy([shallow,insightful])
        changed[0].update(access="full",fulltext="x"*100000,content_access="read")
        changed[1].update(access="headline",paywall=True,http_status=403,fulltext="")
        self.assertEqual(select(changed,profile)[0]["id"],insightful["id"])
        self.assertEqual(score(insightful,profile),score(changed[1],profile))

    def test_quality_criticism_affects_real_quality_not_length_of_fulltext(self):
        signals=style_signals({
            "a":{"rating":"Nicht relevant","reason":"Zu oberflächlich"},
            "b":{"rating":"Nicht relevant","reason":"Zu oberflächlich"},
            "c":{"rating":"Nicht relevant","reason":"Zu speziell"},
            "d":{"rating":"Nicht relevant","reason":"Zu speziell"},
            "e":{"rating":"Nicht relevant","reason":"Einseitig"},
            "f":{"rating":"Nicht relevant","reason":"Einseitig"},
        })
        self.assertEqual(signals["analysis"],1)
        self.assertEqual(signals["broader_context"],1)
        self.assertEqual(signals["perspectives"],1)
        low=item(1)
        high=item(2)
        for row,amount in ((low,1),(high,5)):
            row.update(analysis_value=amount,context_value=amount,perspective=amount)
        profile={"topic_priorities":{"Industrie":3},"style_preference_signals":signals}
        baseline={"topic_priorities":{"Industrie":3}}
        self.assertGreater(score(high,profile)-score(low,profile),
                           score(high,baseline)-score(low,baseline))
        changed=copy.deepcopy([high,low])
        changed[0].update(access="blocked",paywall=True,http_status=403,fulltext="")
        changed[1].update(access="full",paywall=False,http_status=200,fulltext="a"*50000)
        self.assertEqual([x["id"] for x in select([low,high],profile)],
                         [x["id"] for x in select(changed,profile)])
        # Unassessed headline-only candidates are neutral, not auto-penalized.
        missing=item(3)
        self.assertEqual(score(missing,profile),score(missing,baseline)+
                         signals["perspectives"]*(missing["perspective"]-2.5))
        with self.assertRaises(ValueError):
            score({**high,"analysis_value":9},profile)

    def test_twenty_headlines_fifteen_analysis_articles(self):
        pool=[item(i) for i in range(1,26)]
        self.assertEqual(len(select(pool,{},section="Heute wichtig")),20)
        self.assertEqual(len(select(pool,{},section="Vertiefungen")),15)
        self.assertEqual(len(select(pool,{},section="Heute wichtig",limit=18)),18)
        with self.assertRaises(ValueError):
            select(pool,{},section="Heute wichtig",limit=21)
        with self.assertRaises(ValueError):
            select(pool,{},section="Vertiefungen",limit=20)

    def test_memory_marks_repeated_articles_even_with_different_ids(self):
        old=item(1)
        old["id"]="e"*16
        old["url"]="https://example.org/news/1?utm_source=old"
        old["event"]="industry-chip-factory-2026"
        edition={"date":"2026-10-27","preview":False,
                 "articles":[old],"headlines":[]}
        repeated=item(1)
        repeated["url"]="https://example.org/news/1?utm_source=new"
        repeated["event"]=old["event"]
        fresh=item(2)
        profile={"topic_priorities":{"Industrie":3}}
        result=mark_recent_stories([repeated,fresh],[edition],"2026-10-28")
        self.assertTrue(result[0]["seen_recently"])
        self.assertFalse(result[0].get("material_update",False))
        self.assertEqual(select([repeated,fresh],profile,previous_editions=[edition],
                                edition_date="2026-10-28")[0]["id"],fresh["id"])
        # The input and historical edition must remain unchanged after selection.
        self.assertNotIn("seen_recently",repeated)
        self.assertEqual(old["id"],"e"*16)

    def test_material_update_requires_a_real_explanation(self):
        previous=item(1)
        edition={"date":"2026-10-27","preview":False,"articles":[previous],"headlines":[]}
        newer={**item(1),"material_update":True}
        marked=mark_recent_stories([newer],[edition],"2026-10-28")
        self.assertTrue(marked[0]["seen_recently"])
        self.assertFalse(marked[0]["material_update"])
        newer["update_evidence"]="Die Regierung beschloss heute erstmals eine neue Reformvariante."
        marked=mark_recent_stories([newer],[edition],"2026-10-28")
        self.assertTrue(marked[0]["material_update"])
        self.assertEqual(score(marked[0],{}),score(item(1),{}))
        stale=mark_recent_stories([item(1)],[edition],"2026-11-30")
        self.assertFalse(stale[0].get("seen_recently",False))

    def test_history_comparison_uses_same_records(self):
        previous={"date":"2026-10-27","preview":False,"articles":[item(1)],"headlines":[]}
        pool=[item(1),item(2,topic="Klima")]
        before={"topic_priorities":{"Industrie":3,"Klima":3}}
        after={"topic_priorities":{"Industrie":3,"Klima":5}}
        compared=compare_learning(pool,before,after,new_feedback=True,
                                  previous_editions=[previous],edition_date="2026-10-28")
        expected=[x["id"] for x in select(pool,after,previous_editions=[previous],
                                          edition_date="2026-10-28")]
        self.assertEqual(compared["after_ids"],expected)
        self.assertFalse(compared["feedback_applied"]) # no change caused by new feedback

    def test_local_history_index_only_no_external_network(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"index.json").write_text(json.dumps({"dates":["2026-10-27"]}))
            (root/"2026-10-27.json").write_text(json.dumps({
                "date":"2026-10-27","preview":False,"articles":[item(1)],"headlines":[]}))
            self.assertEqual(len(load_edition_history(root)),1)
            with self.assertRaises(ValueError):
                mark_recent_stories([item(1)],load_edition_history(root),None)


if __name__=="__main__":
    unittest.main()
