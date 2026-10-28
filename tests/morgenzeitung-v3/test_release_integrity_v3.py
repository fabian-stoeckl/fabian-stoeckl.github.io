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
    def test_existing_historical_edition_v2_remains_untouched_and_valid(self):
        edition=json.loads(Path("Privat/Persoenliche-Zeitung/data/2026-10-28.json").read_text(encoding="utf-8"))
        self.assertEqual(edition["fact_audit"]["audit_version"],LEGACY_RECEIPT_VERSION)
        self.assertEqual(check_public_receipt(edition),[])
        self.assertEqual(edition_hash(edition,LEGACY_RECEIPT_VERSION),edition["fact_audit"]["edition_sha256"])

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
        edition["fact_audit"]["edition_sha256"]=edition_hash(edition,LEGACY_RECEIPT_VERSION)
        self.assertIn("Wrong fact audit version",check_public_receipt(edition))

    def test_none_novelty_score_falls_back_to_legacy_number(self):
        self.assertEqual(validate_article_metadata({"novelty":7,"novelty_score":None}),
                         ["novelty score must be a number from 0 to 5"])


if __name__=="__main__":
    unittest.main()
