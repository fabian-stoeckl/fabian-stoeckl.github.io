"""Regression: feedback learner must finish before the local editorial run year-round."""
import datetime as dt
import re
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

class ScheduleTests(unittest.TestCase):
    def test_feedback_precedes_editorial_in_summer_and_winter(self):
        workflow = Path(".github/workflows/morgenzeitung-feedback.yml").read_text()
        cron = re.search(r"cron:\s*'([0-9]+) ([0-9]+) \* \* \*'", workflow)
        self.assertIsNotNone(cron, "Scheduled private feedback processing must exist")
        minute, hour = map(int, cron.groups())
        for year, month, day in [(2026, 7, 15), (2026, 11, 15)]:
            utc = dt.datetime(year, month, day, hour, minute, tzinfo=dt.timezone.utc)
            vienna = utc.astimezone(ZoneInfo("Europe/Vienna"))
            self.assertEqual(vienna.date(), utc.date())
            self.assertLessEqual(vienna.hour * 60 + vienna.minute, 6 * 60 + 15,
                                 "Feedback must run >=30 minutes before 06:45 Vienna")

if __name__ == "__main__":
    unittest.main()
