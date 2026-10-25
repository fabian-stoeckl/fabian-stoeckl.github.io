import copy
import unittest
import urllib.error
from unittest.mock import patch

from scripts.morgenzeitung_official_mirror import verify_official_mirror, verify_standard_alias
from scripts.morgenzeitung_prepublication_gate import verify_edition
from tests.test_morgenzeitung_prepublication_gate import Repo


URL = 'https://www.reuters.com/commentary/breakingviews/global-markets-breakingviews-2026-10-24/'
OFFICIAL = ('https://www.breakingviews.com/40925ca4af2b/columns/considered-view/'
            'week-breakingviews-data-dreams-delayed-2026-10-24/')
TITLE = 'The Week in Breakingviews: Data dreams delayed'
CANDIDATE = {'id': 'a', 'source': 'Reuters Breakingviews', 'title': TITLE,
             'source_url': URL, 'published_at': '2026-10-24T10:00:00Z'}


class Response:
    status = 200
    headers = {'Content-Type': 'text/html; charset=utf-8'}
    def __init__(self, html): self.html = html
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, n): return self.html.encode('utf-8')[:n]


class Opener:
    def __init__(self, html): self.html = html
    def open(self, request, timeout):
        if request.get_method() != 'GET':
            raise AssertionError('A live publisher HTML GET is required')
        if request.full_url != OFFICIAL:
            raise AssertionError('Wrong page')
        return Response(self.html)


GOOD = ('<html><head><title>' + TITLE + ' | Reuters Breakingviews</title>'
        '<meta property="article:published_time" content="2026-10-24T10:00:00Z">'
        '</head><body><h1>' + TITLE + '</h1>'
        '<time datetime="2026-10-24T10:00:00Z">October 24, 2026 10:00 AM UTC</time>'
        '</body></html>')


class PublisherMirrorTests(unittest.TestCase):
    def test_official_publisher_original_succeeds(self):
        result = verify_official_mirror(CANDIDATE, OFFICIAL, opener=Opener(GOOD))
        self.assertTrue(result['official_mirror_verified'])
        self.assertEqual(result['publication_time_evidence'], 'match')
        self.assertEqual(result['original_url'], URL)

    def test_rejects_unrelated_source_and_domains(self):
        for changed in [
            ('url', 'https://archive.org/columns/considered-view/week-breakingviews-data-dreams-delayed-2026-10-24/'),
            ('url', 'https://breakingviews.com.evil.example/columns/considered-view/week-breakingviews-data-dreams-delayed-2026-10-24/'),
            ('url', 'http://www.breakingviews.com/columns/considered-view/week-breakingviews-data-dreams-delayed-2026-10-24/'),
            ('source', 'Other Newsroom'),
        ]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                if changed[0] == 'url':
                    verify_official_mirror(CANDIDATE, changed[1], opener=Opener(GOOD))
                else:
                    verify_official_mirror({**CANDIDATE, 'source': changed[1]}, OFFICIAL, opener=Opener(GOOD))

    def test_wrong_title_and_date_fail(self):
        for html in [
            GOOD.replace(TITLE, 'Unrelated news'),
            GOOD.replace('2026-10-24T10:00:00Z', '2026-10-23T10:00:00Z'),
        ]:
            with self.subTest(html=html[:100]), self.assertRaises(ValueError):
                verify_official_mirror(CANDIDATE, OFFICIAL, opener=Opener(html))
        with self.assertRaises(ValueError):
            verify_official_mirror(CANDIDATE, OFFICIAL.replace('2026-10-24', '2026-10-23'), opener=Opener(GOOD))

    def test_date_only_page_requires_visible_publisher_clock(self):
        bare = GOOD.replace('<meta property="article:published_time" content="2026-10-24T10:00:00Z">', '')
        bare = bare.replace('datetime="2026-10-24T10:00:00Z"', '')
        result = verify_official_mirror(CANDIDATE, OFFICIAL, opener=Opener(bare))
        self.assertEqual(result['publication_time_evidence'], 'inconclusive')
        with self.assertRaises(ValueError):
            verify_official_mirror(CANDIDATE, OFFICIAL, opener=Opener(bare.replace('10:00 AM', '11:00 AM')))

    def test_gate_requires_every_original_or_verified_equivalent(self):
        with patch('scripts.morgenzeitung_prepublication_gate.verify_official_mirror',
                   return_value={'official_mirror_verified': True}) as mirror:
            def controlled_checks(candidates, day, publisher_dates):
                if candidates[0]['id'] == 'a':
                    raise ValueError('Publisher access restricted: HTTP 401')
                return {'checked':[{'id':candidates[0]['id'], 'http_status':200}]}
            with patch('scripts.morgenzeitung_prepublication_gate.check_candidates',
                       side_effect=controlled_checks):
                result = verify_edition(Repo(), '2026-10-25',
                                        {'date': '2026-10-25',
                                         'articles': [{'id':'a', 'url':OFFICIAL},
                                                      {'id':'b','url':'https://orf.at/stories/b'}]},
                                        check_live=True)
            self.assertEqual(len(result['live_source_evidence']['checked']), 2)
            self.assertTrue(result['live_source_evidence']['checked'][0]['official_publisher_mirror']['official_mirror_verified'])
            mirror.assert_called_once()

    def test_gate_rejects_unverified_equivalent(self):
        with patch('scripts.morgenzeitung_prepublication_gate.verify_official_mirror',
                   side_effect=ValueError('Wrong title')):
            with self.assertRaisesRegex(ValueError,'Wrong title'):
                verify_edition(Repo(), '2026-10-25',
                               {'date':'2026-10-25',
                                'articles':[{'id':'a','url':OFFICIAL},
                                            {'id':'b','url':'https://orf.at/stories/b'}]},check_live=True)


