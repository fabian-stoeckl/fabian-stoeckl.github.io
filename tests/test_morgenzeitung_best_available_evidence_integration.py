"""PR #190: regression of the existing PR #193 triage -> strict preflight contract."""
import unittest
from unittest.mock import patch

from scripts.morgenzeitung_candidate_triage import triage
from scripts.morgenzeitung_source_preflight import preflight


class BestAvailableEvidenceIntegrationTests(unittest.TestCase):
    DATE = "2026-10-27"

    @staticmethod
    def pool(count=20):
        return [
            {"id": f"article-{i}", "source": f"Publisher {i % 4}",
             "source_url": f"https://example.org/article-{i}",
             "published_at": "2026-10-27T09:00:00+00:00",
             "verified": True, "title": f"Article {i}"}
            for i in range(count)
        ]

    @staticmethod
    def checker(items, date, publisher_dates=True):
        item = items[0]
        index = int(item["id"].split("-")[-1])
        verified = index < 15
        return {"checked": [{
            "original_article_http_verified": verified,
            "publisher_feed_verified": False,
        }]}

    def test_unverified_raw_candidates_are_isolated_before_strict_gate(self):
        raw = self.pool()
        # Keep this test focused on separation, not the independent diversity algorithm.
        with patch("scripts.morgenzeitung_candidate_triage.audit_source_diversity",
                   return_value={"diversity_passed": True}), \
             patch("scripts.morgenzeitung_source_preflight.audit_source_diversity",
                   return_value={"diversity_passed": True}):
            result = triage(raw, self.DATE, checker=self.checker)
            self.assertEqual(result["eligible_count"], 15)
            self.assertEqual(result["rejected_count"], 5)
            self.assertTrue(result["ready_for_final_preflight"])
            self.assertTrue(all(x["state"] == "NEEDS_RESEARCH"
                                for x in result["rejected"]))
            self.assertTrue(preflight(result["eligible"], self.DATE,
                                      checker=self.checker)["preflight_passed"])
            # The strict final gate MUST still reject the unfiltered raw pool.
            self.assertFalse(preflight(raw, self.DATE,
                                       checker=self.checker)["preflight_passed"])

    def test_insufficient_verified_pool_never_passes(self):
        with patch("scripts.morgenzeitung_candidate_triage.audit_source_diversity",
                   return_value={"diversity_passed": True}), \
             patch("scripts.morgenzeitung_source_preflight.audit_source_diversity",
                   return_value={"diversity_passed": True}):
            result = triage(self.pool(14), self.DATE, checker=self.checker)
            self.assertFalse(result["ready_for_final_preflight"])
            self.assertFalse(preflight(result["eligible"], self.DATE,
                                       checker=self.checker)["preflight_passed"])

    def test_unverified_feed_flag_is_not_a_triage_pass(self):
        def false_feed(items, date, publisher_dates=True):
            return {"checked": [{"original_article_http_verified": False,
                                 "publisher_feed_verified": True,
                                 "publisher_feed_evidence": None}]}
        with patch("scripts.morgenzeitung_candidate_triage.audit_source_diversity",
                   return_value={"diversity_passed": True}):
            result = triage(self.pool(1), self.DATE, minimum=1,
                            checker=false_feed)
            self.assertEqual(result["eligible_count"], 0)
            self.assertEqual(result["rejected_count"], 1)
            self.assertFalse(result["ready_for_final_preflight"])


if __name__ == "__main__":
    unittest.main()
