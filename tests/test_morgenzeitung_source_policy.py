import json
import unittest
from unittest.mock import patch

from scripts.morgenzeitung_source_policy import (
    classify_inconclusive, check_inconclusive_budget)
from scripts.morgenzeitung_prepublication_gate import verify_edition
from tests.test_morgenzeitung_prepublication_gate import Repo


ORIGINAL = ('https://www.derstandard.at/story/3000000345625/'
            'wie-gefaehrdet-sind-die-aktienmaerkte-ist-die-nervositaet-berechtigt')
GOOD = {'id':'a', 'title':'Wie gefährdet sind die Aktienmärkte?',
        'source':'Der Standard', 'source_url':ORIGINAL,
        'published_at':'2026-10-24T06:00:00+02:00', 'verified':True}


class SourcePolicyTests(unittest.TestCase):
    def test_expired_rss_is_explicit_inconclusive_not_source_pass(self):
        record = classify_inconclusive(
            GOOD, ValueError('Article identity not independently present in publisher RSS'))
        self.assertEqual(record['source_verification'], 'INCONCLUSIVE')
        self.assertFalse(record['original_article_http_verified'])
        self.assertFalse(record['publisher_feed_verified'])

    def test_access_barrier_is_not_fake_source_verification(self):
        r = classify_inconclusive(GOOD, ValueError('Publisher RSS independently unreachable'))
        self.assertEqual(r['source_verification'], 'INCONCLUSIVE')

    def test_hard_errors_and_wrong_sources_remain_fail_closed(self):
        for msg in (
            'Publisher publication metadata contradict archived date',
            'Source URL not confirmed reachable (HTTP 404)',
            'Publisher redirect changes host or article identity',
            'Publisher access restricted: article existence unverified (HTTP 401)',
        ):
            with self.subTest(message=msg):
                self.assertIsNone(classify_inconclusive(GOOD, ValueError(msg)))
        for candidate in [
            {**GOOD,'verified':False},
            {**GOOD,'source':'Random News'},
            {**GOOD,'source_url':'https://derstandard.at.evil.example/story/12345/x'},
            {**GOOD,'source_url':'https://www.derstandard.at/consent/tcf/story/1/x'},
            {**GOOD,'title':''},
        ]:
            with self.subTest(candidate=candidate), self.assertIsNone(
                classify_inconclusive(candidate, ValueError(
                    'Article identity not independently present in publisher RSS')))

    def test_inconclusive_budget(self):
        r={'source_verification':'INCONCLUSIVE'}
        self.assertEqual(len(check_inconclusive_budget([r, r])),2)
        with self.assertRaisesRegex(ValueError,'Too many independently unverified sources'):
            check_inconclusive_budget([r,r,r])

    def test_gate_expired_rss_allows_editorial_replay_with_partial_warning(self):
        repo=Repo()
        candidates=json.loads(repo.files['candidates/2026-10-25.json'])
        candidates[0]={**candidates[0], **GOOD}
        repo.files['candidates/2026-10-25.json']=json.dumps(candidates).encode()
        def fake_checked(items, date, publisher_dates):
            if items[0]['id']=='a':
                raise ValueError('Article identity not independently present in publisher RSS')
            return {'checked':[{'id':items[0]['id'], 'http_status':200,
                                 'original_article_http_verified':True}]}
        with patch('scripts.morgenzeitung_prepublication_gate.check_candidates',side_effect=fake_checked):
            x=verify_edition(repo,'2026-10-25',
                             {'date':'2026-10-25','articles':[{'id':'a'},{'id':'b'}]},
                             check_live=True)
        self.assertTrue(x['prepublication_gate_verified'])
        self.assertFalse(x['live_source_evidence']['live_source_checks_passed'])
        self.assertEqual(x['live_source_evidence']['source_verification_status'],'PARTIAL')
        self.assertEqual(len(x['live_source_evidence']['warnings']),1)
        self.assertEqual(x['live_source_evidence']['checked'][0]['source_verification'],'INCONCLUSIVE')

    def test_gate_does_not_downgrade_source_contradictions(self):
        repo=Repo()
        items=json.loads(repo.files['candidates/2026-10-25.json'])
        items[0]={**items[0], **GOOD}
        repo.files['candidates/2026-10-25.json']=json.dumps(items).encode()
        with patch('scripts.morgenzeitung_prepublication_gate.check_candidates',
                   side_effect=ValueError('Publisher publication metadata contradict archived date')):
            with self.assertRaisesRegex(ValueError,'contradict'):
                verify_edition(repo,'2026-10-25',{'date':'2026-10-25',
                               'articles':[{'id':'a'},{'id':'b'}]},check_live=True)

    def test_gate_rejects_more_than_two_uncertain_sources(self):
        repo=Repo()
        items=json.loads(repo.files['candidates/2026-10-25.json'])
        items[:]=[{**GOOD,'id':z} for z in ('a','b','c')]
        repo.files['candidates/2026-10-25.json']=json.dumps(items).encode()
        repo.files['snapshots/2026-10-25-selection-parameters.json']=b'{"limit":3,"max_per_source":4}'
        with patch('scripts.morgenzeitung_prepublication_gate.check_candidates',
                   side_effect=ValueError('Article identity not independently present in publisher RSS')):
            with self.assertRaisesRegex(ValueError,'Too many independently unverified'):
                verify_edition(repo,'2026-10-25',{'date':'2026-10-25',
                               'articles':[{'id':'a'},{'id':'b'},{'id':'c'}]},check_live=True)


if __name__=='__main__':
    unittest.main()
