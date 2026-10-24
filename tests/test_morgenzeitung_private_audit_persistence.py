"""Static regression guards for private audit persistence paths."""
import pathlib
import unittest

WORKFLOW = (pathlib.Path(__file__).resolve().parents[1] /
            ".github/workflows/morgenzeitung-private-live-audit.yml")


class PrivateAuditPersistenceTests(unittest.TestCase):
    def test_both_immutable_writes_handle_conflicts(self):
        source = WORKFLOW.read_text()
        self.assertIn("Conflicting private audit content", source)
        self.assertIn("Conflicting acceptance report", source)
        self.assertGreaterEqual(source.count("error.code not in (409,422)"), 2)

    def test_api_retries_only_transient_errors(self):
        source = WORKFLOW.read_text()
        self.assertIn("for attempt in range(3):", source)
        self.assertIn("error.code not in (429,500,502,503,504)", source)
        self.assertIn("urllib.error.URLError,TimeoutError", source)

    def test_both_outputs_require_readback(self):
        source = WORKFLOW.read_text()
        self.assertIn("Private audit readback mismatch", source)
        self.assertIn("Acceptance report readback mismatch", source)


if __name__ == "__main__":
    unittest.main()
