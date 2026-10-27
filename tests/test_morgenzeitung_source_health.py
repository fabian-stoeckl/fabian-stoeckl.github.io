"""Regression suite: feed sampling cannot masquerade as editorial access.

Covers all mandatory publishers, missing source records and three-day notices.
"""
import copy
import datetime as dt
import unittest

from scripts.morgenzeitung_official_feeds import FEEDS
from scripts.morgenzeitung_source_health import (
    REQUIRED_SOURCES, feed_health, validate_editorial_report, multi_day_alerts,
)


def smoke():
    return {"report_type": "real_publisher_first_party_feed_smoke",
            "results": [
                {"publisher": name, "status": "FEED_READABLE",
                 "items": 12, "working_feed": feeds[0][0],
                 "identity_status": "LIVE_IDENTITY_MATCH"}
                for name, feeds in FEEDS.items()]}


def editorial(day, *, blocked=(), unchecked=(), selected=None):
    entries = []
    for name in REQUIRED_SOURCES:
        if name in blocked:
            outcome = "NO_VERIFIABLE_ARTICLES"
        elif name in unchecked:
            outcome = "NOT_CHECKED"
        else:
            outcome = "VERIFIED_ARTICLES"
        entries.append({
            "publisher": name, "outcome": outcome,
            "verified_original_count": 0 if outcome != "VERIFIED_ARTICLES" else 1,
            "attempted_methods": (["direct_original", "official_publisher_feed"]
                                  if outcome == "NO_VERIFIABLE_ARTICLES"
                                  else ["direct_original"]),
            "attempt_evidence": (["original HTTP 403 and article hash a",
                                  "publisher feed no same original URL b"]
                                 if outcome == "NO_VERIFIABLE_ARTICLES" else []),
            "selected_count": 0 if selected is None else selected,
        })
    return {"report_type": "source_editorial_research",
            "date": day, "research_complete": True, "publishers": entries}


