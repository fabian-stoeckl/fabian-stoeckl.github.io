import unittest
from unittest.mock import patch

from scripts.morgenzeitung_publisher_feed import verify_standard_feed, FEED_URL
from scripts.morgenzeitung_live_source_check import check_candidates

SOURCE = ('https://www.derstandard.de/story/3000000345625/'
          'wie-gefaehrdet-sind-die-aktienmaerkte-ist-die-nervositaet-berechtigt')
TITLE = 'Wie gefährdet sind die Aktienmärkte? Ist die Nervosität berechtigt?'
CANDIDATE = {'id': 'standard', 'source': 'Der Standard', 'title': TITLE,
             'source_url': SOURCE, 'published_at': '2026-10-24T06:00:00+02:00'}
RSS = ('<?xml version="1.0"?><rss><channel><item><title>' + TITLE +
       '</title><link>' + SOURCE.replace('.de/', '.at/') +
       '</link><pubDate>Sat, 24 Oct 2026 04:00:00 GMT</pubDate>'
       '</item></channel></rss>')


class Response:
    status = 200
    headers = {'Content-Type': 'application/rss+xml; charset=utf-8'}
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, limit): return self.data.encode()[:limit]


class FeedOpener:
    def __init__(self, data): self.data = data
    def open(self, request, timeout):
        if request.full_url != FEED_URL or request.get_method() != 'GET':
            raise AssertionError('Only the official publisher RSS GET is permitted')
        return Response(self.data)


class PublisherFeedTests(unittest.TestCase):
    def test_matching_official_publisher_feed_proves_listing_and_minute(self):
        result = verify_standard_feed(CANDIDATE, opener=FeedOpener(RSS))
        self.assertTrue(result['publisher_feed_verified'])
        self.assertTrue(result['title_matched'])
        self.assertIn('not article body', result['limitation'])

    def test_wrong_article_title_time_host_and_missing_item_fail(self):
        bad = [
            RSS.replace(TITLE, 'A different article'),
            RSS.replace('04:00:00', '05:00:00'),
            RSS.replace('derstandard.at', 'derstandard.at.evil.example'),
            RSS.replace('3000000345625', '3000000345626'),
            '<?xml version="1.0"?><rss><channel></channel></rss>',
        ]
        for data in bad:
            with self.subTest(data=data[:110]), self.assertRaises(ValueError):
                verify_standard_feed(CANDIDATE, opener=FeedOpener(data))

    def test_no_unrelated_source_or_html_or_doctype(self):
        with self.assertRaises(ValueError):
            verify_standard_feed({**CANDIDATE, 'source': 'Other'}, opener=FeedOpener(RSS))
        with self.assertRaises(ValueError):
            verify_standard_feed(CANDIDATE, opener=FeedOpener('<html>not rss</html>'))
        with self.assertRaises(ValueError):
            verify_standard_feed(CANDIDATE, opener=FeedOpener('<!DOCTYPE rss>' + RSS))

    def test_consent_redirect_requires_verified_feed(self):
        consent = ('Publisher redirect changes host or article identity: '
                   'www.derstandard.de/story/3000000345625/foo -> '
                   'www.derstandard.de/consent/tcf/story/3000000345625/foo')
        with patch('scripts.morgenzeitung_live_source_check.check_http',
                   return_value={'status': 302, 'publisher_consent_wall': True,
                                 'paywall_or_access_restricted': True,
                                 'original_article_http_verified': False}):
            with patch('scripts.morgenzeitung_publisher_feed.verify_standard_feed',
                       return_value={'publisher_feed_verified': True,
                                     'publication_time': '2026-10-24T04:00:00+00:00'}) as verify:
                result = check_candidates([CANDIDATE], '2026-10-25',
                                          publisher_dates=True)
            self.assertEqual(result['checked'][0]['publisher_date_evidence']['status'], 'match')
            self.assertTrue(result['checked'][0]['paywall_or_access_restricted'])
            self.assertTrue(result['live_source_checks_passed'])
            self.assertFalse(result['checked'][0]['original_article_http_verified'])
            verify.assert_called_once()

    def test_consent_redirect_without_feed_is_hard_failure(self):
        consent = ('Publisher redirect changes host or article identity: '
                   'www.derstandard.de/story/3000000345625/foo -> '
                   'www.derstandard.de/consent/tcf/story/3000000345625/foo')
        with patch('scripts.morgenzeitung_live_source_check.check_http',
                   return_value={'status': 302, 'publisher_consent_wall': True,
                                 'paywall_or_access_restricted': True,
                                 'original_article_http_verified': False}):
            with patch('scripts.morgenzeitung_publisher_feed.verify_standard_feed',
                       side_effect=ValueError('Not in publisher RSS')):
                with self.assertRaisesRegex(ValueError, 'Not in publisher RSS'):
                    check_candidates([CANDIDATE], '2026-10-25', publisher_dates=True)

    def test_other_redirect_never_triggers_rss_fallback(self):
        with patch('scripts.morgenzeitung_live_source_check.check_http',
                   side_effect=ValueError('Publisher redirect changes host or article identity')):
            with patch('scripts.morgenzeitung_publisher_feed.verify_standard_feed') as verify:
                with self.assertRaises(ValueError):
                    check_candidates([CANDIDATE], '2026-10-25')
                verify.assert_not_called()


if __name__ == '__main__':
    unittest.main()
