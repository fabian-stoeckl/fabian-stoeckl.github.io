import unittest
from scripts.morgenzeitung_provenance import verify_commit_chronology


def evidence(t="2026-10-24T05:00:00Z"):
    return {k: {"sha": "a" * 40, "timestamp": t}
            for k in ("candidates", "profile", "issues", "parameters")}


PUBLIC = {"sha": "b" * 40, "timestamp": "2026-10-24T06:00:00Z"}


class ChronologyTests(unittest.TestCase):
    def test_private_commits_before_publication(self):
        result = verify_commit_chronology(evidence(), PUBLIC)
        self.assertTrue(result["chronology_verified"])
        self.assertIn("does not prove", result["limitation"])

    def test_missing_private_snapshot_commit(self):
        originals = evidence()
        del originals["issues"]
        with self.assertRaisesRegex(ValueError, "Four original"):
            verify_commit_chronology(originals, PUBLIC)

    def test_snapshot_after_publication(self):
        originals = evidence()
        originals["candidates"]["timestamp"] = "2026-10-24T07:00:00Z"
        with self.assertRaisesRegex(ValueError, "not earlier"):
            verify_commit_chronology(originals, PUBLIC)

    def test_same_second_is_not_proof(self):
        with self.assertRaisesRegex(ValueError, "not earlier"):
            verify_commit_chronology(evidence("2026-10-24T06:00:00Z"), PUBLIC)

    def test_invalid_commit_sha(self):
        originals = evidence()
        originals["profile"]["sha"] = "fake"
        with self.assertRaisesRegex(ValueError, "Invalid private commit"):
            verify_commit_chronology(originals, PUBLIC)

    def test_naive_datetime_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            verify_commit_chronology(evidence("2026-10-24T05:00:00"), PUBLIC)


if __name__ == "__main__":
    unittest.main()
