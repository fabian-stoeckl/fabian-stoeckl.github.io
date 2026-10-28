"""Proof strength of publication receipts: all editorial text in new editions."""
import copy
import json
from pathlib import Path
import unittest

from scripts.morgenzeitung_v3_release import (
    RECEIPT_VERSION, LEGACY_RECEIPT_VERSION, edition_hash,
    private_review, check_public_receipt, check_private_receipt
)
from scripts.morgenzeitung_v3_schema import validate_article_metadata


class PublicReceiptCoverageTests(unittest.TestCase):
    def test_corrected_historical_edition_uses_complete_v3_receipt(self):
        edition=json.loads(Path("Privat/Persoenliche-Zeitung/data/2026-10-28.json").read_text(encoding="utf-8"))
        self.assertEqual(edition["fact_audit"]["audit_version"],RECEIPT_VERSION)
        self.assertEqual(check_public_receipt(edition),[])
        self.assertEqual(edition_hash(edition),edition["fact_audit"]["edition_sha256"])

    def test_future_receipt_covers_all_editorial_assertions(self):
        row={"id":"a"*16,"source":"Example","title":"New material evidence",
             "url":"https://example.org/article","summary":"Die Wirtschaft verzeichnete eine neue Entwicklung.",
             "topic":"Wirtschaft","published_at":"2026-10-29T06:00:00Z",
             "novelty_explanation":"Die Aussage beruht auf einer neuen Analyse.",
             "why_selected":"Eine neu veröffentlichte Studie erklärt den Mechanismus.",
             "evidence_level":"teaser","article_type":"analysis"}
        edition={"date":"2026-10-29","preview":False,"articles":[row],
                 "headlines":[],"selection_audit":{"feedback_applied":False}}
        dossier={"proofs":{row["id"]:{"source_url":row["url"],"level":"teaser",
            "claims":[{"text":row["summary"],"source_excerpt":row["summary"],"supported":True}]}},
            "editorial_review":{"approved":True,"reviewed_at":"2026-10-29T06:05:00Z"}}
        dossier["proofs"][row["id"]]["fields"]={k:[{"text":row[k],"source_excerpt":"Synthetic fixture metadata: "+row[k],"supported":True}]
            for k in ("why_selected","novelty_explanation","title","source","published_at","article_type")}
        edition["fact_audit"]=private_review(edition,dossier)
        self.assertEqual(edition["fact_audit"]["audit_version"],RECEIPT_VERSION)
        self.assertEqual(check_public_receipt(edition),[])
        self.assertEqual(check_private_receipt(edition,dossier),[])
        for changed_path,new_value in [
            ("novelty_explanation","Ungeprüfte neue Behauptung"),
            ("why_selected","Unbelegte andere Schlussfolgerung"),
            ("summary","Nicht freigegebene Aussage")]:
            corrupted=copy.deepcopy(edition)
            corrupted["articles"][0][changed_path]=new_value
            self.assertIn("Fact audit not bound to current edition",check_public_receipt(corrupted),changed_path)
        corrupted=copy.deepcopy(edition)
        corrupted["selection_audit"]["feedback_applied"]=True
        self.assertIn("Fact audit not bound to current edition",check_public_receipt(corrupted))

    def test_legacy_format_cannot_be_used_for_new_issue(self):
        edition=json.loads(Path("Privat/Persoenliche-Zeitung/data/2026-10-28.json").read_text(encoding="utf-8"))
        edition["date"]="2026-10-29"
        edition["fact_audit"]["audit_version"]=LEGACY_RECEIPT_VERSION
        edition["fact_audit"]["edition_sha256"]=edition_hash(edition,LEGACY_RECEIPT_VERSION)
        self.assertIn("Wrong fact audit version",check_public_receipt(edition))

    def test_two_urls_differing_only_by_tracking_are_duplicate(self):
        from scripts.morgenzeitung_v3_engine import validate_edition
        row={"id":"a"*16,"source":"Journal","title":"Original","summary":"Belegte Aussage",
             "url":"https://example.org/news?utm_source=alpha&x=1",
             "published_at":"2026-10-29T06:10:00Z","topic":"Politik"}
        same={"id":"b"*16,"source":"Journal","title":"Alias",
              "summary":"Belegte Zusammenfassung",
              "url":"https://example.org/news?x=1&UTM_source=beta",
              "published_at":"2026-10-29T06:10:00Z","region":"International"}
        edition={"date":"2026-10-29","preview":True,
                 "researched_at":"2026-10-29T06:15:00Z",
                 "available_at":"2026-10-29T06:20:00Z",
                 "articles":[row],"headlines":[same]}
        self.assertIn("duplicate",validate_edition(edition))

    def test_no_fictitious_source_times_and_invalid_dates(self):
        from scripts.morgenzeitung_v3_engine import valid_publication_date,validate_edition
        self.assertTrue(valid_publication_date("2026-10-27"))
        self.assertTrue(valid_publication_date("2026-10-27T14:32:00+01:00"))
        self.assertFalse(valid_publication_date("2026-02-30"))
        self.assertFalse(valid_publication_date("2026-10-27T14:32:00"))
        row={"id":"a"*16,"title":"Bericht","url":"https://example.org/article",
             "source":"Medium","summary":"Belegte Aussage",
             "topic":"Wirtschaft","published_at":"2026-10-27"}
        headline={**row,"id":"b"*16,"url":"https://example.org/headline",
                  "region":"International"}
        edition={"date":"2026-10-28","preview":True,
                 "researched_at":"2026-10-28T05:30:00Z",
                 "available_at":"2026-10-28T05:40:00Z",
                 "articles":[row],"headlines":[headline]}
        self.assertEqual(validate_edition(edition),[])
        edition["date"]="2026-02-30"
        self.assertIn("invalid date",validate_edition(edition))
        edition["date"]="2026-10-28"
        edition["articles"][0]["published_at"]="2026-02-30"
        self.assertIn("invalid published_at",validate_edition(edition))
        edition["articles"][0]["published_at"]="2026-10-27"
        edition["available_at"]="2026-10-28T05:20:00Z"
        self.assertIn("publication precedes research",validate_edition(edition))

    def test_none_novelty_score_falls_back_to_legacy_number(self):
        self.assertEqual(validate_article_metadata({"novelty":7,"novelty_score":None}),
                         ["novelty score must be a number from 0 to 5"])


if __name__=="__main__":
    unittest.main()
