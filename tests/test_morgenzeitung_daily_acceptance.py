"""Fail-closed regressions for the immutable *real* daily acceptance workflow."""
import hashlib
import json
import unittest

from scripts.morgenzeitung_daily_acceptance import (
    REQUIRED, evaluate, inspect_publisher_pages, smoke, REAL_ARTICLES, immutable_acceptance_path
)

DATE = "2026-10-25"


def fixture():
    articles = [{"id": str(i), "source": "ORF", "url": "https://science.orf.at/stories/3237885/",
                 "published_at": "2026-10-23T14:28:00+02:00"} for i in range(10)]
    params = {"limit": 10, "max_per_source": 4}
    issues = [{"number": 3, "updated_at": "2026-10-24T00:00:00Z"}]
    candidates = b'[{"id":"one","verified":true}]'
    profile = b'{"computed_learning_signals":[]}'
    audit = {"candidate_pool_sha256": hashlib.sha256(candidates).hexdigest(),
             "profile_sha256": hashlib.sha256(profile).hexdigest(),
             "issue_versions": issues, "selection_parameters": params,
             "selection_comparison": {"selected_ids": [a["id"] for a in articles]},
             "publication_audit": {"publication_verified": True}}
    run = {"date": DATE, "status": "PASS", "public_merge_commit": "a"*40}
    acceptance = {"date": DATE, "verdict": "PASS"}
    values = {
        "candidates/"+DATE+".json": candidates,
        "snapshots/"+DATE+"-profile.json": profile,
        "snapshots/"+DATE+"-issues.json": json.dumps(issues).encode(),
        "snapshots/"+DATE+"-selection-parameters.json": json.dumps(params).encode(),
        "runs/"+DATE+".json": json.dumps(run).encode(),
        "audits/"+DATE+"-live-learning.json": json.dumps(audit).encode(),
        "audits/"+DATE+"-acceptance.json": json.dumps(acceptance).encode()}
    metadata = [{"evidence": {"status": "match"}}]
    return {"dates": [DATE]}, {"date": DATE, "preview": False, "articles": articles}, values, metadata