class SourceHealthTests(unittest.TestCase):
    def test_every_source_checked_even_without_rss_adapter(self):
        report = feed_health(smoke(), "2026-10-27", run_id="github-123")
        self.assertEqual(report["publisher_count"], len(REQUIRED_SOURCES))
        self.assertEqual(report["feed_adapters"], len(FEEDS))
        self.assertEqual(report["live_identity_sample_confirmed"], len(FEEDS))
        by_source = {r["publisher"]: r for r in report["publishers"]}
        self.assertEqual(by_source["Reuters"]["feed_status"],
                         "NO_OFFICIAL_FEED_CONFIGURED")
        self.assertFalse(by_source["Reuters"]["editorial_research_confirmed"])
        self.assertIsNone(by_source["The Guardian"]["fulltext_available"])
        self.assertTrue(by_source["The Guardian"]["official_feed_sample_article_identity_confirmed"])

    def test_readable_without_identity_is_not_article_verification(self):
        x = smoke()
        x["results"][0]["identity_status"] = "NO_SAMPLE_MATCH"
        r = feed_health(x, "2026-10-27")
        self.assertEqual(r["live_identity_sample_confirmed"], len(FEEDS)-1)
        row = next(z for z in r["publishers"]
                   if z["publisher"] == x["results"][0]["publisher"])
        self.assertEqual(row["feed_status"], "FEED_READABLE_IDENTITY_UNPROVEN")
        self.assertFalse(row["official_feed_sample_article_identity_confirmed"])

    def test_missing_or_duplicate_feed_evidence_is_rejected(self):
        x = smoke()
        x["results"].append(x["results"][0])
        with self.assertRaises(ValueError):
            feed_health(x, "2026-10-27")
        x = smoke()
        x["results"][0]["publisher"] = "Mystery Source"
        with self.assertRaises(ValueError):
            feed_health(x, "2026-10-27")

    def test_no_editorial_ledger_no_blackout_claim(self):
        r = multi_day_alerts("2026-10-27", [])
        self.assertEqual(r["verdict"], "AUDIT_GAP")
        self.assertFalse(r["confirmed_blackouts"])
        self.assertEqual(len(r["missing_dates"]), 3)

    def test_one_day_of_blocked_feed_does_not_trigger_publisher_blackout(self):
        reports = [editorial(day, blocked=("NZZ",) if day.endswith("27") else ())
                   for day in ("2026-10-25", "2026-10-26", "2026-10-27")]
        r = multi_day_alerts("2026-10-27", reports)
        self.assertEqual(r["verdict"], "NO_CONFIRMED_ACCESS_GAPS")

    def test_three_verified_days_without_article_evidence_raise_single_clear_alert(self):
        reports = [editorial(day, blocked=("BBC News", "NZZ"))
                   for day in ("2026-10-25", "2026-10-26", "2026-10-27")]
        r = multi_day_alerts("2026-10-27", reports)
        self.assertEqual(r["verdict"], "ACCESS_GAPS")
        self.assertEqual({p["publisher"] for p in r["confirmed_blackouts"]},
                         {"BBC News", "NZZ"})
        self.assertEqual(len(r["confirmed_blackouts"][0]["dates"]), 3)

    def test_zero_selected_articles_is_not_a_source_outage(self):
        reports = [editorial(day, selected=0)
                   for day in ("2026-10-25", "2026-10-26", "2026-10-27")]
        r = multi_day_alerts("2026-10-27", reports)
        self.assertEqual(r["verdict"], "NO_CONFIRMED_ACCESS_GAPS")

    def test_documented_access_requires_both_direct_and_independent_attempt(self):
        report = editorial("2026-10-27", blocked=("FAZ",))
        target = next(r for r in report["publishers"] if r["publisher"] == "FAZ")
        target["attempted_methods"] = ["direct_original"]
        with self.assertRaisesRegex(ValueError, "alternative attempt"):
            validate_editorial_report(report)

    def test_missing_source_not_misclassified_as_blocked(self):
        x = editorial("2026-10-27", blocked=("FAZ",))
        x["publishers"] = x["publishers"][:-1]
        with self.assertRaisesRegex(ValueError, "Missing mandatory"):
            validate_editorial_report(x)

    def test_no_unchecked_publishers_in_claimed_complete_research(self):
        x = editorial("2026-10-27", unchecked=("The Guardian",))
        with self.assertRaisesRegex(ValueError, "unexamined"):
            validate_editorial_report(x)

    def test_missing_middle_day_is_audit_gap_not_false_access_warning(self):
        x = [editorial("2026-10-25", blocked=("BBC News",)),
             editorial("2026-10-27", blocked=("BBC News",))]
        r = multi_day_alerts("2026-10-27", x)
        self.assertEqual(r["verdict"], "AUDIT_GAP")
        self.assertEqual(r["missing_dates"], ["2026-10-26"])

    def test_duplicate_or_future_editorial_date_cannot_hide_history(self):
        day = editorial("2026-10-27")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            multi_day_alerts("2026-10-27", [day, copy.deepcopy(day)])
        with self.assertRaisesRegex(ValueError, "Future"):
            multi_day_alerts("2026-10-27", [editorial("2026-10-28")])

    def test_unsuitable_not_allowed_to_hide_unverified_publisher(self):
        report = editorial("2026-10-27", blocked=("NZZ",))
        row = next(r for r in report["publishers"] if r["publisher"] == "NZZ")
        row["outcome"] = "NO_SUITABLE_ARTICLES"
        with self.assertRaisesRegex(ValueError, "requires independently verified"):
            validate_editorial_report(report)

    def test_some_verified_articles_can_be_all_rejected_for_relevance(self):
        doc = editorial("2026-10-27")
        row = doc["publishers"][0]
        row["outcome"] = "NO_SUITABLE_ARTICLES"
        row["verified_original_count"] = 5
        self.assertEqual(validate_editorial_report(doc)[row["publisher"]]["verified_original_count"], 5)


if __name__ == "__main__":
    unittest.main()
