import json
import unittest
from scripts.morgenzeitung_prepublication_gate import verify_edition


class Repo:
    def __init__(self):
        day = "2026-10-25"
        self.files = {
            f"candidates/{day}.json": json.dumps([
                {"id": "a", "topic": "Industrie", "source": "FAZ", "verified": True},
                {"id": "b", "topic": "Klima", "source": "ORF", "verified": True},
            ]).encode(),
            f"snapshots/{day}-profile.json": b'{"computed_learning_signals":[]}',
            f"snapshots/{day}-issues.json": b'[]',
            f"snapshots/{day}-selection-parameters.json": b'{"limit":2,"max_per_source":4}',
        }

    def read(self, path):
        return (self.files[path], "sha") if path in self.files else None


class GateTests(unittest.TestCase):
    def test_independent_replay_accepts_exact_order(self):
        result = verify_edition(Repo(), "2026-10-25", {
            "date": "2026-10-25", "articles": [{"id": "a"}, {"id": "b"}]})
        self.assertTrue(result["prepublication_gate_verified"])

    def test_reordering_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_edition(Repo(), "2026-10-25", {
                "date": "2026-10-25", "articles": [{"id": "b"}, {"id": "a"}]})

    def test_missing_snapshot_is_rejected(self):
        repo = Repo()
        del repo.files["snapshots/2026-10-25-profile.json"]
        with self.assertRaisesRegex(ValueError, "Missing original"):
            verify_edition(repo, "2026-10-25", {
                "date": "2026-10-25", "articles": [{"id": "a"}, {"id": "b"}]})

    def test_preview_rejected(self):
        with self.assertRaisesRegex(ValueError, "preview"):
            verify_edition(Repo(), "2026-10-25", {
                "date": "2026-10-25", "preview": True, "articles": [{"id": "a"}, {"id": "b"}]})


if __name__ == "__main__":
    unittest.main()