class StandardAliasTests(unittest.TestCase):
    ORIGINAL = ('https://www.derstandard.de/story/3000000345625/'
                'wie-gefaehrdet-sind-die-aktienmaerkte-ist-die-nervositaet-berechtigt')
    ALIAS = ORIGINAL.replace('derstandard.de', 'derstandard.at')
    TITLE = 'Wie gefährdet sind die Aktienmärkte? Ist die Nervosität berechtigt?'
    CANDIDATE = {'id': 'standard', 'source': 'Der Standard', 'title': TITLE,
                 'source_url': ORIGINAL, 'published_at': '2026-10-24T06:00:00+02:00'}
    GOOD = ('<html><head><title>' + TITLE + ' - derStandard.at</title>'
            '<meta property="article:published_time" content="2026-10-24T04:00:00Z">'
            '</head><body><h1>' + TITLE + '</h1>'
            '24. Oktober 2026, 06:00</body></html>')

    class StandardOpener:
        def __init__(self, html, url):
            self.html, self.url = html, url
        def open(self, request, timeout):
            if request.full_url != self.url or request.get_method() != 'GET':
                raise AssertionError('Only a live GET of the exact alias is allowed')
            return Response(self.html)

    def test_identical_publisher_story_with_matching_live_metadata(self):
        result = verify_standard_alias(
            self.CANDIDATE, self.ALIAS,
            opener=self.StandardOpener(self.GOOD, self.ALIAS))
        self.assertTrue(result['official_mirror_verified'])
        self.assertTrue(result['same_publisher_story_path'])
        self.assertEqual(result['publication_time_evidence'], 'match')

    def test_visible_date_fallback_requires_matching_clock(self):
        html = self.GOOD.replace(
            '<meta property="article:published_time" content="2026-10-24T04:00:00Z">', '')
        result = verify_standard_alias(
            self.CANDIDATE, self.ALIAS,
            opener=self.StandardOpener(html, self.ALIAS))
        self.assertEqual(result['publication_time_evidence'], 'inconclusive')
        with self.assertRaisesRegex(ValueError, 'date and time'):
            verify_standard_alias(
                self.CANDIDATE, self.ALIAS,
                opener=self.StandardOpener(html.replace('06:00', '07:00'), self.ALIAS))

    def test_rejects_wrong_article_host_title_and_time(self):
        for alias in [
            self.ALIAS.replace('derstandard.at', 'derstandard.at.evil.example'),
            self.ALIAS.replace('3000000345625', '3000000345626'),
            self.ALIAS.replace('derstandard.at', 'othernews.at'),
        ]:
            with self.subTest(alias=alias), self.assertRaises(ValueError):
                verify_standard_alias(
                    self.CANDIDATE, alias,
                    opener=self.StandardOpener(self.GOOD, alias))
        for html in [
            self.GOOD.replace(self.TITLE, 'A different article'),
            self.GOOD.replace('2026-10-24T04:00:00Z', '2026-10-23T04:00:00Z'),
        ]:
            with self.subTest(html=html[:70]), self.assertRaises(ValueError):
                verify_standard_alias(
                    self.CANDIDATE, self.ALIAS,
                    opener=self.StandardOpener(html, self.ALIAS))


if __name__ == '__main__':
    unittest.main()
