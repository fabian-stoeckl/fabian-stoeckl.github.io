"""Prevent S7 from auditing stale v1 originals after a versioned republication."""
import unittest
from pathlib import Path
from scripts.morgenzeitung_capture_preselection import snapshot_paths


class VersionedS7WorkflowTests(unittest.TestCase):
    def test_legacy_and_versioned_paths_are_disjoint(self):
        old = snapshot_paths("2026-10-26")
        new = snapshot_paths("2026-10-26", "v2")
        self.assertFalse(set(old.values()) & set(new.values()))
        self.assertEqual(old["candidates"], "candidates/2026-10-26.json")
        self.assertEqual(new["candidates"], "candidates/2026-10-26-v2.json")

    def test_s7_reads_edition_pinned_version_not_legacy_hardcoded(self):
        text = Path(".github/workflows/morgenzeitung-private-live-audit.yml").read_text()
        self.assertIn("edition.get('snapshot_version')", text)
        self.assertIn("names=snapshot_paths(date,version)", text)
        self.assertIn("candidate_path=names['candidates']", text)
        self.assertIn("profile_snapshot_path=names['profile']", text)
        self.assertIn("issue_snapshot_path=names['issues']", text)
        self.assertIn("parameter_path=names['parameters']", text)
        self.assertNotIn("candidate_path='candidates/'+date+'.json'", text)

    def test_append_only_v2_audits_do_not_collide_with_legacy(self):
        text = Path(".github/workflows/morgenzeitung-private-live-audit.yml").read_text()
        self.assertIn("suffix='-'+version if version else ''", text)
        self.assertIn("dest='audits/'+date+suffix+'-live-learning.json'", text)
        self.assertIn("report_dest='audits/'+date+suffix+'-acceptance.json'", text)
        self.assertIn("result['snapshot_version']=version", text)


if __name__ == "__main__":
    unittest.main()
