import unittest
from scripts.morgenzeitung_publisher_date_evidence import compare_publisher_timestamp


class PublisherTimestampEvidenceTests(unittest.TestCase):
    def test_meta_match(self):
        html = '<meta property="article:published_time" content="2026-10-24T10:00:00+02:00">'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "match")

    def test_jsonld_match(self):
        html = '<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-10-24T08:00:00Z"}</script>'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "match")

    def test_mismatch(self):
        html = '<meta property="article:published_time" content="2026-10-23T08:00:00Z">'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "mismatch")

    def test_conflicting_metadata(self):
        html = ('<meta property="article:published_time" content="2026-10-23T08:00:00Z">'
                '<meta name="datePublished" content="2026-10-24T08:00:00Z">')
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "conflict")

    def test_missing_metadata_inconclusive(self):
        self.assertEqual(compare_publisher_timestamp("<html></html>", "2026-10-24T08:00:00Z")["status"], "inconclusive")

    def test_naive_publisher_date_inconclusive(self):
        html = '<meta property="article:published_time" content="2026-10-24T08:00:00">'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
