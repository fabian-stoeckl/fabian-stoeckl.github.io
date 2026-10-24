"""Guard against silent CI trigger regressions for source-check changes."""
from pathlib import Path
import unittest


class GateWorkflowCoverageTests(unittest.TestCase):
    def test_source_validation_changes_trigger_gate(self):
        workflow = Path(".github/workflows/morgenzeitung-prepublication-gate.yml").read_text()
        for path in (
            "scripts/morgenzeitung_source_evidence.py",
            "scripts/morgenzeitung_live_source_check.py",
            "scripts/morgenzeitung_prepublication_gate.py",
        ):
            with self.subTest(path=path):
                self.assertIn("      - '" + path + "'", workflow)

    def test_real_edition_requires_live_source_check(self):
        workflow = Path(".github/workflows/morgenzeitung-prepublication-gate.yml").read_text()
        self.assertIn("'--check-live-sources'", workflow)
        self.assertIn("if not editions:", workflow)
        self.assertIn("No edition JSON changed; no publication to gate", workflow)


if __name__ == "__main__":
    unittest.main()
