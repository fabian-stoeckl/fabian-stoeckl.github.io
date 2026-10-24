import unittest
from scripts.morgenzeitung_source_evidence import validate_source_url, audit_sources
from tests.test_morgenzeitung_prepublication_gate import Repo
from scripts.morgenzeitung_prepublication_gate import verify_edition


class SourceEvidenceTests(unittest.TestCase):
    def test_publisher_url(self):
        self.assertEqual(validate_source_url("https://www.faz.net/aktuell/wirtschaft/artikel.html"),
                         "https://www.faz.net/aktuell/wirtschaft/artikel.html")

    def test_unsafe_and_nonpublisher_urls(self):
        for url in ("http://www.faz.net/story", "https://localhost/story",
                    "https://127.0.0.1/story", "https://user:password@faz.net/story",
                    "https://faz.net:444/story", "https://faz.net/story#fragment"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_source_url(url)

    def test_missing_urls_reported_without_false_verification(self):
        result = audit_sources([{"id": "a"}, {"id": "b", "source_url": "http://example.com"}])
        self.assertFalse(result["source_url_structure_verified"])
        self.assertEqual(result["missing_original_url_ids"], ["a"])
        self.assertEqual(result["invalid_original_url_ids"], ["b"])

    def test_conflicting_source_alias_rejected(self):
        result = audit_sources([{"id": "a", "source_url": "https://faz.net/a",
                                 "original_url": "https://faz.net/b"}])
        self.assertFalse(result["source_url_structure_verified"])

    def test_positive_offline_replay_verifies_url_structure(self):
        result = verify_edition(Repo(), "2026-10-25", {
            "date": "2026-10-25", "articles": [{"id": "a"}, {"id": "b"}]})
        self.assertTrue(result["prepublication_gate_verified"])
        self.assertTrue(result["source_evidence"]["source_url_structure_verified"])


if __name__ == "__main__":
    unittest.main()
