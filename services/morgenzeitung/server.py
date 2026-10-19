"""Private API. Run behind HTTPS in production; no credentials in static website."""
import hmac
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from core import Store

ROOT=Path(__file__).resolve().parents[2]/'Privat/Pressespiegel'
TOKEN=os.environ.get('PAPER_TOKEN','')
ORIGIN=os.environ.get('PAPER_ORIGIN','https://www.fabian-stoeckl.com')
PREVIEW=os.environ.get('PAPER_PREVIEW')=='1'
DB=os.environ.get('PAPER_DB','/data/morgenzeitung.sqlite')
STORE=None

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Never put personal URLs, feedback or credentials in HTTP logs.
    def send_headers(self, code, kind='application/json; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type',kind)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        if self.headers.get('Origin')==ORIGIN:
            self.send_header('Access-Control-Allow-Origin',ORIGIN)
            self.send_header('Vary','Origin')
        self.end_headers()
    def result(self, data, code=200):
        self.send_headers(code); self.wfile.write(json.dumps(data,ensure_ascii=False).encode())
    def do_OPTIONS(self):
        if self.headers.get('Origin')!=ORIGIN:
            return self.result({'error':'Nicht erlaubt'},403)
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin',ORIGIN)
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers','Authorization, Content-Type')
        self.end_headers()
    def authorized(self):
        supplied=self.headers.get('Authorization','').removeprefix('Bearer ')
        # Preview serves only synthetic test feedback on loopback, never production data.
        return PREVIEW or (bool(TOKEN) and hmac.compare_digest(supplied,TOKEN))
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/health':
            return self.result({'ok':True})
        if PREVIEW and path in ('/','/index.html','/app.js','/style.css','/config.json'):
            if path=='/config.json':
                return self.result({'api':'','preview':True})
            p=ROOT/('index.html' if path=='/' else path[1:])
            self.send_headers(200, 'text/html; charset=utf-8' if p.suffix=='.html' else 'text/javascript; charset=utf-8' if p.suffix=='.js' else 'text/css; charset=utf-8')
            return self.wfile.write(p.read_bytes())
        if not self.authorized():
            return self.result({'error':'Bitte anmelden'},401)
        q=parse_qs(urlsplit(self.path).query)
        if path=='/api/editions':
            return self.result({'dates':STORE.list_editions(),'preview':PREVIEW,'scheduler_enabled':os.environ.get('PAPER_AUTOMATION')=='1'})
        if path=='/api/edition':
            e=STORE.edition(q.get('date',[None])[0]); return self.result(e or {'error':'Noch keine Ausgabe verfügbar'},200 if e else 404)
        if path=='/api/profile':
            return self.result({'profile':STORE.profile(),'learning':STORE.learning(),'history':STORE.context()['profile_changes']})
        if path=='/api/ratings':
            return self.result(STORE.ratings())
        return self.result({'error':'Nicht gefunden'},404)
    def do_POST(self):
        if not self.authorized():
            return self.result({'error':'Bitte anmelden'},401)
        if self.headers.get('Origin') and self.headers['Origin']!=ORIGIN and not PREVIEW:
            return self.result({'error':'Nicht erlaubt'},403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=16000:
                raise ValueError('Anfrage zu groß oder leer')
            data=json.loads(self.rfile.read(size))
            path=urlsplit(self.path).path
            if path=='/api/rating':
                STORE.rate(data['id'],data['value'],data.get('reason',''))
            elif path=='/api/feedback':
                STORE.feedback(data['text'])
            elif path=='/api/profile':
                return self.result(STORE.save_profile(data))
            else:
                return self.result({'error':'Nicht gefunden'},404)
            self.result({'saved':True})
        except (ValueError,KeyError,TypeError,sqlite3.IntegrityError):
            self.result({'error':'Nicht gespeichert. Eingabe prüfen; bei Profilkonflikt neu laden.'},400)
        except sqlite3.Error:
            self.result({'error':'Speicher nicht erreichbar. Bitte erneut versuchen.'},503)

if __name__=='__main__':
    if not PREVIEW and len(TOKEN)<32:
        raise SystemExit('PAPER_TOKEN mit mindestens 32 Zeichen erforderlich')
    if PREVIEW and os.environ.get('PAPER_HOST','127.0.0.1')!='127.0.0.1':
        raise SystemExit('Vorschau ausschließlich auf Loopback')
    Path(DB).parent.mkdir(parents=True,exist_ok=True)
    os.umask(0o077)
    STORE=Store(DB)
    ThreadingHTTPServer((os.environ.get('PAPER_HOST','127.0.0.1'),int(os.environ.get('PORT','8765'))),Handler).serve_forever()
