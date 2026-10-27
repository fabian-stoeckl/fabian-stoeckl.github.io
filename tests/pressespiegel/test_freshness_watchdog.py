"""Regressions for the free GitHub Morgenzeitung release monitor."""
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
VIENNA = ZoneInfo("Europe/Vienna")


class FreshnessWatchdogTests(unittest.TestCase):
    def test_scheduled_utc_slots_cover_vienna_1015_with_dst(self):
        # GitHub cron has no Europe/Vienna timezone; both slots are necessary.
        scenarios = [
            (datetime(2026, 10, 21, 8, 15, tzinfo=timezone.utc), "1015", True),
            (datetime(2026, 10, 21, 9, 15, tzinfo=timezone.utc), "1115", True),
            (datetime(2026, 12, 2, 8, 15, tzinfo=timezone.utc), "0915", False),
            (datetime(2026, 12, 2, 9, 15, tzinfo=timezone.utc), "1015", True),
        ]
        for utc, local_hhmm, must_check in scenarios:
            with self.subTest(utc=utc):
                hhmm = utc.astimezone(VIENNA).strftime("%H%M")
                self.assertEqual(hhmm, local_hhmm)
                self.assertEqual(hhmm >= "1015", must_check)

    def test_monitor_checks_real_publication_and_raises_actionable_issue(self):
        workflow = (ROOT / ".github/workflows/morgenzeitung-freshness.yml").read_text()
        self.assertIn("15 8,9 * * *", workflow)
        self.assertIn('TZ=Europe/Vienna date +%H%M', workflow)
        self.assertIn("python3 scripts/check_morgenzeitung.py --live --require-today", workflow)
        self.assertIn('if [[ "$hhmm" < "1015" ]]; then', workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn('if: failure() && github.event_name == \'schedule\'', workflow)
        self.assertIn('gh issue create --title "$title" --body "$body"', workflow)
        self.assertIn("gh issue close", workflow)


if __name__ == "__main__":
    unittest.main()
