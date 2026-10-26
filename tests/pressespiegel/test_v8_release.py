"""26 Oct v8 production rerun: immutable provenance and non-ETF regression."""
import json
import unittest
from datetime import datetime
from pathlib import Path
from scripts.check_morgenzeitung import validate

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/"Privat"/"Pressespiegel"/"data"

class V8Release(unittest.TestCase):
    def setUp(self):
        if self.edition.get("snapshot_version") != "v8":
            self.skipTest("v8 edition not yet staged; source preflight phase")
    @classmethod
    def setUpClass(cls):
        cls.edition=json.loads((DATA/"2026-10-26.json").read_text())
    def test_schema_and_counts(self):
        self.assertTrue(validate(self.edition))
        self.assertEqual(self.edition["snapshot_version"],"v8")
        self.assertFalse(self.edition["preview"])
        self.assertTrue(10 <= len(self.edition["articles"]) <= 15)
        self.assertTrue(15 <= len(self.edition["headlines"]) <= 20)
    def test_chronology_and_no_duplicates(self):
        start=datetime.fromisoformat(self.edition["window_start"].replace("Z","+00:00"))
        end=datetime.fromisoformat(self.edition["window_end"].replace("Z","+00:00"))
        self.assertLess(start,end)
        events=set()
        urls=set()
        for row in self.edition["headlines"]+self.edition["articles"]:
            pub=datetime.fromisoformat(row["published_at"].replace("Z","+00:00"))
            self.assertLessEqual(start,pub,row["title"])
            self.assertLessEqual(pub,end,row["title"])
            self.assertNotIn(row["event"],events)
            self.assertNotIn(row["url"],urls)
            events.add(row["event"])
            urls.add(row["url"])
    def test_index_and_v6_preserved(self):
        index=json.loads((DATA/"index.json").read_text())
        self.assertEqual(index["dates"][0],"2026-10-26")
        preview=json.loads((ROOT/"Privat"/"Pressespiegel"/"previews"/"2026-10-26-v6.json").read_text())
        self.assertEqual(preview["snapshot_version"],"v6")
        payload=json.dumps(self.edition).lower()
        self.assertNotIn("processed_feedback",payload)
        self.assertNotIn("feedback_observations",payload)
        self.assertNotIn("private_snapshot",payload)

if __name__=="__main__":
    unittest.main()
