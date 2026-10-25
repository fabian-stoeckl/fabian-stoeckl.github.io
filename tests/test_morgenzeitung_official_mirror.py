import copy
import unittest
import urllib.error
from unittest.mock import patch

from scripts.morgenzeitung_official_mirror import verify_official_mirror
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


if __name__ == '__main__':
    unittest.main()
