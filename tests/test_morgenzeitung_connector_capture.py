import copy
import json
import unittest
from scripts.morgenzeitung_connector_capture import prepare, verify_readback, blob_sha, REPOSITORY


class ConnectorCaptureTests(unittest.TestCase):
    def setUp(self):
        content = '{"computed_learning_signals": []}\n'
        self.export = {'repository': REPOSITORY, 'commit_sha': 'a'*40,
                       'profile': {'content': content, 'blob_sha': blob_sha(content)},
                       'issues_pagination_complete': True,
                       'issues': [{'number': 1, 'updated_at': '2026-10-23T00:00:00Z'},
                                  {'number': 3, 'updated_at': '2026-10-24T00:00:00Z'}]}
        self.pool = json.dumps([{'id':'one','topic':'Industrie','source':'Example',
                                'source_url':'https://example.org/article',
                                'published_at':'2026-10-24T12:00:00Z','verified':True}]).encode()
        self.date = '2026-10-25'
        self.manifest = prepare(self.export, self.date, self.pool, limit=12, max_per_source=12)
        self.readback = {'repository': REPOSITORY, 'commit_sha': 'b'*40,
                         'files': copy.deepcopy(self.manifest['files'])}

    def test_prepare_is_not_persistence_and_preserves_input(self):
        self.assertFalse(self.manifest['private_persistence_verified'])
        self.assertEqual(len(self.manifest['files']), 4)
        self.assertEqual(self.manifest['files']['candidates/'+self.date+'.json']['content'].encode(), self.pool)
        self.assertEqual(self.manifest['capture']['issue_count'], 1)

    def test_readback_preserves_parameters_and_profile(self):
        result = verify_readback(self.manifest, self.readback, self.date)
        self.assertEqual(result['parameters'], {'limit':12,'max_per_source':12})
        self.assertTrue(result['connector_readback_matches'])
        self.assertEqual(result['profile_blob_sha'], self.export['profile']['blob_sha'])

    def test_missing_changed_and_bad_hash_fail(self):
        for mode in ['missing','changed','hash']:
            readback = copy.deepcopy(self.readback)
            path = next(iter(readback['files']))
            if mode == 'missing': del readback['files'][path]
            elif mode == 'changed': readback['files'][path]['content'] += ' '
            else: readback['files'][path]['blob_sha'] = 'c'*40
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                verify_readback(self.manifest, readback, self.date)

    def test_wrong_repository_date_commit_rejected(self):
        for key,value in [('repository','public/repo'),('commit_sha','')]:
            bad = copy.deepcopy(self.readback); bad[key] = value
            with self.assertRaises(ValueError): verify_readback(self.manifest,bad,self.date)
        with self.assertRaises(ValueError): verify_readback(self.manifest,self.readback,'2026-10-26')

    def test_incomplete_issues_and_bad_profile_rejected(self):
        bad = copy.deepcopy(self.export); bad['issues_pagination_complete'] = False
        with self.assertRaises(ValueError): prepare(bad,self.date,self.pool)
        bad = copy.deepcopy(self.export); bad['profile']['content'] += ' '
        with self.assertRaises(ValueError): prepare(bad,self.date,self.pool)

    def test_pagination_and_duplicates(self):
        export = copy.deepcopy(self.export)
        export['issues'] = [{'number': n, 'updated_at':'2026-10-24T00:00:00Z'} for n in range(3,205)]
        self.assertEqual(prepare(export,self.date,self.pool)['capture']['issue_count'],202)
        export['issues'].append(export['issues'][0])
        with self.assertRaises(ValueError): prepare(export,self.date,self.pool)

    def test_profile_provenance_tampering_fails(self):
        manifest = copy.deepcopy(self.manifest); manifest['profile_blob_sha'] = 'd'*40
        with self.assertRaises(ValueError): verify_readback(manifest,self.readback,self.date)
