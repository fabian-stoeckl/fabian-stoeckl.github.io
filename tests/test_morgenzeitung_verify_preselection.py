import json
import unittest
from scripts.morgenzeitung_capture_preselection import verify_existing


DATE = "2026-10-25"


class Repo:
    def __init__(self):
        self.data = {
            f"candidates/{DATE}.json": json.dumps([{"id": "article1", "topic": "Industrie", "source": "Handelsblatt", "source_url": "https://www.handelsblatt.com/politik/test", "verified": True}]).encode(),
            f"snapshots/{DATE}-profile.json": b'{"computed_learning_signals":[]}',
            f"snapshots/{DATE}-issues.json": b'[]',
            f"snapshots/{DATE}-selection-parameters.json": b'{"limit":10,"max_per_source":4}',
        }

    def read(self, path):
        return (self.data[path], "sha") if path in self.data else None


class VerifyExistingTests(unittest.TestCase):
    def test_four_originals_required(self):
        repo = Repo()
        result = verify_existing(repo, DATE)
        self.assertEqual(len(result["verified_paths"]), 4)
        self.assertEqual(result["parameters"]["limit"], 10)

    def test_missing_snapshot_fails(self):
        repo = Repo()
        del repo.data[f"snapshots/{DATE}-issues.json"]
        with self.assertRaisesRegex(ValueError, "Missing original"):
            verify_existing(repo, DATE)

    def test_invalid_candidate_fails(self):
        repo = Repo()
        repo.data[f"candidates/{DATE}.json"] = b'[{"id":"article1","topic":"Industrie","source":"Handelsblatt","verified":false}]'
        with self.assertRaises(ValueError):
            verify_existing(repo, DATE)

    def test_duplicate_issue_versions_fail(self):
        repo = Repo()
        repo.data[f"snapshots/{DATE}-issues.json"] = b'[{"number":3,"updated_at":"2026-10-24T10:00:00Z"},{"number":3,"updated_at":"2026-10-24T11:00:00Z"}]'
        with self.assertRaisesRegex(ValueError, "Duplicate original issue"):
            verify_existing(repo, DATE)

    def test_malformed_issue_versions_fail(self):
        repo = Repo()
        repo.data[f"snapshots/{DATE}-issues.json"] = b'[{"number":true,"updated_at":"2026-10-24T10:00:00Z"}]'
        with self.assertRaisesRegex(ValueError, "Invalid original issue"):
            verify_existing(repo, DATE)

    def test_invalid_parameters_fail(self):
        repo = Repo()
        repo.data[f"snapshots/{DATE}-selection-parameters.json"] = b'{"limit":20,"max_per_source":4}'
        with self.assertRaises(ValueError):
            verify_existing(repo, DATE)


if __name__ == "__main__":
    unittest.main()
