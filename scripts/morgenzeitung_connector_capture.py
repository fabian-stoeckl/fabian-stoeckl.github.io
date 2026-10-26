"""Prepare and verify private capture using the authenticated GitHub connector.

No credential export. Preparation is NOT persistence. The caller must commit the
four exact files atomically through the connector and export a pinned readback.
The existing GitHub Actions gate independently reads those files before merge.
"""
import hashlib
import json
import re
from scripts.morgenzeitung_capture_preselection import capture, verify_existing, snapshot_paths

REPOSITORY = 'fabian-stoeckl/morgenzeitung-feedback'


def blob_sha(content):
    raw = content.encode('utf-8')
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def require_sha(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{40}', value):
        raise ValueError('Missing or invalid GitHub SHA')


def validate_envelope(envelope):
    if envelope.get('repository') != REPOSITORY:
        raise ValueError('Wrong private repository')
    require_sha(envelope.get('commit_sha'))


class PreparedRepo:
    def __init__(self, export):
        validate_envelope(export)
        profile = export['profile']
        if blob_sha(profile['content']) != profile['blob_sha']:
            raise ValueError('Profile blob SHA mismatch')
        # A short first page alone must never masquerade as a complete export.
        if export.get('issues_pagination_complete') is not True:
            raise ValueError('Complete issue pagination required')
        issues = export['issues']
        if not isinstance(issues, list) or any(not isinstance(i, dict) for i in issues):
            raise ValueError('Invalid issue export')
        versions = [i.get('number') for i in issues]
        if any(type(n) is not int for n in versions) or len(set(versions)) != len(versions):
            raise ValueError('Invalid or duplicate issue numbers')
        for issue in issues:
            if not isinstance(issue.get('updated_at'), str) or not issue['updated_at']:
                raise ValueError('Missing issue version')
        self.issues = issues
        self.files = {'profile.json': (profile['content'].encode(), profile['blob_sha'])}
        self.prepared = {}

    def read(self, path):
        return self.files.get(path)

    def api(self, path, method='GET', payload=None):
        match = re.fullmatch(r'/issues\?state=all&per_page=100&page=(\d+)', path)
        if method != 'GET' or not match:
            raise ValueError('Unsupported preparation request')
        page = int(match[1])
        return self.issues[(page-1)*100:page*100]

    def put_immutable(self, path, data):
        if path in self.files and self.files[path][0] != data:
            raise ValueError('Conflicting prepared file')
        content = data.decode('utf-8')
        sha = blob_sha(content)
        self.files[path] = (data, sha)
        self.prepared[path] = {'content': content, 'blob_sha': sha}


def prepare(export, date, candidates, *, limit=10, max_per_source=4, version=None):
    repo = PreparedRepo(export)
    capture_result = capture(repo, date, candidates, limit=limit, max_per_source=max_per_source, version=version)
    verify_existing(repo, date, version=version)
    return {'repository': REPOSITORY, 'date': date, 'snapshot_version': version,
            'base_commit_sha': export['commit_sha'],
            'profile_blob_sha': export['profile']['blob_sha'],
            'files': repo.prepared, 'capture': capture_result,
            'private_persistence_verified': False,
            'note': 'Prepare only. Commit exact files via connector with expected-head lease; pinned remote readback required before selection.'}


class ReadbackRepo:
    def __init__(self, files):
        self.files = files

    def read(self, path):
        item = self.files.get(path)
        return (item['content'].encode(), item['blob_sha']) if item else None


def verify_readback(manifest, readback, date, version=None):
    validate_envelope(readback)
    if manifest.get('repository') != REPOSITORY or manifest.get('date') != date:
        raise ValueError('Manifest date or repository mismatch')
    if manifest.get('snapshot_version') != version:
        raise ValueError('Snapshot version mismatch')
    require_sha(manifest.get('base_commit_sha'))
    require_sha(manifest.get('profile_blob_sha'))
    names = snapshot_paths(date, version)
    expected_paths = set(names.values())
    if set(manifest.get('files', {})) != expected_paths or set(readback.get('files', {})) != expected_paths:
        raise ValueError('Exactly four original private files required')
    for path in expected_paths:
        item = readback['files'][path]
        if item != manifest['files'][path] or blob_sha(item['content']) != item['blob_sha']:
            raise ValueError('Remote readback differs from prepared original: '+path)
    if readback['files'][names['profile']]['blob_sha'] != manifest['profile_blob_sha']:
        raise ValueError('Profile provenance mismatch')
    result = verify_existing(ReadbackRepo(readback['files']), date, version=version)
    result.update(repository=REPOSITORY, snapshot_commit_sha=readback['commit_sha'],
                  profile_blob_sha=manifest['profile_blob_sha'],
                  connector_readback_matches=True,
                  note='Connector-exported pinned readback matches exact prepared bytes. Independent remote prepublication gate remains mandatory; this is not publication or learning PASS.')
    return result
