"""Protect the production/QA chronology and prevent legacy reruns on each merge.

ChatGPT's separate scheduled tasks are managed through its task service;
these tests cover only GitHub Actions workflows committed to the repository.
"""
import re
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
VIENNA = ZoneInfo("Europe/Vienna")


def workflow(name):
    return (WORKFLOWS / name).read_text(encoding="utf-8")


class MorgenzeitungOperatingSchedule(unittest.TestCase):
    def test_private_live_audit_after_freshness_in_both_dst_seasons(self):
        text = workflow("morgenzeitung-private-live-audit.yml")
        self.assertIn("cron: '45 9 * * *'", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("push:", text)  # immediate audit after edition publication remains
        self.assertIn("Privat/Pressespiegel/data/*.json", text)
        for day, expected in [(datetime(2026, 10, 27, tzinfo=timezone.utc), "11:45"),
                              (datetime(2026, 12, 2, tzinfo=timezone.utc), "10:45")]:
            with self.subTest(day=day):
                when_utc = day.replace(hour=9, minute=45)
                local = when_utc.astimezone(VIENNA)
                self.assertEqual(local.strftime("%H:%M"), expected)
                self.assertGreater(local.strftime("%H:%M"), "10:15")
                self.assertLess(local.strftime("%H:%M"), "12:30")

    def test_daily_acceptance_after_new_live_audit(self):
        text = workflow("morgenzeitung-daily-acceptance.yml")
        self.assertIn("cron: '15 12 * * *'", text)
        for day in [datetime(2026, 10, 27, tzinfo=timezone.utc),
                    datetime(2026, 12, 2, tzinfo=timezone.utc)]:
            local = day.replace(hour=12, minute=15).astimezone(VIENNA)
            self.assertGreater(local.strftime("%H:%M"), "12:30")
        self.assertIn("workflow_dispatch:", text)

    def test_production_recovery_stays_enabled_by_schedule(self):
        self.assertIn("cron: '15 8,9 * * *'", workflow("morgenzeitung-freshness.yml"))
        self.assertIn('if [[ "$hhmm" < "1015" ]]; then', workflow("morgenzeitung-freshness.yml"))
        self.assertIn("schedule:", workflow("morgenzeitung-feedback.yml"))
        self.assertIn("cron: '15 4 * * *'", workflow("morgenzeitung-feedback.yml"))
        self.assertIn("pull_request:", workflow("morgenzeitung-prepublication-gate.yml"))
        self.assertIn("pull_request:", workflow("verify-pressespiegel.yml"))

    def test_historical_gates_only_manual_and_unchanged_validation_logic(self):
        for filename in ("morgenzeitung-preview-v3-gate.yml",
                         "morgenzeitung-preview-v6-gate.yml",
                         "morgenzeitung-v7-gate.yml",
                         "morgenzeitung-v8-gate.yml"):
            with self.subTest(filename=filename):
                text = workflow(filename)
                self.assertIn("workflow_dispatch:", text)
                self.assertIn("jobs:", text)
                trigger = text.split("\non:\n", 1)[1].split("\npermissions:\n", 1)[0]
                self.assertNotRegex(trigger, r"(?m)^  (?:push|pull_request|schedule|repository_dispatch|workflow_run):")
                self.assertRegex(text, r"(?m)^  (?:source-preflight|preview-gate|v6-independent-gate):")

    def test_no_redundant_scheduled_legacy_checks(self):
        occurrences = {}
        for path in WORKFLOWS.glob("*.yml"):
            text = path.read_text(encoding="utf-8")
            header = text.split("\npermissions:\n", 1)[0]
            occurrences[path.name] = "  schedule:" in header
        self.assertFalse(occurrences["morgenzeitung-v7-gate.yml"])
        self.assertFalse(occurrences["morgenzeitung-v8-gate.yml"])
        self.assertTrue(occurrences["morgenzeitung-private-live-audit.yml"])
        self.assertTrue(occurrences["morgenzeitung-daily-acceptance.yml"])


if __name__ == "__main__":
    unittest.main()
