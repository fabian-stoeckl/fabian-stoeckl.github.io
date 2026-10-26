"""Regression: replacement S4 is append-only and independently replayed."""
import copy
import json
import unittest
from unittest.mock import patch

from scripts.morgenzeitung_capture_preselection import capture, verify_existing, snapshot_paths
from scripts.morgenzeitung_connector_capture import prepare, verify_readback, blob_sha, REPOSITORY
from scripts.morgenzeitung_prepublication_gate import verify_edition


class MemoryRepo:
    def __init__(self):
        self.files = {"profile.json": (b'{"computed_learning_signals": []}', "p" * 40)}
        self.writes = []

    def read(self, path):
        return self.files.get(path)

    def api(self, path, method="GET", payload=None):
        if path.startswith("/issues?"):
            return [{"number": 3, "updated_at": "2026-10-26T00:00:00Z"}]
        raise AssertionError(path)

    def put_immutable(self, path, data):
        if path in self.files and self.files[path][0] != data:
            raise ValueError("Conflicting immutable snapshot")
        self.files[path] = (data, "a" * 40)
        self.writes.append(path)


class VersionedSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.date = "2026-10-26"
        self.pool = json.dumps([{
            "id": "article1", "topic": "Industrie", "source": "Handelsblatt",
            "source_url": "https://www.handelsblatt.com/story/example",
            "published_at": "2026-10-26T06:00:00Z", "verified": True
        }], ensure_ascii=False).encode()

    def test_v2_does_not_modify_legacy_originals(self):
        repo = MemoryRepo()
        capture(repo, self.date, self.pool)
        original = {k: v for k, v in repo.files.items() if k != "profile.json"}
        capture(repo, self.date, self.pool, version="v2")
        self.assertEqual({k: repo.files[k] for k in original}, original)
        self.assertEqual(len(repo.writes), 8)
        self.assertEqual(len(verify_existing(repo, self.date, version="v2")["verified_paths"]), 4)
        self.assertEqual(len(verify_existing(repo, self.date)["verified_paths"]), 4)

    def test_version_conflict_is_fail_closed(self):
        repo = MemoryRepo()
        capture(repo, self.date, self.pool, version="v2")
        original = dict(repo.files)
        modified = self.pool.replace(b"article1", b"article2")
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            capture(repo, self.date, modified, version="v2")
        self.assertEqual(repo.files, original)

    def test_reject_path_traversal_and_ambiguous_versions(self):
        for version in ("v1", "../v2", "v2/evil", "v02", "latest", "", "V2", 2):
            with self.subTest(version=version), self.assertRaises(ValueError):
                snapshot_paths(self.date, version)
        with self.assertRaises(ValueError):
            snapshot_paths("../2026-10-26", "v2")

    def test_connector_pinned_v2_readback_and_tamper(self):
        profile = '{"computed_learning_signals": []}\\n'
        export = {"repository": REPOSITORY, "commit_sha": "a" * 40,
                  "profile": {"content": profile, "blob_sha": blob_sha(profile)},
                  "issues_pagination_complete": True,
                  "issues": [{"number": 3, "updated_at": "2026-10-26T00:00:00Z"}]}
        manifest = prepare(export, self.date, self.pool, version="v2")
        self.assertEqual(set(manifest["files"]), set(snapshot_paths(self.date, "v2").values()))
        readback = {"repository": REPOSITORY, "commit_sha": "b" * 40,
                    "files": copy.deepcopy(manifest["files"])}
        self.assertTrue(verify_readback(manifest, readback, self.date, version="v2")["connector_readback_matches"])
        with self.assertRaisesRegex(ValueError, "version mismatch"):
            verify_readback(manifest, readback, self.date)
        readback["files"][snapshot_paths(self.date, "v2")["candidates"]]["content"] += " "
        with self.assertRaisesRegex(ValueError, "readback differs"):
            verify_readback(manifest, readback, self.date, version="v2")

    def test_gate_requires_explicit_version_and_uses_v2(self):
        repo = MemoryRepo()
        capture(repo, self.date, self.pool, version="v2")
        edition = {"date": self.date, "snapshot_version": "v2",
                   "articles": [{"id": "article1", "url": "https://www.handelsblatt.com/story/example"}]}
        with patch("scripts.morgenzeitung_prepublication_gate.compare") as compare, \\
             patch("scripts.morgenzeitung_prepublication_gate.audit_sources") as audit:
            compare.return_value = {"selected_ids": ["article1"], "counterfactual_effect_verified": False}
            audit.return_value = {"source_url_structure_verified": True}
            result = verify_edition(repo, self.date, edition)
        self.assertEqual(result["snapshot_version"], "v2")
        with self.assertRaisesRegex(ValueError, "Missing original"):
            verify_edition(repo, self.date, {**edition, "snapshot_version": None})


if __name__ == "__main__":
    unittest.main()
