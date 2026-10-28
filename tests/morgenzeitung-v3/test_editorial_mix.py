"""V3 editorial balance without rigid quotas, publisher access probes or forced viewpoints."""
import copy
import unittest

from scripts.morgenzeitung_v3_engine import select, score
from scripts.morgenzeitung_v3_editorial import editorial_mix_report


def item(n, publisher="A", genre="analysis", topic="Industry", fit=4):
    return {"id":f"{n:016x}","title":f"Different report {n}",
            "url":f"https://example.org/story/{n}","source":publisher,
            "article_type":genre,"topic":topic,"fit":fit,
            "novelty":4,"impact":4,"perspective":3}


class EditorialMixTests(unittest.TestCase):
    def test_near_tied_candidates_prefer_more_distinct_publishers(self):
        pool=[item(1),item(2),item(3),item(4,"B"),item(5,"C")]
        chosen=select(pool,{},limit=4,discovery_slots=0)
        self.assertEqual(chosen[0]["id"],item(1)["id"])
        self.assertEqual(chosen[1]["id"],item(2)["id"])
        self.assertEqual(chosen[2]["source"],"B")
        self.assertEqual(len(chosen),4)

    def test_clear_quality_wins_over_variety(self):
        pool=[item(1,fit=5),item(2,fit=5),item(3,fit=5),
              item(4,"B",fit=1)]
        chosen=select(pool,{},limit=3,discovery_slots=0)
        self.assertEqual([x["source"] for x in chosen],["A","A","A"])

    def test_article_types_and_topics_gently_mix(self):
        pool=[item(1),item(2),item(3),item(4),
              item(5,genre="investigation",topic="Technology"),
              item(6,genre="report",topic="Climate")]
        chosen=select(pool,{},limit=5,discovery_slots=0)
        types=[x["article_type"] for x in chosen]
        self.assertIn("investigation",types)
        self.assertIn("report",types)
        self.assertEqual(len(chosen),5)

    def test_access_stays_neutral_under_mix(self):
        pool=[item(i,publisher=("A" if i<5 else "B")) for i in range(1,7)]
        first=[x["id"] for x in select(pool,{},limit=5,discovery_slots=0)]
        changed=copy.deepcopy(pool)
        for i,row in enumerate(changed):
            row.update(access="full" if i%2 else "blocked",paywall=i%2==0,
                       http_status=403 if i%2 else 200,fulltext="x"*i*2000)
        self.assertEqual([x["id"] for x in select(changed,{},limit=5,
                                                 discovery_slots=0)],first)

    def test_research_report_warns_without_blocking_or_quota(self):
        pool=[item(i,publisher=("A" if i<7 else "B"),
                   topic=("Industry" if i<7 else "Climate")) for i in range(1,9)]
        chosen=pool[:6]
        report=editorial_mix_report(pool,chosen)
        self.assertFalse(report["release_blocked"])
        self.assertTrue(any("Publisher concentration" in x for x in report["recommendations"]))
        self.assertTrue(any("Thematic repetition" in x for x in report["recommendations"]))

    def test_debate_report_asks_for_research_without_false_balance(self):
        a=item(1)
        a.update(debate_id="Industrial-price-cap",viewpoint="support")
        report=editorial_mix_report([a],[a])
        self.assertTrue(any("counter-perspectives" in x for x in report["recommendations"]))
        self.assertFalse(report["release_blocked"])
        b=item(2,"B",genre="opinion")
        b.update(debate_id=a["debate_id"],viewpoint="oppose")
        report2=editorial_mix_report([a,b],[a,b])
        self.assertFalse(any("counter-perspectives" in x for x in report2["recommendations"]))


if __name__=="__main__":
    unittest.main()
