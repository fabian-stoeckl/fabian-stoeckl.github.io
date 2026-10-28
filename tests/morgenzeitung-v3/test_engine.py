import copy
import json
import unittest
from scripts.morgenzeitung_v3_engine import compare_learning, evidence_guard, ingest_feedback, score, select, validate_edition
from scripts.morgenzeitung_v3_release import private_review, check_public_receipt, check_private_receipt

def cand(i, topic="Industrie", fit=4, discovery=False):
    return {"id":f"{i:016x}","title":f"Story {i}","source":f"Journal {i%4}",
            "url":f"https://example.org/story/{i}","topic":topic,"fit":fit,
            "novelty":4,"impact":4,"perspective":3,"discovery":discovery}

class V3EngineTests(unittest.TestCase):
    def setUp(self):
        self.profile={"topic_priorities":{"Industrie":3,"Klima":3},"feedback_topic_deltas":{}}
    def test_paywall_and_access_cannot_change_rank(self):
        entries=[cand(1),cand(2,"Klima",5),cand(3,"Industrie",2)]
        ranked=[x["id"] for x in select(entries,self.profile)]
        changed=copy.deepcopy(entries)
        for i,row in enumerate(changed):
            row.update(access=["full","teaser","blocked"][i],paywall=i==0,
                       fulltext="word "*(1000*i+1),http_status=[200,403,404][i])
        self.assertEqual([x["id"] for x in select(changed,self.profile)],ranked)
        self.assertEqual(score(entries[0],self.profile),score(changed[0],self.profile))
    def test_actual_counterfactual_selection_change(self):
        pool=[cand(1,"Industrie"),cand(2,"Klima")]
        after=copy.deepcopy(self.profile)
        after["feedback_topic_deltas"]={"Klima":2,"Industrie":-2}
        test=compare_learning(pool,self.profile,after,True)
        self.assertTrue(test["feedback_applied"])
        self.assertEqual(test["after_ids"][0],f"{2:016x}")
        self.assertFalse(compare_learning(pool,self.profile,self.profile,True)["feedback_applied"])
        self.assertFalse(compare_learning(pool,self.profile,after,False)["feedback_applied"])
    def test_discoveries_fair_not_forced_low_quality(self):
        pool=[cand(i,fit=5) for i in range(1,5)]
        strong=cand(5,"Wissenschaft",fit=5,discovery=True)
        weak=cand(6,"Offtopic",fit=0,discovery=True)
        weak.update(novelty=0,impact=0,perspective=0)
        chosen=[x["id"] for x in select([*pool,strong,weak],self.profile,limit=4)]
        self.assertIn(strong["id"],chosen)
        self.assertNotIn(weak["id"],chosen)
    def test_feedback_only_real_own_issues_once_with_edits(self):
        base={"date":"2026-10-28","origin":"website-explicit","ratings":[
              {"id":"a"*16,"rating":"Nicht relevant","reason":"Schon bekannt"}]}
        issue={"number":10,"title":"[Morgenzeitung 3] Feedback 2026-10-28",
               "updated_at":"2026-10-28T08:00:00Z",
               "body":"MORGENZEITUNG_V3_FEEDBACK_V1\n"+json.dumps(base)}
        first,changed=ingest_feedback({},[issue],{"a"*16:"Klima"})
        self.assertEqual(changed,["10"])
        self.assertEqual(first["feedback_topic_deltas"],{})
        again,changed=ingest_feedback(first,[issue],{"a"*16:"Klima"})
        self.assertEqual(changed,[])
        base["ratings"][0]["rating"]="Sehr relevant"
        issue["updated_at"]="2026-10-28T09:00:00Z"
        issue["body"]="MORGENZEITUNG_V3_FEEDBACK_V1\n"+json.dumps(base)
        edited,changed=ingest_feedback(first,[issue],{"a"*16:"Klima"})
        self.assertEqual(changed,["10"])
        self.assertEqual(len(edited["feedback_by_issue"]),1)
    def test_repeated_positive_signal_influences_topic(self):
        body={"date":"2026-10-28","origin":"website-explicit","ratings":[
            {"id":"a"*16,"rating":"Sehr relevant","reason":""},
            {"id":"b"*16,"rating":"Sehr relevant","reason":""}]}
        issue={"number":2,"updated_at":"2026-10-28T09:00:00Z",
               "title":"[Morgenzeitung 3] Feedback 2026-10-28",
               "body":"MORGENZEITUNG_V3_FEEDBACK_V1\n"+json.dumps(body)}
        p,_=ingest_feedback({},[issue],{"a"*16:"Industrie","b"*16:"Industrie"})
        self.assertEqual(p["feedback_topic_deltas"]["Industrie"],1)
    def test_mismatched_number_quote_and_causality_warn(self):
        s1="Das Projekt kostet 95 Millionen Euro."
        s2="„Wir schaffen das“, sagte die Ministerin."
        s3="Weil die Preise steigen, sinkt die Nachfrage."
        row={"id":"a"*16,"url":"https://example.org/news","summary":" ".join([s1,s2,s3])}
        report=evidence_guard({"articles":[row],"headlines":[]},{"proofs":{row["id"]:{
            "source_url":row["url"],"level":"teaser","claims":[
             {"text":s1,"source_excerpt":"Das Projekt kostet 15 Millionen Euro.","supported":True},
             {"text":s2,"source_excerpt":"Die Ministerin gab eine Pressekonferenz.","supported":True},
             {"text":s3,"source_excerpt":"Der Preis steigt seit April.","supported":True}]
        }}})
        self.assertTrue({"NUMBER_MISMATCH","QUOTE_MISMATCH","CAUSALITY_UNCONFIRMED"} <=
                        {w["code"] for w in report["warnings"]})
        self.assertEqual(report["status"],"warn")
    def test_supported_snippet_passes_and_unverified_blocked(self):
        row={"id":"b"*16,"url":"https://example.org/real",
             "summary":"Das Vorhaben kostet 21 Millionen Euro."}
        proof={"proofs":{row["id"]:{"source_url":row["url"],"level":"teaser",
            "claims":[{"text":row["summary"],"source_excerpt":"Das Vorhaben kostet 21 Millionen Euro.","supported":True}]}}}
        self.assertEqual(evidence_guard({"articles":[row],"headlines":[]},proof)["status"],"pass")
        article=cand(7); article.update(summary="Belegte Entwicklung.",published_at="2026-10-28T05:00:00Z")
        headline=cand(8);headline.update(summary="Neue Schlagzeile.",published_at="2026-10-28T05:00:00Z",region="International")
        edition={"date":"2026-10-28","researched_at":"2026-10-28T05:30:00Z",
                 "available_at":"2026-10-28T05:40:00Z","preview":False,
                 "articles":[article],"headlines":[headline],
                 "fact_audit":{"status":"warn"},"selection_audit":{"feedback_applied":False}}
        self.assertTrue(validate_edition(edition), "Missing actual private proof must not pass")
        # A handwritten pass is NOT a valid release receipt.
        edition["fact_audit"]={"status":"pass","warning_count":0,"claims_checked":2}
        self.assertTrue(validate_edition(edition))
        dossier={"proofs":{
            article["id"]:{"source_url":article["url"],"level":"teaser","claims":[
                {"text":article["summary"],"source_excerpt":"Belegte Entwicklung.","supported":True}]},
            headline["id"]:{"source_url":headline["url"],"level":"teaser","claims":[
                {"text":headline["summary"],"source_excerpt":"Neue Schlagzeile.","supported":True}]}
        },"editorial_review":{"approved":True,"reviewed_at":"2026-10-28T05:35:00Z"}}
        edition["fact_audit"]=private_review(edition,dossier)
        self.assertEqual(validate_edition(edition,dossier,require_dossier=True),[])
        self.assertEqual(check_public_receipt(edition),[])
        self.assertIn("private dossier required for release",validate_edition(edition,require_dossier=True))
        dossier["proofs"][article["id"]]["claims"][0]["source_excerpt"]="Unbelegte Behauptung."
        self.assertTrue(check_private_receipt(edition,dossier))
        dossier["proofs"][article["id"]]["claims"][0]["source_excerpt"]="Belegte Entwicklung."
        edition["articles"][0]["summary"]="Geänderte unbelegte Entwicklung."
        self.assertTrue(check_public_receipt(edition))
    def test_individual_negative_rating_penalizes_article_without_topic_penalty(self):
        pool=[cand(1),cand(2)]
        p=copy.deepcopy(self.profile)
        p["article_feedback"]={pool[0]["id"]:{"rating":"Nicht relevant","reason":"Schon bekannt"}}
        self.assertEqual(select(pool,p)[0]["id"],pool[1]["id"])
        self.assertEqual(p["feedback_topic_deltas"],{})
        full=copy.deepcopy(pool)
        full[0]["access"]="full";full[1]["access"]="teaser"
        self.assertEqual([x["id"] for x in select(full,p)],[x["id"] for x in select(pool,p)])
    def test_latest_issue_wins_even_with_reverse_api_order(self):
        topic={"a"*16:"Industrie"}
        old={"number":1,"updated_at":"2026-10-27T10:00:00Z",
             "title":"[Morgenzeitung 3] Feedback 2026-10-27"}
        new={"number":2,"updated_at":"2026-10-28T10:00:00Z",
             "title":"[Morgenzeitung 3] Feedback 2026-10-28"}
        def body(date,rating):
            return "MORGENZEITUNG_V3_FEEDBACK_V1\\n".replace("\\n","\n")+json.dumps({
                "date":date,"origin":"website-explicit",
                "ratings":[{"id":"a"*16,"rating":rating,"reason":""}]})
        old["body"]=body("2026-10-27","Sehr relevant")
        new["body"]=body("2026-10-28","Nicht relevant")
        a,_=ingest_feedback({},[new,old],topic)
        b,_=ingest_feedback({},[old,new],topic)
        self.assertEqual(a["article_feedback"]["a"*16]["rating"],"Nicht relevant")
        self.assertEqual(a["article_feedback"],b["article_feedback"])
        self.assertEqual(a["article_feedback"]["a"*16]["source_issue"],"2")
    def test_topic_family_avoids_default_when_new_subtopic(self):
        p={"topic_priorities":{"KI":5,"Industrie & Innovation":5}}
        a=cand(1,topic="KI & Arbeit")
        b=cand(2,topic="Anderes")
        self.assertGreater(score(a,p),score(b,p))
    def test_same_original_url_tracking_is_duplicate_without_network(self):
        a=cand(1);b=cand(2)
        b["url"]=a["url"]+"?utm_source=homepage&fbclid=123"
        self.assertEqual(len(select([a,b],self.profile)),1)

if __name__=="__main__":unittest.main()
