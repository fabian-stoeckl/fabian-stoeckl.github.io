import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.morgenzeitung_v3_private_ci import changed_dates, verify_changed
from scripts.morgenzeitung_v3_release import private_review

DAY = "2026-10-28"
FILE = "Privat/Morgenzeitung-3/data/" + DAY + ".json"


def fixture():
    articles = [{
        "id": "a"*16, "url": "https://example.org/story/a",
        "title": "Bericht der Regierung", "source": "Testverlag",
        "summary": "Die Regierung stellt einen Bericht vor.",
        "topic": "Politik", "published_at": "2026-10-28T04:00:00Z"
    }]
    headlines = [{
        "id": "b"*16, "url": "https://example.org/story/b",
        "title": "Studie veröffentlicht", "source": "Testverlag",
        "summary": "Eine neue Studie wurde vorgestellt.",
        "region": "International", "published_at": "2026-10-28T04:00:00Z"
    }]
    edition = {
        "date": DAY, "researched_at": "2026-10-28T05:00:00Z",
        "available_at": "2026-10-28T05:10:00Z",
        "preview": False, "articles": articles, "headlines": headlines,
        "selection_audit": {"feedback_applied": False}
    }
    evidence = {"proofs": {
        row["id"]: {"source_url": row["url"], "level": "teaser",
                    "claims": [{"text": row["summary"],
                                "source_excerpt": row["summary"],
                                "supported": True}]}
        for row in articles + headlines
    }, "editorial_review": {
        "approved": True, "reviewed_at": "2026-10-28T05:08:00Z"
    }}
    edition["fact_audit"] = private_review(edition, evidence)
    return edition, evidence


class PrivateCITest(unittest.TestCase):
    def test_no_unrelated_network_or_private_access(self):
        self.assertEqual(changed_dates(["Privat/index.html", "scripts/update_etf_data.py"]), [])
        self.assertRaises(ValueError, changed_dates, ["Privat/Morgenzeitung-3/data/index.json"])

    def test_preview_is_exempt_only_for_historical_date(self):
        from scripts.morgenzeitung_v3_private_ci import verify_changed
        result = verify_changed(".", ["Privat/Morgenzeitung-3/data/2026-10-27.json"],
                                "", fetcher=lambda *_: self.fail("No private call for preview"))
        self.assertEqual(result["preview_skipped"], ["2026-10-27"])

    def test_real_edition_must_match_private_evidence(self):
        edition, evidence = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"Privat/Morgenzeitung-3/data"
            root.mkdir(parents=True)
            (root/"index.json").write_text(json.dumps({"dates":[DAY]}), encoding="utf-8")
            (root/(DAY+".json")).write_text(json.dumps(edition), encoding="utf-8")
            result = verify_changed(tmp, [FILE, "Privat/Morgenzeitung-3/data/index.json"],
                                    "fake-token", fetcher=lambda date,token: evidence)
            self.assertEqual(result["checked"], [DAY])
            tampered = copy.deepcopy(evidence)
            tampered["proofs"]["a"*16]["claims"][0]["source_excerpt"] = (
                "Ein völlig anderes Ereignis wurde veröffentlicht.")
            with self.assertRaisesRegex(ValueError, "private factual review failed"):
                verify_changed(tmp, [FILE], "fake-token", fetcher=lambda date,token: tampered)
            changed = copy.deepcopy(edition)
            changed["articles"][0]["summary"] = "Eine nicht belegte Behauptung."
            (root/(DAY+".json")).write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "private factual review failed"):
                verify_changed(tmp, [FILE], "fake-token", fetcher=lambda date,token: evidence)

    def test_index_or_filename_mismatch_blocks(self):
        edition, evidence = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"Privat/Morgenzeitung-3/data"
            root.mkdir(parents=True)
            (root/"index.json").write_text(json.dumps({"dates":[]}), encoding="utf-8")
            (root/(DAY+".json")).write_text(json.dumps(edition), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing from index"):
                verify_changed(tmp,[FILE],"fake-token",lambda day,token: evidence)


if __name__ == "__main__":
    unittest.main()
