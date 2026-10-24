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
                                 "source": "FAZ", "source_url": "https://www.faz.net/aktuell/wirtschaft/test", "published_at": "2026-10-23T12:00:00+02:00", "verified": True}]).encode()

    def test_capture_and_idempotence(self):
        repo = MemoryPrivateRepo()
        result = capture(repo, "2026-10-24", self.pool)
        self.assertEqual(result["issue_count"], 1)
        self.assertEqual(len(repo.writes), 4)
        capture(repo, "2026-10-24", self.pool)
        self.assertEqual(len(repo.writes), 8)
        self.assertEqual(json.loads(repo.files["snapshots/2026-10-24-issues.json"][0])[0]["number"], 3)

    def test_selection_parameters_preserved(self):
        repo = MemoryPrivateRepo()
        capture(repo, "2026-10-24", self.pool, limit=15, max_per_source=3)
        settings = json.loads(repo.files["snapshots/2026-10-24-selection-parameters.json"][0])
        self.assertEqual(settings, {"limit": 15, "max_per_source": 3})
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            capture(repo, "2026-10-24", self.pool, limit=10, max_per_source=3)

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

    def test_rejects_missing_or_unsafe_source_url(self):
        for url in (None, "http://example.org/story", "https://localhost/story",
                    "https://user:pass@example.org/story", "https://example.org/story#frag"):
            candidate = {"id": "a", "topic": "Industrie", "source": "FAZ",
                         "verified": True}
            if url is not None:
                candidate["source_url"] = url
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "source_url"):
                validate_candidates(json.dumps([candidate]).encode())

    def test_rejects_missing_or_naive_publication_time(self):
        for stamp in (None, "2026-10-23T12:00:00", "not-a-date"):
            candidate = {"id": "a", "topic": "Industrie", "source": "FAZ",
                         "source_url": "https://www.faz.net/aktuell/wirtschaft/test", "verified": True}
            if stamp is not None:
                candidate["published_at"] = stamp
            with self.subTest(stamp=stamp), self.assertRaisesRegex(ValueError, "published_at"):
                validate_candidates(json.dumps([candidate]).encode())

    def test_invalid_date_before_write(self):
        repo = MemoryPrivateRepo()
        with self.assertRaises(ValueError):
            capture(repo, "../escape", self.pool)
        self.assertFalse(repo.writes)


if __name__ == "__main__":
    unittest.main()
