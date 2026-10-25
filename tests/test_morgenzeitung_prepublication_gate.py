import json
import unittest
from unittest.mock import patch
from scripts.morgenzeitung_prepublication_gate import verify_edition, validate_published_count, verify_index


class Repo:
    def __init__(self):
        day = "2026-10-25"
        self.files = {
            f"candidates/{day}.json": json.dumps([
                {"id": "a", "topic": "Industrie", "source": "FAZ", "source_url": "https://www.faz.net/aktuell/wirtschaft/a", "verified": True, "published_at": "2026-10-24T08:00:00Z"},
                {"id": "b", "topic": "Klima", "source": "ORF", "source_url": "https://orf.at/stories/b", "verified": True, "published_at": "2026-10-24T08:00:00Z"},
            ]).encode(),
            f"snapshots/{day}-profile.json": b'{"computed_learning_signals":[]}',
            f"snapshots/{day}-issues.json": b'[]',
            f"snapshots/{day}-selection-parameters.json": b'{"limit":2,"max_per_source":4}',
        }

    def read(self, path):
        return (self.files[path], "sha") if path in self.files else None


class GateTests(unittest.TestCase):
    def test_publication_count_boundary(self):
        for n in (0, 1, 9, 16):
            with self.subTest(n=n), self.assertRaisesRegex(ValueError, "10 to 15"):
                validate_published_count({"articles": [{}] * n})
        for n in (10, 15):
            self.assertTrue(validate_published_count({"articles": [{}] * n}))
        with self.assertRaises(ValueError):
            validate_published_count({"articles": None})

    def test_valid_index(self):
        self.assertTrue(verify_index({"dates": ["2026-10-25", "2026-10-24"]}, "2026-10-25"))

    def test_index_missing_edition(self):
        with self.assertRaisesRegex(ValueError, "Edition missing"):
            verify_index({"dates": ["2026-10-24"]}, "2026-10-25")

    def test_index_duplicates(self):
        with self.assertRaisesRegex(ValueError, "Edition missing"):
            verify_index({"dates": ["2026-10-25", "2026-10-25"]}, "2026-10-25")

    def test_index_wrong_order(self):
        with self.assertRaisesRegex(ValueError, "Edition missing"):
            verify_index({"dates": ["2026-10-24", "2026-10-25"]}, "2026-10-25")

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

    def test_live_check_runs_only_after_exact_replay(self):
        with patch("scripts.morgenzeitung_prepublication_gate.check_candidates") as check:
            verify_edition(Repo(), "2026-10-25", {
                "date": "2026-10-25", "articles": [{"id": "a"}, {"id": "b"}]},
                check_live=True)
            self.assertEqual(sum(len(call.args[0]) for call in check.call_args_list), 2)
        with patch("scripts.morgenzeitung_prepublication_gate.check_candidates") as check:
            with self.assertRaisesRegex(ValueError, "does not match"):
                verify_edition(Repo(), "2026-10-25", {
                    "date": "2026-10-25", "articles": [{"id": "b"}, {"id": "a"}]},
                    check_live=True)
            check.assert_not_called()

    def test_unselected_candidates_not_live_checked(self):
        repo = Repo()
        pool = json.loads(repo.files["candidates/2026-10-25.json"])
        pool.append({"id": "c", "topic": "Politik", "source": "SZ",
                     "source_url": "https://sz.de/article", "verified": True, "published_at": "2026-10-24T08:00:00Z"})
        repo.files["candidates/2026-10-25.json"] = json.dumps(pool).encode()
        with patch("scripts.morgenzeitung_prepublication_gate.check_candidates") as check:
            verify_edition(repo, "2026-10-25", {
                "date": "2026-10-25", "articles": [{"id": "a"}, {"id": "b"}]},
                check_live=True)
            self.assertEqual([x["id"] for x in check.call_args.args[0]], ["a", "b"])

    def test_live_source_checks_replay_and_archive(self):
        with patch("scripts.morgenzeitung_live_source_check.check_http") as http:
            with patch("scripts.morgenzeitung_publisher_date_evidence.fetch_publisher_metadata") as metadata:
                http.return_value = {"status": 200, "paywall_or_access_restricted": False}
                metadata.return_value = {"status": "match"}
                repo = Repo()
                pool = json.loads(repo.files["candidates/2026-10-25.json"])
                for item in pool:
                    item["published_at"] = "2026-10-24T08:00:00Z"
                repo.files["candidates/2026-10-25.json"] = json.dumps(pool).encode()
                result = verify_edition(repo, "2026-10-25", {
                    "date": "2026-10-25", "articles": [{"id": "a"}, {"id": "b"}]},
                    {"dates": ["2026-10-25", "2026-10-24"]}, check_live=True)
                self.assertEqual(result["selected_ids"], ["a", "b"])
                self.assertEqual(http.call_count, 2)
                self.assertEqual(metadata.call_count, 2)
                self.assertEqual(len(result["live_source_evidence"]["checked"]), 2)

    def test_live_source_metadata_contradiction_blocks(self):
        with patch("scripts.morgenzeitung_prepublication_gate.check_candidates",
                   side_effect=ValueError("Publisher publication metadata contradict archived date")):
            with self.assertRaisesRegex(ValueError, "contradict"):
                verify_edition(Repo(), "2026-10-25", {
                    "date": "2026-10-25", "articles": [{"id": "a"}, {"id": "b"}]},
                    check_live=True)

    def test_preview_rejected(self):
        with self.assertRaisesRegex(ValueError, "preview"):
            verify_edition(Repo(), "2026-10-25", {
                "date": "2026-10-25", "preview": True, "articles": [{"id": "a"}, {"id": "b"}]})


if __name__ == "__main__":
    unittest.main()
