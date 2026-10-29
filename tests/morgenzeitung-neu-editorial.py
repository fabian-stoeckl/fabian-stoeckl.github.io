"""Small editorial-metadata regression: no automated topical censorship."""
import importlib.util
import pathlib
import unittest

root=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("morgenzeitung_neu",root/"scripts/morgenzeitung_neu.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def story(id, url, event="eu-climate-decision-2026"):
    return {"id":id,"title":"Verified original title","source":"Test outlet",
            "summary":"An explicitly supported short claim","url":url,
            "published_at":"2026-10-29","region":"International",
            "evidence_level":"teaser","event_key":event}


class EditorialEventTests(unittest.TestCase):
    def edition(self):
        return {"date":"2026-10-29","researched_at":"2026-10-29T05:15:00+01:00",
                "preview":False,"articles":[],
                "headlines":[story("a"*16,"https://a.example/a"),
                             story("b"*16,"https://b.example/b")]}

    def test_detects_shared_event_without_silently_dropping_a_source(self):
        ed=self.edition()
        mod.validate(ed)
        self.assertEqual(len(ed["headlines"]),2)
        self.assertTrue(any("eu-climate-decision" in x for x in mod.editorial_warnings(ed)))

    def test_distinct_angle_allows_both_articles(self):
        ed=self.edition()
        ed["headlines"][1]["distinct_contribution"]="Verified independent cost analysis"
        mod.validate(ed)
        self.assertEqual(mod.editorial_warnings(ed),[])

    def test_missing_event_key_is_advisory_not_a_blocker(self):
        ed=self.edition()
        for a in ed["headlines"]: a.pop("event_key")
        mod.validate(ed)
        self.assertTrue(any("no event_key" in x for x in mod.editorial_warnings(ed)))

    def test_invalid_event_key_is_an_actual_structural_error(self):
        ed=self.edition()
        ed["headlines"][0]["event_key"]="Bad Event With Spaces"
        with self.assertRaisesRegex(ValueError,"event key"):
            mod.validate(ed)

    def test_related_article_must_be_independent(self):
        ed=self.edition()
        ed["headlines"][0]["related_article"]={
            "title":"Different original report", "source":"Another publisher",
            "url":"https://example.org/original"
        }
        mod.validate(ed)
        ed["headlines"][0]["related_article"]["url"]=ed["headlines"][0]["url"]
        with self.assertRaisesRegex(ValueError,"different original"):
            mod.validate(ed)

    def test_malformed_related_article_not_published(self):
        ed=self.edition()
        ed["headlines"][0]["related_article"]={"title":"Context"}
        with self.assertRaisesRegex(ValueError,"Incomplete related"):
            mod.validate(ed)

    def test_preview_stays_historical_without_new_editorial_requirements(self):
        ed=self.edition()
        ed["preview"]=True
        self.assertEqual(mod.editorial_warnings(ed),[])

    def test_exact_duplicate_original_url_remains_prohibited(self):
        ed=self.edition()
        ed["headlines"][1]["url"]=ed["headlines"][0]["url"]
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            mod.validate(ed)


if __name__=="__main__":
    unittest.main()
