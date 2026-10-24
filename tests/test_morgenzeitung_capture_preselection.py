import json
import unittest
from unittest.mock import patch
from scripts.morgenzeitung_capture_preselection import capture, validate_candidates


class MemoryPrivateRepo:
    def __init__(self):
        self.files = {"profile.json": (b'{"computed_learning_signals":[]}', "blob-sha")}
        self.writes = []

    def read(self, path):
        return self.files.get(path)

    def api(self, path, method="GET", payload=None):
        if path.startswith("/issues?"):
            return [{"number": 3, "updated_at": "2026-10-23T09:00:00Z",
                     "title": "[Morgenzeitung] Sammelbewertung"}]
        raise AssertionError(path)

    def put_immutable(self, path, data):
        existing = self.read(path)
        if existing and existing[0] != data:
            raise ValueError("conflict")
        self.files[path] = (data, "saved")
        self.writes.append(path)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.pool = json.dumps([{"id": "a", "topic": "Industrie",
                                 "source": "FAZ", "verified": True}]).encode()

    def test_capture_and_idempotence(self):
        repo = MemoryPrivateRepo()
        result = capture(repo, "2026-10-24", self.pool)
        self.assertEqual(result["issue_count"], 1)
        self.assertEqual(len(repo.writes), 3)
        capture(repo, "2026-10-24", self.pool)
        self.assertEqual(len(repo.writes), 6)
        self.assertEqual(json.loads(repo.files["snapshots/2026-10-24-issues.json"][0])[0]["number"], 3)

    def test_conflict_prevents_any_new_write(self):
        repo = MemoryPrivateRepo()
        repo.files["snapshots/2026-10-24-profile.json"] = (b'{"old":true}', "old")
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            capture(repo, "2026-10-24", self.pool)
        self.assertFalse(repo.writes)

    def test_rejects_unverified_and_duplicate(self):
        for items in ([{"id":"a","topic":"x","source":"y","verified":False}],
                      [{"id":"a","topic":"x","source":"y","verified":True}]*2):
            with self.assertRaises(ValueError):
                validate_candidates(json.dumps(items).encode())

    def test_invalid_date_before_write(self):
        repo = MemoryPrivateRepo()
        with self.assertRaises(ValueError):
            capture(repo, "../escape", self.pool)
        self.assertFalse(repo.writes)


if __name__ == "__main__":
    unittest.main()
