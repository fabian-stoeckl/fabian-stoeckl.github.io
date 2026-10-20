"""Private single-reader storage and deterministic publication guards (stdlib only)."""
import copy
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from zoneinfo import ZoneInfo

VIENNA = ZoneInfo('Europe/Vienna')
TOPICS = {'Wirtschaft & Budget': 5, 'Produktivität & Industrie': 5, 'KI & Arbeit': 5,
          'Klima & Energie': 5, 'Migration & Sozialstaat': 4, 'Bildung & Forschung': 4,
          'Welthandel': 4, 'Gesundheitssystem': 4, 'Kapitalmärkte': 2, 'Gesundheit & Training': 2, 'Zuckerl': 2}
REASONS = ['', 'Mehr davon', 'Schon bekannt', 'Zu oberflächlich', 'Thema interessiert mich nicht']

def now():
    return datetime.now(timezone.utc).isoformat()

def instant(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('Zeit ohne Zeitzone')
    return d.astimezone(timezone.utc)

def canonical(url):
    p = urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password:
        raise ValueError('Nur öffentliche HTTPS-Artikellinks')
    return urlunsplit(('https', p.netloc.lower(), p.path.rstrip('/'), urlencode(sorted(
        (k, v) for k, v in parse_qsl(p.query) if not k.startswith('utm_') and k not in ('fbclid', 'gclid'))), ''))

def article_id(url):
    return hashlib.sha256(canonical(url).encode()).hexdigest()[:24]

def tokens(text):
    return set(re.findall(r'[\wäöüß]{4,}', text.lower())) - {'eine','einen','einer','einem','über','dies','sich','auch','werden','wurde','sind','wird','dass','nicht','nach','mehr'}

def similar(a, b):
    x, y = tokens(a), tokens(b)
    return len(x & y) / max(1, len(x | y)) >= .65

def schedule(day):
    """Research cutoff 07:15 local; public availability 07:45 local, DST aware."""
    d = datetime.fromisoformat(str(day))
    return (d.replace(hour=7, minute=15, tzinfo=VIENNA).astimezone(timezone.utc),
            d.replace(hour=7, minute=45, tzinfo=VIENNA).astimezone(timezone.utc))

class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT, reason TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS editions(day TEXT PRIMARY KEY, available TEXT NOT NULL, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS articles(id TEXT PRIMARY KEY, url TEXT UNIQUE, topic TEXT, event TEXT, facts TEXT, title TEXT, day TEXT, read_at TEXT);
            CREATE TABLE IF NOT EXISTS ratings(article TEXT PRIMARY KEY REFERENCES articles(id), value INTEGER NOT NULL CHECK(value IN(-1,0,1)), reason TEXT NOT NULL, at TEXT);
            CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY, text TEXT NOT NULL, at TEXT);
            CREATE TABLE IF NOT EXISTS runs(day TEXT PRIMARY KEY, attempts INTEGER NOT NULL, state TEXT, at TEXT, error TEXT);
            ''')
            db.execute('INSERT OR IGNORE INTO profile VALUES(1,1,?)', (json.dumps({'topics': TOPICS, 'rules': 'Mechanismen, belastbare Zahlen, Zielkonflikte und Reformoptionen erklären. Unterschiedliche Positionen zulassen.'}, ensure_ascii=False),))
    def db(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db
    def profile(self):
        with self.db() as db:
            row = db.execute('SELECT * FROM profile').fetchone()
            p = json.loads(row['data']); p['version'] = row['version']
            return p
    def save_profile(self, p):
        topics = p.get('topics')
        if not isinstance(topics, dict) or not 1 <= len(topics) <= 30 or any(not isinstance(k,str) or not 1 <= len(k) <= 80 or type(v) is not int or not 0 <= v <= 5 for k,v in topics.items()):
            raise ValueError('Ungültige Themenprioritäten')
        if not isinstance(p.get('rules'), str) or len(p['rules']) > 4000:
            raise ValueError('Regeln zu lang')
        data = json.dumps({'topics': topics, 'rules': p['rules']}, ensure_ascii=False)
        with self.db() as db:
            cur = db.execute('UPDATE profile SET data=?,version=version+1 WHERE id=1 AND version=?', (data,p.get('version')))
            if not cur.rowcount:
                raise ValueError('Profil wurde auf einem anderen Gerät geändert. Bitte neu laden.')
            db.execute('INSERT INTO audit(at,reason,data) VALUES(?,?,?)',(now(),'Explizite Profiländerung',data))
        return self.profile()
    def rate(self, aid, value, reason):
        if type(value) is not int or value not in (-1,0,1) or reason not in REASONS:
            raise ValueError('Ungültige Bewertung')
        with self.db() as db:
            db.execute('INSERT INTO ratings VALUES(?,?,?,?) ON CONFLICT(article) DO UPDATE SET value=excluded.value,reason=excluded.reason,at=excluded.at', (aid,value,reason,now()))
    def feedback(self, text):
        if not isinstance(text,str) or not text.strip() or len(text)>4000:
            raise ValueError('Bitte 1–4000 Zeichen eingeben')
        with self.db() as db:
            db.execute('INSERT INTO feedback(text,at) VALUES(?,?)',(text.strip(),now()))
    def context(self):
        with self.db() as db:
            return {'profile':self.profile(), 'ratings':[dict(r) for r in db.execute('SELECT ratings.*,topic,title FROM ratings JOIN articles ON article=articles.id')],
                    'feedback':[dict(r) for r in db.execute('SELECT * FROM feedback ORDER BY id')],
                    'history':[dict(r) for r in db.execute('SELECT * FROM articles ORDER BY day')],
                    'profile_changes':[dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id')]}
    def learning(self):
        """Small, transparent signals; explicit priorities always dominate. No click penalty."""
        c = self.context(); out={}
        for topic in c['profile']['topics']:
            rs=[r for r in c['ratings'] if r['topic']==topic and r['reason'] not in ('Schon bekannt','Zu oberflächlich')]
            out[topic]=round(sum(r['value'] for r in rs)/(len(rs)+8)*.5,3)
        return out
    def list_editions(self, at=None):
        t=instant(at or now())
        with self.db() as db:
            return [r['day'] for r in db.execute('SELECT day,available FROM editions ORDER BY day DESC') if instant(r['available'])<=t]
    def edition(self, day=None, at=None):
        dates=self.list_editions(at)
        if not dates or (day and day not in dates):
            return None
        with self.db() as db:
            return json.loads(db.execute('SELECT data FROM editions WHERE day=?',(day or dates[0],)).fetchone()['data'])
    def ratings(self):
        with self.db() as db:
            return {r['article']:dict(r) for r in db.execute('SELECT * FROM ratings')}
    def publish(self, edition):
        e=copy.deepcopy(edition)
        with self.db() as db:
            if db.execute('SELECT 1 FROM editions WHERE day=?',(e['date'],)).fetchone():
                return False
        start,end=instant(e['window_start']),instant(e['window_end'])
        if end<=start or instant(e['available_at'])<end:
            raise ValueError('Ungültiger Recherchezeitraum')
        if not 1<=len(e['articles'])<=15 or not 1<=len(e['headlines'])<=20:
            raise ValueError('Ungültige Ausgabegröße')
        history=self.context()['history']; seen=set(); events=set(); titles=[]
        for section in ('articles','headlines'):
            section_seen=set()
            for a in e[section]:
                url=canonical(a['url']); aid=article_id(url)
                if url in section_seen or not start<=instant(a['published_at'])<=end:
                    raise ValueError('Doppelter Link oder Artikel außerhalb des Zeitraums')
                section_seen.add(url)
                if not all(isinstance(a.get(k),str) and a[k].strip() for k in ('title','source','event')):
                    raise ValueError('Unvollständige Quellenangabe')
                if a.get('region') not in ('Österreich','International'):
                    raise ValueError('Region fehlt')
                if section=='articles':
                    if a.get('access') not in ('full','teaser') or not a.get('summary') or not a.get('facts') or not a.get('topic') or not a.get('kind'):
                        raise ValueError('Inhaltsbeleg fehlt')
                    if a['event'] in events or any(similar(a['title'],t) for t in titles):
                        raise ValueError('Inhaltliche Doppelung in Ausgabe')
                    events.add(a['event']); titles.append(a['title'])
                    for old in history:
                        if url==old['url']:
                            raise ValueError('Bereits ausgelieferter Link')
                        if a['event']==old['event'] or similar(a['title'],old['title']):
                            new=set(a['facts'])-set(json.loads(old['facts']))
                            if not new or not a.get('novelty'):
                                raise ValueError('Fortsetzung ohne belegte neue Information')
                    seen.add(aid)
                a['id']=aid
        # Two editorial categories: headline news and long reads cannot reuse URLs,
        # event IDs or near-identical titles. Historic demo issues are exempt from
        # publication validation, but the browser still removes overlaps.
        if not e.get('preview'):
            for deep in e['articles']:
                if deep.get('kind') in ('Nachricht', 'Kurzmeldung', 'Ticker'):
                    raise ValueError('Vertiefungen dürfen keine reinen Kurznachrichten sein')
            for deep in e['articles']:
                for headline in e['headlines']:
                    if (canonical(deep['url']) == canonical(headline['url'])
                            or deep.get('event') == headline.get('event')
                            or similar(deep['title'], headline['title'])):
                        raise ValueError('Identischer Artikel oder Ereignis in beiden Rubriken')
        if any(a.get('treat') for a in e['articles'][:-1]):
            raise ValueError('Zuckerl muss letzter Beitrag sein')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM editions WHERE day=?',(e['date'],)).fetchone():
                return False
            last=db.execute('SELECT data FROM editions ORDER BY day DESC LIMIT 1').fetchone()
            if last and instant(e['window_start'])>instant(json.loads(last['data'])['window_end']):
                raise ValueError('Lücke zum letzten Recherchezeitraum')
            db.execute('INSERT INTO editions VALUES(?,?,?)',(e['date'],e['available_at'],json.dumps(e,ensure_ascii=False)))
            for a in e['articles']:
                db.execute('INSERT INTO articles VALUES(?,?,?,?,?,?,?,NULL)',(a['id'],canonical(a['url']),a['topic'],a['event'],json.dumps(a['facts'],ensure_ascii=False),a['title'],e['date']))
        return True
