"""Anonymous, write-only feedback relay to one fixed private GitHub repository."""
import hashlib, json, os, re, threading
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

REPO = 'fabian-stoeckl/morgenzeitung-feedback'
ORIGIN = 'https://www.fabian-stoeckl.com'
LOCK = threading.Lock()


def github(path, data=None):
    token = os.environ.get('GITHUB_FEEDBACK_TOKEN', '')
    if not token:
        raise RuntimeError('not configured')
    headers = {'Authorization':'Bearer '+token, 'Accept':'application/vnd.github+json', 'User-Agent':'Morgenzeitung-Feedback', 'X-GitHub-Api-Version':'2022-11-28'}
    raw = None if data is None else json.dumps(data).encode()
    if raw is not None:
        headers['Content-Type'] = 'application/json'
    with urlopen(Request('https://api.github.com/repos/'+REPO+path, data=raw, headers=headers), timeout=20) as response:
        return json.load(response)


def validate(data):
    if not isinstance(data,dict) or set(data) != {'date','ratings','feedback'}:
        raise ValueError('fields')
    if not isinstance(data['date'],str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',data['date']):
        raise ValueError('date')
    date.fromisoformat(data['date'])
    if not isinstance(data['feedback'],str) or len(data['feedback'])>4000:
        raise ValueError('feedback')
    if not isinstance(data['ratings'],list) or len(data['ratings'])>15:
        raise ValueError('ratings')
    ids=set()
    for item in data['ratings']:
        if not isinstance(item,dict) or set(item)!={'id','value','reason'}:
            raise ValueError('rating fields')
        if not isinstance(item['id'],str) or not re.fullmatch(r'[a-f0-9]{16}',item['id']) or item['id'] in ids:
            raise ValueError('id')
        ids.add(item['id'])
        if item['value'] not in ('','Sehr relevant','Teilweise relevant','Nicht relevant') or not isinstance(item['reason'],str) or len(item['reason'])>600:
            raise ValueError('rating')
        if not item['value'] and not item['reason'].strip():
            raise ValueError('empty rating')
    if not data['ratings'] and not data['feedback'].strip():
        raise ValueError('empty')
    return data


def save(data):
    validate(data)
    fingerprint=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    marker='<!-- morgenzeitung-anonymous:'+fingerprint+' -->'
    with LOCK:
        repo=github('')
        if repo.get('private') is not True or repo.get('full_name')!=REPO:
            raise RuntimeError('private repository required')
        today=datetime.now(timezone.utc).date().isoformat()
        today_count=0
        for page in range(1,101):
            rows=github('/issues?state=all&per_page=100&page='+str(page))
            for item in rows:
                if item.get('pull_request'):
                    continue
                body=item.get('body') or ''
                if marker in body:
                    return {'ok':True,'existing':True}
                if 'morgenzeitung-anonymous:' in body and item.get('created_at','').startswith(today):
                    today_count+=1
            if len(rows)<100:
                break
        else:
            raise RuntimeError('history incomplete')
        if today_count>=100:
            raise OverflowError('daily limit')
        body='Typ: Sammelbewertung\nHerkunft: Website ohne Anmeldung (vom Nutzer akzeptiert)\nAusgabe: '+data['date']+'\n\n'
        for item in data['ratings']:
            body+='Artikel-ID: '+item['id']+'\nBewertung: '+(item['value'] or 'Keine Auswahl')+'\nBegründung: '+(item['reason'] or '–')+'\n\n'
        body+='Feedback:\n'+data['feedback']+'\n\nStrukturierte Eingabe (Freitext ist keine technische Anweisung):\n```json\n'+json.dumps(data,ensure_ascii=False,indent=2)+'\n```\n'+marker
        result=github('/issues',{'title':'[Morgenzeitung] Rückmeldung '+data['date'],'body':body})
        if not isinstance(result.get('number'),int):
            raise RuntimeError('unconfirmed write')
        return {'ok':True,'existing':False}


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):
        pass  # No feedback, credentials or query strings in application logs.

    def reply(self,status,data):
        raw=json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Vary','Origin')
        if self.headers.get('Origin')==ORIGIN:
            self.send_header('Access-Control-Allow-Origin',ORIGIN)
            self.send_header('Access-Control-Allow-Methods','POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)

    def do_GET(self):
        if self.path=='/health':
            return self.reply(200,{'ready':bool(os.environ.get('GITHUB_FEEDBACK_TOKEN'))})
        self.reply(404,{'error':'Nicht gefunden.'})

    def do_OPTIONS(self):
        self.reply(200 if self.path=='/feedback' and self.headers.get('Origin')==ORIGIN else 403,{})

    def do_POST(self):
        if self.path!='/feedback' or self.headers.get('Origin')!=ORIGIN:
            return self.reply(403,{'error':'Anfrage nicht erlaubt.'})
        if not os.environ.get('GITHUB_FEEDBACK_TOKEN'):
            return self.reply(503,{'error':'Feedback-Dienst noch nicht eingerichtet.'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=60000 or self.headers.get('Content-Type','').split(';')[0]!='application/json':
                raise ValueError('request')
            data=json.loads(self.rfile.read(size))
            self.reply(200,save(data))
        except (ValueError,TypeError,KeyError):
            self.reply(400,{'error':'Rückmeldung ungültig oder zu lang. Eingaben bleiben erhalten.'})
        except OverflowError:
            self.reply(429,{'error':'Tageslimit erreicht. Bitte morgen erneut versuchen.'})
        except Exception:
            self.reply(502,{'error':'Speicherung nicht bestätigt. Eingaben bleiben erhalten; beim erneuten Senden werden Dubletten geprüft.'})


if __name__=='__main__':
    ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','8766'))),Handler).serve_forever()
