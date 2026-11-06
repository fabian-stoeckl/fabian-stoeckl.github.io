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

    def test_cluster_report_recognizes_equivalent_headlines_without_deleting(self):
        ed=self.edition()
        first,second=ed["headlines"]
        first["title"]="Austrian government announces wind power funding after talks"
        second["title"]="Government announces wind power funding after talks in Austria"
        first["summary"]="The cabinet announced new wind power funding today. Details include financing."
        second["summary"]="After talks the government announced wind power funding. The report discusses politics."
        first.pop("event_key");second.pop("event_key")
        before=[dict(a) for a in ed["headlines"]]
        report=mod.cluster_candidates(ed)
        self.assertEqual(len(report["possible_same_event"]),1)
        self.assertIn("funding",report["possible_same_event"][0]["shared_title_terms"])
        self.assertEqual(ed["headlines"],before,"Clustering must NEVER rewrite or drop articles")
        mod.validate(ed)

    def test_shared_subject_without_same_event_is_not_automatically_clustered(self):
        ed=self.edition()
        first,second=ed["headlines"]
        first["title"]="EU parliament considers new battery recycling law"
        second["title"]="EU parliament hosts conference on battery manufacturing"
        first["summary"]="The draft regulation would change collection and material recovery quotas."
        second["summary"]="Researchers presented manufacturing methods and investment plans."
        first.pop("event_key");second.pop("event_key")
        self.assertEqual(mod.cluster_candidates(ed)["possible_same_event"],[])
        self.assertEqual(len(ed["headlines"]),2)

    def test_explicit_group_recognizes_independent_views_across_sections(self):
        ed=self.edition()
        second=ed["headlines"].pop()
        second.pop("region");second["topic"]="Wirtschaft"
        second["title"]="Economic analysis on climate costs"
        second["distinct_contribution"]="Independent cost analysis supported by the original report"
        ed["articles"].append(second)
        mod.validate(ed)
        report=mod.cluster_candidates(ed)
        self.assertEqual(len(report["explicit_event_groups"]),1)
        self.assertEqual(set(row["section"] for row in report["explicit_event_groups"][0]["articles"]),
                         {"headlines","articles"})
        self.assertFalse(any("document what is genuinely new" in x for x in mod.editorial_warnings(ed)))
        self.assertEqual(len(ed["headlines"])+len(ed["articles"]),2)

    def test_missing_distinct_angle_is_a_warning_not_a_publication_failure(self):
        ed=self.edition()
        mod.validate(ed)
        report=mod.cluster_candidates(ed)
        self.assertEqual(len(report["explicit_event_groups"]),1)
        self.assertEqual(len(report["explicit_event_groups"][0]["articles"]),2)
        self.assertTrue(any("document what is genuinely new" in x for x in mod.editorial_warnings(ed)))
        self.assertEqual(len(ed["headlines"]),2)

    def test_different_event_keys_do_not_suppress_obvious_possible_overlap(self):
        ed=self.edition()
        ed["headlines"][0]["title"]="Finance minister announces carbon tariff reform today"
        ed["headlines"][1]["title"]="Minister announces carbon tariff reform after negotiations"
        ed["headlines"][1]["event_key"]="other-tariff-policy-2026"
        report=mod.cluster_candidates(ed)
        self.assertEqual(len(report["explicit_event_groups"]),0)
        self.assertEqual(len(report["possible_same_event"]),1)

    def test_historical_repeat_checks_only_exact_original_from_real_prior_editions(self):
        ed=self.edition()
        past=self.edition()
        past["date"]="2026-10-28"
        past["headlines"][1]["url"]="https://unrelated.example/story"
        past["headlines"][0]["id"]="c"*16
        old=mod.historical_overlap(ed,[past])
        self.assertEqual(len(old),1)
        self.assertEqual(old[0]["date"],"2026-10-28")
        self.assertEqual(old[0]["reason"],"same_original_url")
        past["preview"]=True
        self.assertEqual(mod.historical_overlap(ed,[past]),[],
                         "Imported previews must never be treated as genuine prior editions")

    def test_cross_language_search_terms_are_hints_not_censorship(self):
        terms=mod.news_terms("Techwerte und Aktien unter Verkaufswelle")
        self.assertTrue({"tech","stock","verkaufswelle"}.issubset(terms))
        self.assertNotIn("und",terms)
        ed=self.edition()
        ed["headlines"][1]["title"]="A completely independent story on research"
        self.assertEqual(len(ed["headlines"]),2)
        self.assertEqual(mod.cluster_candidates(ed)["possible_same_event"],[])

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

    def test_correction_retains_original_article_identity(self):
        ed=self.edition()
        original=ed["headlines"][0]
        original_id,original_url=original["id"],original["url"]
        original["correction"]={
            "corrected_at":"2026-10-30T11:15:00+01:00",
            "previous_summary":"The earlier, incorrect description",
            "note":"Corrected the verified interpretation of the decision.",
            "source_url":"https://example.org/evidence"
        }
        mod.validate(ed)
        self.assertEqual((original["id"],original["url"]),(original_id,original_url))

    def test_correction_must_retain_previous_visible_text_and_valid_date(self):
        ed=self.edition()
        article=ed["headlines"][0]
        article["correction"]={"corrected_at":"2026-10-30T11:15:00+01:00",
            "previous_summary":article["summary"],"note":"Wrong claim",
            "source_url":"https://example.org/evidence"}
        with self.assertRaisesRegex(ValueError,"change"):
            mod.validate(ed)
        article["correction"]["previous_summary"]="Earlier incorrect words"
        article["correction"]["corrected_at"]="2026-10-30T11:15:00"
        with self.assertRaisesRegex(ValueError,"timezone"):
            mod.validate(ed)

    def test_correction_cannot_be_attached_to_imported_preview(self):
        ed=self.edition()
        ed["preview"]=True
        ed["headlines"][0]["correction"]={
            "corrected_at":"2026-10-30T11:15:00+01:00",
            "previous_summary":"Old description","note":"Fixed text",
            "source_url":"https://example.org/evidence"}
        with self.assertRaisesRegex(ValueError,"real edition"):
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
