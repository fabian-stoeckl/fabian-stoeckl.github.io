import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from scripts.morgenzeitung_v3_private_ci import changed_dates, verify_changed
from scripts.morgenzeitung_v3_release import private_review

DAY = "2026-10-28"
FILE = "Privat/Persoenliche-Zeitung/data/" + DAY + ".json"


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
        self.assertRaises(ValueError, changed_dates, ["Privat/Persoenliche-Zeitung/data/index.json"])

    def test_removed_copy_preview_is_only_allowlisted_retirement(self):
        # The 27 Oct article list was a copy, not an independent issue.
        # Retirement must never consult GitHub's private feedback repository.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"Privat/Persoenliche-Zeitung/data"
            root.mkdir(parents=True)
            (root/"index.json").write_text(json.dumps({"dates":[DAY]}), encoding="utf-8")
            result = verify_changed(tmp, ["Privat/Persoenliche-Zeitung/data/2026-10-27.json",
                                          "Privat/Persoenliche-Zeitung/data/index.json"],
                                    "", fetcher=lambda *_: self.fail("No private call for retired preview"))
            self.assertEqual(result["retired_preview"], ["2026-10-27"])
            with self.assertRaisesRegex(ValueError, "missing from index"):
                verify_changed(tmp, ["Privat/Persoenliche-Zeitung/data/2026-10-26.json"],
                               "", fetcher=lambda *_: self.fail("Unexpected evidence fetch"))
            (root/"2026-10-27.json").write_text(json.dumps({"date":"2026-10-27","preview":True}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing from index"):
                verify_changed(tmp, ["Privat/Persoenliche-Zeitung/data/2026-10-27.json"],
                               "", fetcher=lambda *_: self.fail("Unexpected evidence fetch"))

    def test_new_previews_do_not_bypass_private_evidence_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"Privat/Persoenliche-Zeitung/data"
            root.mkdir(parents=True)
            (root/"index.json").write_text(json.dumps({"dates":[DAY]}), encoding="utf-8")
            (root/(DAY+".json")).write_text(json.dumps({"date":DAY,"preview":True}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot be previews"):
                verify_changed(tmp, [FILE], "",
                               fetcher=lambda *_: self.fail("Unexpected private fetch"))

    def test_real_edition_must_match_private_evidence(self):
        edition, evidence = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/"Privat/Persoenliche-Zeitung/data"
            root.mkdir(parents=True)
            (root/"index.json").write_text(json.dumps({"dates":[DAY]}), encoding="utf-8")
            (root/(DAY+".json")).write_text(json.dumps(edition), encoding="utf-8")
            result = verify_changed(tmp, [FILE, "Privat/Persoenliche-Zeitung/data/index.json"],
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
            root = Path(tmp)/"Privat/Persoenliche-Zeitung/data"
            root.mkdir(parents=True)
            (root/"index.json").write_text(json.dumps({"dates":[]}), encoding="utf-8")
            (root/(DAY+".json")).write_text(json.dumps(edition), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing from index"):
                verify_changed(tmp,[FILE],"fake-token",lambda day,token: evidence)


    def test_exact_migration_avoids_second_private_fetch_but_edited_content_does_not(self):
        """The old public edition is moved, not republished or silently changed."""
        from scripts.morgenzeitung_v3_private_ci import unchanged_migration
        baseline = "a"*40
        day = "2026-10-28"
        original = json.dumps({"date":day,"articles":[]}).encode()
        dates = json.dumps({"dates":[day]}).encode()
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)/"Privat/Persoenliche-Zeitung/data"
            directory.mkdir(parents=True)
            (directory/(day+".json")).write_bytes(original)
            (directory/"index.json").write_bytes(dates)
            def old_git_file(args, **kwargs):
                old_path = args[-1]
                return SimpleNamespace(stdout=dates if old_path.endswith("index.json") else original)
            with patch("scripts.morgenzeitung_v3_private_ci.subprocess.run", side_effect=old_git_file):
                self.assertTrue(unchanged_migration(tmp,day,baseline))
                (directory/(day+".json")).write_bytes(original+b" ")
                self.assertFalse(unchanged_migration(tmp,day,baseline))
                self.assertFalse(unchanged_migration(tmp,"2026-10-29",baseline))



if __name__ == "__main__":
    unittest.main()
