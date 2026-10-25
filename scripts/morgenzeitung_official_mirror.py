"""Strict cross-domain verification for a Reuters Breakingviews article on its own official site.

The primary Reuters.com permalink can return HTTP 401 to GitHub Actions.
That is not positive article evidence. Only when the edition explicitly links to
the corresponding Breakingviews ORIGINAL and the original fetch is access-blocked,
verify the alternate publisher page's title, publication date and HTTPS origin.
Never use a search result, archive proxy or unrelated publisher as a substitute.
"""
import datetime as dt
from html.parser import HTMLParser
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from scripts.morgenzeitung_live_source_check import NoRedirect
from scripts.morgenzeitung_source_evidence import validate_source_url

MAX_HTML_BYTES = 2097152


class ArticleIdentity(HTMLParser):
    def __init__(self):
        super().__init__()
        self.titles = []
        self.dates = []
        self._collect = None
        self._chunks = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('title', 'h1'):
            self._collect = tag
            self._chunks = []
        if tag == 'meta':
            key = (a.get('property') or a.get('name') or '').lower()
            if key in ('og:title', 'twitter:title') and a.get('content'):
                self.titles.append(a['content'])
            if key in ('article:published_time', 'datepublished') and a.get('content'):
                self.dates.append(a['content'])
        if tag == 'time' and a.get('datetime'):
            self.dates.append(a['datetime'])

    def handle_data(self, data):
        if self._collect:
            self._chunks.append(data)

    def handle_endtag(self, tag):
        if tag == self._collect:
            value = ' '.join(self._chunks).strip()
            if value:
                self.titles.append(value)
            self._collect = None
            self._chunks = []


def _normalized_title(value):
    return ''.join(c for c in value.casefold() if c.isalnum())


