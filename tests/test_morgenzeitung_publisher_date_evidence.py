import unittest
from scripts.morgenzeitung_publisher_date_evidence import compare_publisher_timestamp


class PublisherTimestampEvidenceTests(unittest.TestCase):
    def test_meta_match(self):
        html = '<meta property="article:published_time" content="2026-10-24T10:00:00+02:00">'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "match")

    def test_jsonld_match(self):
        html = '<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-10-24T08:00:00Z"}</script>'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "match")

    def test_actual_publisher_seconds_with_displayed_minute_precision(self):
        # Observed in genuine 23 Oct 2026 ORF/Presse JSON-LD: the site shows
        # HH:MM while the machine field retains second/millisecond precision.
        orf = '<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-10-23T12:28:01.469Z"}</script>'
        presse = '<meta property="article:published_time" content="2026-10-23T12:11:52Z">'
        self.assertEqual(compare_publisher_timestamp(orf, "2026-10-23T14:28:00+02:00")["status"], "match")
        evidence = compare_publisher_timestamp(presse, "2026-10-23T14:11:00+02:00")
        self.assertEqual(evidence["status"], "match")
        self.assertEqual(evidence["resolution"], "declared-minute")

    def test_minute_tolerance_does_not_hide_next_minute(self):
        meta = '<meta property="article:published_time" content="2026-10-23T12:12:01Z">'
        self.assertEqual(compare_publisher_timestamp(meta, "2026-10-23T14:11:00+02:00")["status"], "mismatch")

    def test_precise_declared_second_is_not_rounded(self):
        meta = '<meta property="article:published_time" content="2026-10-23T12:11:52Z">'
        self.assertEqual(compare_publisher_timestamp(meta, "2026-10-23T12:11:51Z")["status"], "mismatch")

    def test_mismatch(self):
        html = '<meta property="article:published_time" content="2026-10-23T08:00:00Z">'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "mismatch")

    def test_real_handelsblatt_jsonld_fractional_seconds_not_conflict(self):
        html = ('<script type="application/ld+json">'
                '{"@type":"NewsArticle","datePublished":"2026-10-23T16:09:01.912Z"}'
                '</script><meta property="article:published_time" content="2026-10-23T16:09:01Z">')
        result = compare_publisher_timestamp(html, "2026-10-23T18:09:00+02:00")
        self.assertEqual(result["status"], "match")

    def test_different_publisher_seconds_are_not_automatically_equivalent(self):
        html = ('<script type="application/ld+json">'
                '{"@type":"NewsArticle","datePublished":"2026-10-23T16:09:01Z"}'
                '</script><meta property="article:published_time" content="2026-10-23T16:09:03Z">')
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-23T18:09:00+02:00")["status"], "conflict")

    def test_conflicting_metadata(self):
        html = ('<meta property="article:published_time" content="2026-10-23T08:00:00Z">'
                '<meta name="datePublished" content="2026-10-24T08:00:00Z">')
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "conflict")

    def test_nested_recommended_article_does_not_create_conflict(self):
        html = ('<script type="application/ld+json">'
                '{"@type":"NewsArticle","datePublished":"2026-10-24T08:00:00Z",'
                '"relatedLink":{"@type":"NewsArticle","datePublished":"2026-10-21T08:00:00Z"}}'
                '</script>')
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "match")

    def test_ambiguous_modification_meta_is_not_publication_evidence(self):
        html = ('<meta name="dateCreated" content="2026-10-23T08:00:00Z">'
                '<meta property="article:published_time" content="2026-10-24T08:00:00Z">')
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "match")

    def test_untyped_jsonld_date_is_not_publication_evidence(self):
        html = '<script type="application/ld+json">{"@type":"WebPage","datePublished":"2026-10-21T08:00:00Z"}</script>'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "inconclusive")

    def test_actual_autumn_2026_handelsblatt_fold_is_ambiguous_not_verified(self):
        # 25 Oct 2026 Europe/Vienna falls back at 03:00 CEST to 02:00 CET.
        # The publisher supplies 02:11:16 CET but the stored display time
        # says 02:11 CEST. These are distinct instants but identical local
        # wall-clock minutes; do not claim a verified match.
        html = ('<meta property="article:published_time" '
                'content="2026-10-25T01:11:16.732Z">'
                '<script type="application/ld+json">'
                '{"@type":"NewsArticle","datePublished":"2026-10-25T01:11:16.732Z"}'
                '</script>')
        result = compare_publisher_timestamp(html, "2026-10-25T02:11:00+02:00")
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["resolution"], "dst-overlap-minute")
        self.assertEqual(result["publisher_published_at"], "2026-10-25T01:11:16.732000+00:00")

    def test_dst_overlap_does_not_whitelist_other_hour_or_date(self):
        html = '<meta property="article:published_time" content="2026-10-25T01:11:16Z">'
        for declared in ["2026-10-25T03:11:00+01:00",
                         "2026-10-24T02:11:00+02:00",
                         "2026-10-25T02:12:00+02:00",
                         "2026-10-25T02:11:17+02:00"]:
            with self.subTest(declared=declared):
                self.assertEqual(compare_publisher_timestamp(html, declared)["status"], "mismatch")

    def test_dst_overlap_does_not_mask_true_conflicting_meta(self):
        html = ('<meta property="article:published_time" content="2026-10-25T01:11:16Z">'
                '<meta name="datePublished" content="2026-10-25T00:11:16Z">')
        self.assertEqual(compare_publisher_timestamp(html,"2026-10-25T02:11:00+02:00")["status"],"conflict")

    def test_missing_metadata_inconclusive(self):
        self.assertEqual(compare_publisher_timestamp("<html></html>", "2026-10-24T08:00:00Z")["status"], "inconclusive")

    def test_naive_publisher_date_inconclusive(self):
        html = '<meta property="article:published_time" content="2026-10-24T08:00:00">'
        self.assertEqual(compare_publisher_timestamp(html, "2026-10-24T08:00:00Z")["status"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
