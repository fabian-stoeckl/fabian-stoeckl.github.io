"""Safety contract for automatic private feedback refresh after main merge."""
import unittest
from pathlib import Path

WORKFLOW = Path(".github/workflows/morgenzeitung-feedback.yml")
class FeedbackWorkflowContract(unittest.TestCase):
    def test_trusted_main_push_refreshes_real_private_profile(self):
        text = WORKFLOW.read_text()
        self.assertIn("branches: [main]", text)
        self.assertIn("github.event_name == 'push'", text)
        self.assertIn("github.event_name == 'schedule'", text)
        self.assertIn("write_profile_if_unchanged(api", text)
        self.assertIn("write_profile_if_unchanged", text)
    def test_never_commit_private_profile_to_public_repo(self):
        text = WORKFLOW.read_text()
        self.assertIn("MORGENZEITUNG_FEEDBACK_TOKEN", text)
        self.assertIn("applied=write_profile_if_unchanged", text)
        self.assertNotIn("git add profile.json", text)
        self.assertNotIn("git push", text)
    def test_live_publication_gate_before_private_apply(self):
        text = WORKFLOW.read_text()
        self.assertLess(text.index("Verified public edition:"), text.index("applied=write_profile_if_unchanged"))
        self.assertIn("raise ValueError('Live edition/index mismatch')", text)
        self.assertIn("raise ValueError('Latest live edition is only a preview')", text)

if __name__ == "__main__":
    unittest.main()
