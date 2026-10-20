"""Offline checks for substantive reporting and verified evidence metadata."""
import copy
import sys
import unittest
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from check_morgenzeitung import validate

class PublicQualityTests(unittest.TestCase):
    def setUp(self):
        self.preview=json.loads((ROOT/"Privat/Pressespiegel/data/2026-10-18.json").read_text())
    def test_reduced_demo_is_not_mistaken_for_real_daily_issue(self):
        self.assertTrue(self.preview.get("preview"))
        self.assertTrue(validate(self.preview))
    def test_short_headline_summaries_are_required(self):
        for day in ("2026-10-18", "2026-10-20"):
            with self.subTest(day=day):
                issue=json.loads((ROOT/"Privat/Pressespiegel/data"/(day+".json")).read_text())
                self.assertTrue(validate(issue))
                self.assertTrue(all(40<=len(x["summary"])<=320 for x in issue["headlines"]))
        bad=copy.deepcopy(self.preview)
        bad["headlines"][0].pop("summary")
        with self.assertRaisesRegex(ValueError,"Zusammenfassungssatz"):validate(bad)

    def test_new_features_require_research_basis(self):
        ed=copy.deepcopy(self.preview)
        ed["preview"]=False
        ed["limitations"]=["Reduced number justified for unit test"]
        with self.assertRaisesRegex(ValueError,"Recherchezugsbasis"):validate(ed)
    def test_source_derived_from_verified_archive(self):
        ed=copy.deepcopy(self.preview)
        ed["preview"]=False
        ed["limitations"]=["Unit-test fixture"]
        for article in ed["articles"]:
            article["research_access"]="verified_archive"
            article["research_reference"]="https://archive.is/https://example.com/article"
            article["research_checked_at"]="2026-10-20T07:00:00+02:00"
        self.assertTrue(validate(ed))
    def test_external_source_requires_exact_domain_and_scheme(self):
        ed=copy.deepcopy(self.preview)
        ed["preview"]=False
        ed["limitations"]=["Unit-test fixture"]
        for article in ed["articles"]:
            article["research_access"]="verified_smry"
            article["research_reference"]="https://smry.ai/https://example.com/post"
            article["research_checked_at"]="2026-10-20T07:00:00+02:00"
        self.assertTrue(validate(ed))
        ed["articles"][0]["research_reference"]="https://not-smry.example/https://source.example"
        with self.assertRaisesRegex(ValueError,"Alternativquelle"):validate(ed)
    def test_not_just_short_news(self):
        ed=copy.deepcopy(self.preview)
        ed["articles"][0]["kind"]="Nachricht"
        with self.assertRaisesRegex(ValueError,"substanzielle Analyse"):validate(ed)
        ed=copy.deepcopy(self.preview)
        ed["articles"][0]["facts"]=["One lonely claim"]
        with self.assertRaisesRegex(ValueError,"zwei belegte Sachverhalte"):validate(ed)

if __name__=="__main__":unittest.main()
