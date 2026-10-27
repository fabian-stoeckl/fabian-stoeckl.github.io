import unittest

from scripts.morgenzeitung_candidate_triage import triage
from scripts.morgenzeitung_source_preflight import preflight

DATE = "2026-10-27"
URL = "https://www.faz.net/aktuell/wirtschaft/energie-123.html"


def pool():
    names = ["ORF","Handelsblatt","FAZ","NZZ","BBC News"]
    return [{"id":str(i),"source":names[i % 5], "topic":"Wirtschaft",
             "title":"Energie, Investitionen und Europas Wirtschaft im Wandel",
             "source_url":URL if names[i % 5]=="FAZ" else "https://example.org/article-"+str(i),
             "published_at":"2026-10-27T06:00:00+00:00",
             "verified":True}
            for i in range(20)]


class TriageTests(unittest.TestCase):
    def test_single_blocked_original_does_not_destroy_eligible_candidate_pool(self):
        raw = pool()
        def checker(rows, date, publisher_dates):
            if rows[0]["id"] == "2":
                raise ValueError("Publisher article original HTTP 403; official feed no identical story")
            return {"checked":[{"original_article_http_verified": True}]}
        report = triage(raw,DATE,checker=checker)
        self.assertTrue(report["ready_for_final_preflight"])
        self.assertEqual(report["eligible_count"],19)
        self.assertEqual(report["rejected_count"],1)
        self.assertEqual(report["rejected"][0]["id"],"2")
        self.assertEqual(len(raw),20, "Raw research may not be overwritten")
        # A separate unchanged hard preflight must STILL be run on eligible.
        clean = preflight(report["eligible"],DATE,checker=checker)
        self.assertTrue(clean["preflight_passed"])

    def test_feed_verification_requires_actual_original_proof(self):
        raw = pool()
        def fake_flag(rows, date, publisher_dates):
            return {"checked":[{"publisher_feed_verified":True,
                                "original_article_http_verified":False}]}
        report = triage(raw,DATE,checker=fake_flag)
        self.assertFalse(report["ready_for_final_preflight"])
        self.assertEqual(report["eligible_count"],0)
        self.assertEqual(report["rejected_count"],20)

    def test_matching_publisher_feed_can_make_a_blocked_story_eligible(self):
        raw = pool()
        def official(rows, date, publisher_dates):
            item=rows[0]
            return {"checked":[{
                "original_article_http_verified":False,
                "publisher_feed_verified":True,
                "publisher_feed_evidence":{
                    "publisher_feed_verified":True,
                    "original_url":item["source_url"],
                    "publication_time":"2026-10-27T06:00:00Z",
                }
            }]}
        result=triage(raw,DATE,checker=official)
        self.assertTrue(result["ready_for_final_preflight"])
        self.assertEqual(result["eligible_count"],20)

    def test_wrong_feed_original_and_false_evidence_never_pass(self):
        raw=pool()
        def wrong(rows,date,publisher_dates):
            return {"checked":[{"original_article_http_verified":False,
                "publisher_feed_verified":True,
                "publisher_feed_evidence":{
                    "publisher_feed_verified":True,
                    "original_url":"https://www.faz.net/aktuell/wirtschaft/other.html",
                    "publication_time":"2026-10-27T06:00:00Z"}}]}
        result=triage(raw,DATE,checker=wrong)
        self.assertEqual(result["eligible_count"],0)

    def test_not_marked_verified_is_not_silently_fixed(self):
        raw=pool()
        raw[0]["verified"]=False
        def checker(rows,date,publisher_dates):
            return {"checked":[{"original_article_http_verified":True}]}
        result=triage(raw,DATE,checker=checker)
        self.assertEqual(result["eligible_count"],19)
        self.assertEqual(result["rejected"][0]["id"],"0")

    def test_duplicate_candidate_id_rejected_before_any_silent_deduplication(self):
        raw=pool()
        raw[1]["id"]=raw[0]["id"]
        with self.assertRaisesRegex(ValueError,"unique"):
            triage(raw,DATE)

    def test_many_blocked_stories_still_fail_final_quality_threshold(self):
        def checker(rows,date,publisher_dates):
            if int(rows[0]["id"]) < 10:
                raise ValueError("unverified story")
            return {"checked":[{"original_article_http_verified":True}]}
        result=triage(pool(),DATE,checker=checker)
        self.assertFalse(result["ready_for_final_preflight"])
        self.assertEqual(result["eligible_count"],10)
        self.assertEqual(result["rejected_count"],10)


if __name__=="__main__":
    unittest.main()
