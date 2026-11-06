"""Small editorial-metadata regression: no automated topical censorship."""
import importlib.util
import hashlib
import json
import pathlib
import subprocess
import sys
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

    def test_cli_review_on_actual_latest_issue_is_read_only(self):
        folder=root/"Privat/Pressespiegel/data"
        index=folder/"index.json"
        days=json.loads(index.read_text(encoding="utf-8"))["dates"]
        latest=days[0]
        edition=folder/(latest+".json")
        before=(hashlib.sha256(index.read_bytes()).hexdigest(),
                hashlib.sha256(edition.read_bytes()).hexdigest())
        process=subprocess.run(
            [sys.executable,str(root/"scripts/morgenzeitung_neu.py"),"cluster-review",
             "--root",str(folder),"--date",latest,"--previous-days","3"],
            cwd=root,capture_output=True,text=True,check=True
        )
        self.assertIn("CLUSTER REVIEW "+latest,process.stdout)
        self.assertIn("EDITORIAL DECISION REQUIRED",process.stdout)
        after=(hashlib.sha256(index.read_bytes()).hexdigest(),
               hashlib.sha256(edition.read_bytes()).hexdigest())
        self.assertEqual(before,after,"Review must never mutate public editions")

    def test_publisher_diversity_advisory_detects_source_clumping_without_deletion(self):
        ed=self.edition()
        ed["headlines"]=[]
        for i in range(9):
            a=story(f"{i:016x}",f"https://distinct.example/{i}",f"test-event-{i}")
            a["source"]="Reuters" if i<6 else ("ORF Science" if i==6 else "ORF")
            ed["headlines"].append(a)
        original=json.dumps(ed,sort_keys=True)
        snapshot=mod.diversity_snapshot(ed)
        total=snapshot["sections"]["Gesamtausgabe"]
        self.assertEqual(total["total"],9)
        self.assertEqual(total["distinct_source_groups"],2)
        self.assertEqual(total["sources"][0],{"source":"Reuters","count":6})
        self.assertEqual(total["sources"][1],{"source":"ORF","count":3})
        self.assertTrue(any(a["source"]=="Reuters" for a in snapshot["alerts"]))
        self.assertEqual(json.dumps(ed,sort_keys=True),original)
        mod.validate(ed)

    def test_source_diversity_does_not_reject_a_legitimate_single_publisher(self):
        ed=self.edition()
        ed["headlines"]=[]
        for i in range(7):
            a=story(f"{i:016x}",f"https://independent.example/{i}",f"independent-event-{i}")
            a["source"]="Financial Times"
            ed["headlines"].append(a)
        self.assertTrue(mod.diversity_snapshot(ed)["alerts"])
        self.assertEqual(len(ed["headlines"]),7)
        mod.validate(ed)
        self.assertEqual(len(mod.cluster_candidates(ed)["explicit_event_groups"]),0,
                         "Source concentration does not prove identical events")

    def test_different_outlets_same_group_never_assumed_independent_confirmation(self):
        ed=self.edition()
        ed["headlines"][0]["source"]="ORF"
        ed["headlines"][1]["source"]="ORF Science"
        snap=mod.diversity_snapshot(ed)
        self.assertEqual(snap["sections"]["Heute wichtig"]["distinct_source_groups"],1)
        self.assertEqual(snap["all_sources"][0]["source"],"ORF")
        self.assertEqual(snap["all_sources"][0]["count"],2)

    def test_historical_signals_use_only_real_nonidentical_issues(self):
        ed=self.edition()
        ed["headlines"]=[]
        for i in range(6):
            ed["headlines"].append(story(f"{i:016x}",f"https://new.example/{i}",f"event-{i}"))
        past=json.loads(json.dumps(ed))
        past["date"]="2026-10-28"
        past["headlines"][0]["id"]="f"*16
        past["headlines"][0]["url"]="https://new.example/replacement"
        self.assertEqual(len(mod.recurring_concentration(ed,[past])),1)
        self.assertEqual(mod.recurring_concentration(ed,[{**past,"preview":True}]),[])
        self.assertEqual(mod.recurring_concentration(ed,[{**past,"date":ed["date"]}]),[])
        self.assertEqual(len(ed["headlines"]),6)

    def test_diversity_review_never_rewrites_original_or_index(self):
        folder=root/"Privat/Pressespiegel/data"
        idx=folder/"index.json"
        latest=json.loads(idx.read_text(encoding="utf-8"))["dates"][0]
        edition=folder/(latest+".json")
        before=(hashlib.sha256(idx.read_bytes()).hexdigest(),
                hashlib.sha256(edition.read_bytes()).hexdigest())
        proc=subprocess.run(
            [sys.executable,str(root/"scripts/morgenzeitung_neu.py"),"diversity-review",
             "--root",str(folder),"--date",latest,"--previous-days","3"],
            cwd=root,capture_output=True,text=True,check=True
        )
        self.assertIn("DIVERSITY REVIEW "+latest,proc.stdout)
        self.assertIn("NO AUTOMATIC ACTION:",proc.stdout)
        self.assertIn("PERSONALIZATION SAFEGUARD:",proc.stdout)
        self.assertIn("PUBLICATION SOURCES Vertiefungen",proc.stdout)
        after=(hashlib.sha256(idx.read_bytes()).hexdigest(),
               hashlib.sha256(edition.read_bytes()).hexdigest())
        self.assertEqual(before,after)

    def test_imported_preview_does_not_create_bubble_conclusions(self):
        ed=self.edition()
        ed["preview"]=True
        self.assertFalse(mod.diversity_snapshot(ed)["alerts"])
        self.assertFalse(mod.recurring_concentration(ed,[]))

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
