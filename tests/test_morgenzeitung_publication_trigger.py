"""Guard against broken edition-path detection in the live audit workflow."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/morgenzeitung-private-live-audit.yml"


class PublicationTriggerTests(unittest.TestCase):
    def test_push_diff_uses_complete_history_and_event_range(self):
        workflow = WORKFLOW.read_text()
        self.assertIn('fetch-depth: 0', workflow)
        self.assertIn('PUSH_BEFORE: ${{ github.event.before }}', workflow)
        self.assertIn("['git','diff','--name-only',before,os.environ['GITHUB_SHA']]", workflow)
        self.assertNotIn("'diff-tree'", workflow)

    def test_private_audit_runs_are_serialized(self):
        workflow = WORKFLOW.read_text()
        self.assertIn('concurrency:', workflow)
        self.assertIn('group: morgenzeitung-private-live-audit', workflow)
        self.assertIn('cancel-in-progress: false', workflow)

    def test_push_path_is_monitored(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("  push:", workflow)
        self.assertIn("'Privat/Pressespiegel/data/*.json'", workflow)
        self.assertIn("  schedule:", workflow)

    def test_edition_filename_regex_matches_real_paths(self):
        pattern = r"Privat/Pressespiegel/data/\d{4}-\d{2}-\d{2}\.json"
        workflow = WORKFLOW.read_text()
        self.assertIn(pattern, workflow)
        self.assertTrue(re.fullmatch(pattern, "Privat/Pressespiegel/data/2026-10-24.json"))
        self.assertFalse(re.fullmatch(pattern, "Privat/Pressespiegel/data/index.json"))
        self.assertFalse(re.fullmatch(pattern, "Privat/Pressespiegel/data/2026-10-24.json.bak"))

    def test_date_validation_regex(self):
        pattern = r"\d{4}-\d{2}-\d{2}"
        self.assertIn(pattern, WORKFLOW.read_text())
        self.assertTrue(re.fullmatch(pattern, "2026-10-24"))
        self.assertFalse(re.fullmatch(pattern, "../2026-10-24"))


if __name__ == "__main__":
    unittest.main()
