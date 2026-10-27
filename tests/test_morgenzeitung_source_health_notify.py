"""Production notification gates: no silent genuine blackout, no false alert."""
import os
import unittest
from unittest.mock import patch, Mock

from scripts.morgenzeitung_source_health_notify import (
    plan_actions, run, AUDIT_TITLE, PREFIX,
)


def result(verdict, date="2026-10-30", *, publishers=(), missing=None):
    records = [{
        "publisher": name, "dates": ["2026-10-28", "2026-10-29", "2026-10-30"],
        "status": "CONFIRMED_RESEARCH_ACCESS_GAP",
    } for name in publishers]
    return {
        "date": date, "verdict": verdict, "confirmed_blackouts": list(publishers),
        "confirmed_blackout_details": records,
        "missing_dates": missing or [],
    }


class SourceHealthNotifications(unittest.TestCase):
    def test_three_day_publisher_blackout_is_not_silent(self):
        actions = plan_actions(result("ACCESS_GAPS", publishers=("NZZ", "BBC News")), [])
        self.assertEqual(len(actions), 2)
        self.assertEqual({a[2] for a in actions},
                         {PREFIX + "NZZ", PREFIX + "BBC News"})
        self.assertTrue(all(a[0] == "create" for a in actions))
        self.assertTrue(all("drei aufeinanderfolgenden Tagen" in a[3] for a in actions))

    def test_idempotent_existing_issues_never_recreate_or_recomment(self):
        old = [{"number": 55, "title": PREFIX + "BBC News"}]
        actions = plan_actions(result("ACCESS_GAPS", publishers=("BBC News",)), old)
        self.assertEqual(actions, [])

    def test_clears_confirmed_outage_after_actual_healthy_three_day_history(self):
        old = [{"number": 4, "title": PREFIX + "NZZ"},
               {"number": 8, "title": AUDIT_TITLE},
               {"number": 99, "title": "Unrelated issue"}]
        actions = plan_actions(result("NO_CONFIRMED_ACCESS_GAPS"), old)
        self.assertEqual({a[1] for a in actions}, {4, 8})
        self.assertEqual({a[0] for a in actions}, {"close"})

    def test_unverified_missing_research_must_not_close_previous_blackout(self):
        old = [{"number": 4, "title": PREFIX + "NZZ"}]
        a = plan_actions(result("AUDIT_GAP", missing=["2026-10-29"]), old)
        self.assertTrue(all(a[0] != "close" for a in a))

    def test_audit_gap_warns_only_after_three_day_rollout_window(self):
        early = result("AUDIT_GAP", date="2026-10-28", missing=["2026-10-27"])
        self.assertEqual(plan_actions(early, []), [])
        late = result("AUDIT_GAP", missing=["2026-10-29"])
        act = plan_actions(late, [])
        self.assertEqual([a[2] for a in act], [AUDIT_TITLE])
        self.assertIn("keine bestätigte Verlagssperre", act[0][3])
        self.assertEqual(plan_actions(late, [{"number": 17, "title": AUDIT_TITLE}]), [])

    def test_no_invented_outages_or_unknown_publishers(self):
        bad = result("ACCESS_GAPS", publishers=("Fake Newspaper",))
        with self.assertRaisesRegex(ValueError, "Unknown publisher"):
            plan_actions(bad, [])
        bad = result("ACCESS_GAPS", publishers=("NZZ",))
        bad["confirmed_blackout_details"] = []
        # Do not pretend an empty/mismatched list is enough for a positive blackout.
        with self.assertRaisesRegex(ValueError, "Mismatch"):
            plan_actions(bad, [])
        with self.assertRaises(ValueError):
            plan_actions({**bad, "confirmed_blackout_details": None}, [])
        with self.assertRaisesRegex(ValueError, "Unrecognized"):
            plan_actions(result("PARTIAL"), [])

    def test_existing_github_token_and_exact_repo_are_required(self):
        with patch.dict(os.environ, {"GH_TOKEN": "", "GITHUB_REPOSITORY": "fabian-stoeckl/fabian-stoeckl.github.io"}):
            with self.assertRaisesRegex(ValueError, "token"):
                run(result("NO_CONFIRMED_ACCESS_GAPS"))
        with patch.dict(os.environ, {"GH_TOKEN": "token", "GITHUB_REPOSITORY": "anyone/else"}):
            with self.assertRaisesRegex(ValueError, "another repository"):
                run(result("NO_CONFIRMED_ACCESS_GAPS"))

    @patch("scripts.morgenzeitung_source_health_notify.subprocess.run")
    def test_uses_existing_token_to_create_exactly_one_github_issue(self, fake):
        fake.return_value = Mock(stdout="[]")
        with patch.dict(os.environ, {"GH_TOKEN": "github-actions", "GITHUB_REPOSITORY": "fabian-stoeckl/fabian-stoeckl.github.io"}):
            run(result("ACCESS_GAPS", publishers=("NZZ",)))
        self.assertEqual(fake.call_count, 2)
        self.assertEqual(fake.call_args.args[0][:3], ["gh", "issue", "create"])
        self.assertIn(PREFIX + "NZZ", fake.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
