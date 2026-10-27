"""Keep Morgenzeitung article relevance independent of automated full-text access.

These are deterministic regression checks, not publisher availability tests:
full article bodies may still be blocked in GitHub or ChatGPT environments.
"""
import copy
import unittest
from unittest.mock import patch

from scripts.morgenzeitung_editorial import select_articles
from scripts.morgenzeitung_selection_audit import check_access_neutrality, compare


def pool():
    return [
        {"id": "faz", "topic": "Industrie & Rohstoffe", "source": "FAZ",
         "verified": True, "access": "teaser", "paywall": True},
        {"id": "orf", "topic": "Industrie & Rohstoffe", "source": "ORF",
         "verified": True, "access": "full", "paywall": False},
        {"id": "handelsblatt", "topic": "Industrie & Rohstoffe", "source": "Handelsblatt",
         "verified": True, "access": "metadata"},
        {"id": "nzz", "topic": "Finanzen", "source": "NZZ",
         "verified": True, "access": "teaser"},
        {"id": "bbc", "topic": "Technologie", "source": "BBC News",
         "verified": True, "access": "full"},
    ]


PROFILE = {"computed_learning_signals": [
    {"topic": "Industrie", "confidence": "preliminary", "direction": "positive"}
]}


class AccessNeutralityTests(unittest.TestCase):
    def test_same_relevance_evidence_same_ranking_regardless_of_fulltext(self):
        p = pool()
        saved = copy.deepcopy(p)
        full, _ = select_articles(p, PROFILE, limit=3, max_per_source=3)
        self.assertEqual([r["id"] for r in full], ["faz", "orf", "handelsblatt"])
        for mode in ("full", "teaser", "metadata"):
            trial = [dict(x, access=mode, paywall=mode != "full",
                          fulltext_available=mode == "full") for x in p]
            selected, _ = select_articles(trial, PROFILE, limit=3, max_per_source=3)
            self.assertEqual([r["id"] for r in selected],
                             [r["id"] for r in full])
        self.assertEqual(p, saved)

    def test_live_selection_audit_checks_access_parity(self):
        report = compare(pool(), PROFILE, limit=3, max_per_source=3)
        self.assertTrue(report["access_neutrality_verified"])
        self.assertEqual(report["selected_ids"], ["faz", "orf", "handelsblatt"])
        self.assertTrue(check_access_neutrality(pool(), PROFILE, limit=3, max_per_source=3))

    def test_meta_only_candidate_must_still_be_source_verified(self):
        p = pool()
        p[0]["verified"] = False
        with self.assertRaisesRegex(ValueError, "source-verified"):
            compare(p, PROFILE, limit=3)

    def test_future_access_weight_leak_fails_closed(self):
        real_select = select_articles

        # A deliberately biased future implementation would be detected.
        def biased(items, profile, *, limit, max_per_source):
            if items[0].get("access") != "full":
                items = list(reversed(items))
            return real_select(items, profile, limit=limit, max_per_source=max_per_source)

        from scripts import morgenzeitung_selection_audit as module
        with patch.object(module, "select_articles", side_effect=biased):
            with self.assertRaisesRegex(ValueError, "Access-based selection bias"):
                check_access_neutrality(pool(), PROFILE, limit=3, max_per_source=3)


if __name__ == "__main__":
    unittest.main()