class DailyAcceptanceTests(unittest.TestCase):
    def test_complete_genuine_shape_passes_pure_verification(self):
        report = evaluate(DATE, *fixture())
        self.assertEqual(report["verdict"], "PASS")
        self.assertTrue(all(report["checks"].values()))

    def final_evidence_fixture(self):
        index, edition, files, publisher = fixture()
        files["audits/"+DATE+"-acceptance.json"] = json.dumps({
            "date": DATE, "verdict": "PARTIAL",
            "checks": {"feedback_provenance": {"status":"PARTIAL"},
                       "profile_learning":{"status":"PARTIAL"},
                       "production_provenance":{"status":"PARTIAL"}}}).encode()
        files["audits/"+DATE+"-live-learning.json"] = json.dumps({
            **json.loads(files["audits/"+DATE+"-live-learning.json"]),
            "publication_audit":{"publication_verified":True,
                                 "editorial_effect_verified":True}}).encode()
        files["runs/"+DATE+".json"] = json.dumps({
            "date":DATE,"status":"PASS","public_merge_commit":"a"*40,
            "private_readback_verified":True}).encode()
        final = {"date": DATE, "verdict":"PASS",
                 "scope":"productive_feedback_learning_and_publication_not_full_publisher_access",
                 "parent_immutable_acceptance_verdict":"PARTIAL",
                 "checks":{"feedback_provenance":{"status":"PASS"},
                           "profile_learning":{"status":"PASS"},
                           "production_provenance":{"status":"PASS"}},
                 "evidence":{"real_feedback_verification_path":
                                "audits/"+DATE+"-real-feedback-and-profile-verification.json",
                             "live_learning_audit_path":"audits/"+DATE+"-live-learning.json",
                             "private_s7_run_path":"runs/"+DATE+".json",
                             "public_merge_commit":"a"*40,
                             "private_run_readback_verified":True}}
        fb = {"feedback_provenance":{"status":"PASS",
                "unique_ratings_reconciled_against_public_original_editions":55},
              "deterministic_profile_check":{"status":"PASS",
                "stored_computed_learning_signals_match":True}}
        files["audits/"+DATE+"-acceptance-final.json"]=json.dumps(final).encode()
        files["audits/"+DATE+"-real-feedback-and-profile-verification.json"]=json.dumps(fb).encode()
        return index, edition, files, publisher

    def test_immutable_partial_supplemented_by_genuine_final_evidence(self):
        report = evaluate(DATE, *self.final_evidence_fixture())
        self.assertEqual(report["verdict"], "PASS")
        self.assertTrue(report["checks"]["private_acceptance_pass"])

    def test_final_report_alone_never_upgrades_unverified_feedback(self):
        index, edition, files, publisher = self.final_evidence_fixture()
        path = "audits/"+DATE+"-real-feedback-and-profile-verification.json"
        obj = json.loads(files[path])
        obj["feedback_provenance"]["status"] = "PARTIAL"
        files[path] = json.dumps(obj).encode()
        report = evaluate(DATE,index,edition,files,publisher)
        self.assertEqual(report["verdict"], "PARTIAL")

    def test_final_report_requires_real_recovered_run_and_live_editorial_effect(self):
        index, edition, files, publisher = self.final_evidence_fixture()
        runpath = "runs/"+DATE+".json"
        d=json.loads(files[runpath]);d["private_readback_verified"]=False
        files[runpath]=json.dumps(d).encode()
        self.assertEqual(evaluate(DATE,index,edition,files,publisher)["verdict"], "PARTIAL")
        index,edition,files,publisher = self.final_evidence_fixture()
        apath = "audits/"+DATE+"-live-learning.json"
        audit=json.loads(files[apath]);audit["publication_audit"]["editorial_effect_verified"]=False
        files[apath]=json.dumps(audit).encode()
        self.assertEqual(evaluate(DATE,index,edition,files,publisher)["verdict"], "PARTIAL")

    def test_final_acceptance_needs_historical_immutable_partial(self):
        index,edition,files,publisher=self.final_evidence_fixture()
        del files["audits/"+DATE+"-acceptance.json"]
        self.assertEqual(evaluate(DATE,index,edition,files,publisher)["verdict"], "PARTIAL")

    def test_reruns_get_new_immutable_report_path_without_overwriting(self):
        first = immutable_acceptance_path(DATE, 40173569839, 1)
        retry = immutable_acceptance_path(DATE, 40173569839, 2)
        self.assertNotEqual(first, retry)
        self.assertEqual(first, "audits/"+DATE+"-daily-acceptance-40173569839-attempt-1.json")
        self.assertEqual(retry, "audits/"+DATE+"-daily-acceptance-40173569839-attempt-2.json")
        self.assertEqual(immutable_acceptance_path(DATE, "manual", "1"),
                         "audits/"+DATE+"-daily-acceptance-manual-attempt-1.json")
        for date, run, attempt in ((DATE, "bad/../../name", "1"),
                                   ("2026/10/25", "123", "1"),
                                   (DATE, "123", "0"),
                                   (DATE, "123", "-1"),
                                   (DATE, "123", "4/../5")):
            with self.subTest(date=date, run=run, attempt=attempt), self.assertRaises(ValueError):
                immutable_acceptance_path(date, run, attempt)

    def test_missing_snapshot_cannot_be_recreated_or_pass(self):
        index, edition, files, publisher = fixture()
        files.pop("candidates/"+DATE+".json")
        report = evaluate(DATE, index, edition, files, publisher)
        self.assertEqual(report["verdict"], "PARTIAL")
        self.assertIn("candidates/"+DATE+".json", report["missing_original_evidence"])
        self.assertFalse(report["checks"]["private_origins_complete"])

    def test_partial_run_never_counts_as_finished(self):
        index, edition, files, publisher = fixture()
        path = "runs/"+DATE+".json"
        d = json.loads(files[path]); d["status"] = "PARTIAL"
        files[path] = json.dumps(d).encode()
        report = evaluate(DATE, index, edition, files, publisher)
        self.assertEqual(report["verdict"], "PARTIAL")
        self.assertFalse(report["checks"]["private_run_committed"])

    def test_simulated_selection_different_from_live_is_partial(self):
        index, edition, files, publisher = fixture()
        path = "audits/"+DATE+"-live-learning.json"
        d = json.loads(files[path])
        d["selection_comparison"]["selected_ids"] = list(reversed(d["selection_comparison"]["selected_ids"]))
        files[path] = json.dumps(d).encode()
        report = evaluate(DATE, index, edition, files, publisher)
        self.assertEqual(report["verdict"], "PARTIAL")
        self.assertFalse(report["checks"]["public_matches_audited_selection"])

    def test_publisher_conflict_is_fail_not_inconclusive_pass(self):
        index, edition, files, publisher = fixture()
        publisher.append({"evidence": {"status": "conflict"}})
        report = evaluate(DATE, index, edition, files, publisher)
        self.assertEqual(report["verdict"], "FAIL")

    def test_paywall_inconclusive_does_not_count_as_verified(self):
        index, edition, files, _ = fixture()
        report = evaluate(DATE, index, edition, files, [{"evidence": {"status": "inconclusive"}}])
        self.assertEqual(report["verdict"], "PARTIAL")
        self.assertFalse(report["checks"]["publisher_metadata_checked"])

    def test_stale_publication_not_pass(self):
        index, edition, files, publisher = fixture()
        index["dates"] = ["2026-10-24"]
        self.assertFalse(evaluate(DATE, index, edition, files, publisher)["checks"]["public_edition_current"])

    def test_live_fetch_is_original_url_no_archive_and_bounded_per_host(self):
        pages = [{"url": u, "published_at": d, "source": n}
                 for n, u, d in REAL_ARTICLES]
        called = []
        def fake_fetch(url, expected):
            called.append((url, expected))
            return {"status": "match"}
        observed = inspect_publisher_pages(pages + pages, fetch=fake_fetch)
        self.assertEqual(len(observed), 4)
        self.assertEqual(len(called), 4)
        self.assertTrue(all(url.startswith("https://") for url, _ in called))

    def test_real_publisher_fixture_is_genuine_public_news_article(self):
        self.assertGreaterEqual(len(REAL_ARTICLES), 3)
        self.assertEqual(len({u.split("/")[2] for _, u, _ in REAL_ARTICLES}), len(REAL_ARTICLES))
        self.assertTrue(all(d.startswith("2026-10-23T") for _, _, d in REAL_ARTICLES))
        self.assertTrue(all("archive." not in u and "smry." not in u for _, u, _ in REAL_ARTICLES))


if __name__ == "__main__":
    unittest.main()