def verify_official_mirror(candidate, mirror_url, *, opener=None):
    """Fail closed unless a real HTTPS Breakingviews page matches the Reuters article."""
    original = validate_source_url(candidate['source_url'])
    mirror_url = validate_source_url(mirror_url)
    src, alt = urlsplit(original), urlsplit(mirror_url)
    if (src.hostname not in ('www.reuters.com', 'reuters.com')
            or not src.path.startswith('/commentary/breakingviews/')
            or alt.hostname not in ('www.breakingviews.com', 'breakingviews.com')
            or not re.fullmatch(
                r'/(?:[0-9a-f]{12}/)?columns/[a-z0-9-]+/[a-z0-9-]+-\d{4}-\d{2}-\d{2}/',
                alt.path)
            or src.query or alt.query
            or candidate.get('source') != 'Reuters Breakingviews'):
        raise ValueError('Not an approved Reuters Breakingviews official mirror')
    stamp = dt.datetime.fromisoformat(candidate['published_at'].replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Official mirror needs timezone-aware publication date')
    published = stamp.astimezone(dt.timezone.utc)
    date_slug = published.date().isoformat()
    if not alt.path.endswith('-' + date_slug + '/'):
        raise ValueError('Official mirror publication date contradicts archived source')

    opener = opener or urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(mirror_url, method='GET',
                                 headers={'Accept': 'text/html', 'User-Agent': 'MorgenzeitungSourceCheck/1.0'})
    try:
        with opener.open(req, timeout=10) as response:
            if response.status != 200:
                raise ValueError('Official mirror did not return HTTP 200')
            if 'text/html' not in response.headers.get('Content-Type', '').lower():
                raise ValueError('Official mirror did not return HTML')
            data = response.read(MAX_HTML_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise ValueError('Official mirror was not independently reachable') from exc
    if len(data) > MAX_HTML_BYTES:
        raise ValueError('Official mirror response exceeded HTML inspection limit')
    body = data.decode('utf-8', errors='replace')
    parser = ArticleIdentity()
    parser.feed(body)
    expected = _normalized_title(candidate.get('title', ''))
    if not expected or not any(expected in _normalized_title(t) for t in parser.titles):
        raise ValueError('Official mirror title differs from archived candidate')
    # Read the actual publisher metadata when present. A date-only check is a
    # fallback only for publisher HTML with a visible date+time and a dated URL.
    from scripts.morgenzeitung_publisher_date_evidence import compare_publisher_timestamp
    timestamp = compare_publisher_timestamp(body, candidate['published_at'])
    if timestamp['status'] in ('mismatch', 'conflict'):
        raise ValueError('Official mirror timestamp contradicts archived publication time')
    if timestamp['status'] == 'inconclusive':
        month = published.strftime('%B')
        visible_date = f'{month} {published.day}, {published.year}'
        ampm = published.strftime('%I:%M %p').lstrip('0')
        flattened = re.sub(r'<[^>]*>', ' ', body)
        flattened = re.sub(r'\s+', ' ', flattened)
        if visible_date not in flattened or ampm not in flattened:
            raise ValueError('Official mirror has no independently visible date and time')
    return {'official_mirror_verified': True, 'original_url': original,
            'mirror_url': mirror_url, 'title_matched': True,
            'publication_time_evidence': timestamp['status'],
            'original_blocked': True}


def verify_standard_alias(candidate, alias_url, *, opener=None):
    """Verify a Der Standard .de/.at alias by identical story path AND live publisher HTML.

    An alias is never trusted merely because its URL looks plausible. A real
    response must match the archived article title and its publication time.
    """
    original = validate_source_url(candidate['source_url'])
    alias_url = validate_source_url(alias_url)
    src, alt = urlsplit(original), urlsplit(alias_url)
    hosts = {'derstandard.at', 'www.derstandard.at',
             'derstandard.de', 'www.derstandard.de'}
    if (src.hostname not in hosts or alt.hostname not in hosts
            or src.hostname == alt.hostname or src.path != alt.path
            or not src.path.startswith('/story/')
            or src.query or alt.query
            or candidate.get('source') != 'Der Standard'):
        raise ValueError('Not an identical Der Standard publisher alias')
    stamp = dt.datetime.fromisoformat(candidate['published_at'].replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Publisher alias needs timezone-aware publication date')
    opener = opener or urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(alias_url, method='GET',
                                 headers={'Accept': 'text/html',
                                          'User-Agent': 'MorgenzeitungSourceCheck/1.0'})
    try:
        with opener.open(req, timeout=10) as response:
            if response.status != 200:
                raise ValueError('Publisher alias did not return HTTP 200')
            if 'text/html' not in response.headers.get('Content-Type', '').lower():
                raise ValueError('Publisher alias did not return HTML')
            data = response.read(MAX_HTML_BYTES + 1)
    except (urllib.error.HTTPError, urllib.error.URLError,
            TimeoutError, ConnectionError) as exc:
        raise ValueError('Publisher alias was not independently reachable') from exc
    if len(data) > MAX_HTML_BYTES:
        raise ValueError('Publisher alias response exceeded HTML inspection limit')
    body = data.decode('utf-8', errors='replace')
    parser = ArticleIdentity()
    parser.feed(body)
    expected = _normalized_title(candidate.get('title', ''))
    if not expected or not any(expected in _normalized_title(title)
                               for title in parser.titles):
        raise ValueError('Publisher alias title differs from archived candidate')
    from scripts.morgenzeitung_publisher_date_evidence import compare_publisher_timestamp
    timestamp = compare_publisher_timestamp(body, candidate['published_at'])
    if timestamp['status'] in ('mismatch', 'conflict'):
        raise ValueError('Publisher alias timestamp contradicts archived candidate')
    if timestamp['status'] == 'inconclusive':
        from html import unescape
        months = ('', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
                  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember')
        visible = f'{stamp.day}. {months[stamp.month]} {stamp.year}, {stamp:%H:%M}'
        flattened = unescape(re.sub(r'<[^>]*>', ' ', body))
        flattened = re.sub(r'\\s+', ' ', flattened)
        if visible not in flattened:
            raise ValueError('Publisher alias has no matching visible date and time')
    return {'official_mirror_verified': True, 'original_url': original,
            'mirror_url': alias_url, 'title_matched': True,
            'publication_time_evidence': timestamp['status'],
            'same_publisher_story_path': True}
