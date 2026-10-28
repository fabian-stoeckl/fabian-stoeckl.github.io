"""Small Pressespiegel I/O checks. No ranking, scoring or interpretation of feedback."""
import argparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

MARKER='PRESSESPIEGEL_FEEDBACK_V1\n'
LEGACY='MORGENZEITUNG_V3_FEEDBACK_V1\n'

def url_key(value):
    p=urlsplit(value)
    if p.scheme!='https' or not p.hostname or p.username or p.password:
        raise ValueError('Expected original HTTPS URL')
    query=urlencode(sorted((k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid')))
    return urlunsplit((p.scheme,p.netloc.lower(),p.path.rstrip('/'),query,''))

def validate(edition):
    date.fromisoformat(edition['date'])
    t=datetime.fromisoformat(edition['researched_at'].replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('researched_at needs timezone')
    if edition.get('kind') not in ('researched','imported'):raise ValueError('Missing edition kind')
    allowed={'date','researched_at','kind','note','source_edition','articles','headlines'}
    if set(edition)-allowed:raise ValueError('Unknown public edition field')
    if edition['kind']=='imported' and not (edition.get('source_edition') and edition.get('note')):
        raise ValueError('Imported content needs origin and visible note')
    ids=set();urls=set()
    for section,limit in [('articles',15),('headlines',20)]:
        rows=edition[section]
        if not isinstance(rows,list) or len(rows)>limit:raise ValueError('Invalid section size')
        for row in rows:
            if set(row)-{'id','title','source','url','published_at','summary','basis','why','source_context'}:
                raise ValueError('Unknown public article field')
            for key in ['id','title','source','url','published_at','summary']:
                if not isinstance(row.get(key),str) or not row[key].strip():raise ValueError('Missing '+key)
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',row['id']):raise ValueError('Invalid stable ID')
            date.fromisoformat(row['published_at'][:10])
            if row['basis'] not in ('headline','teaser','read'):raise ValueError('Invalid source basis')
            if 'why' in row and not isinstance(row['why'],str):raise ValueError('Invalid explanation')
            key=url_key(row['url'])
            if row['id'] in ids or key in urls:raise ValueError('Duplicate article')
            ids.add(row['id']);urls.add(key)
    if not ids:raise ValueError('Empty edition')

def feedback_packet(issues,state):
    """Return changed source texts, never infer interests or add up votes."""
    seen=dict(state.get('issues',{}));changed=[]
    submissions=set()
    for issue in sorted(issues,key=lambda x:(x.get('updated_at',''),x.get('number',0)),reverse=True):
        body=issue.get('body') or '';title=issue.get('title','')
        if issue.get('pull_request') or not body.startswith((MARKER,LEGACY)):continue
        marker=MARKER if body.startswith(MARKER) else LEGACY
        try:
            data=json.loads(body[len(marker):]);date.fromisoformat(data['date'])
            prefix='[Pressespiegel] Feedback ' if marker==MARKER else '[Morgenzeitung 3] Feedback '
            if title!=prefix+data['date'] or data.get('origin')!='website-explicit' or data.get('test'):continue
            if not isinstance(data.get('ratings'),list):continue
            if marker==MARKER:
                sid=data['submission_id']
                if not isinstance(sid,str) or not sid:continue
                if sid in submissions:continue
                submissions.add(sid)
        except (ValueError,KeyError,TypeError):continue
        key=str(issue['number']);version={'updated_at':issue.get('updated_at',''),'sha256':hashlib.sha256(body.encode()).hexdigest()}
        if seen.get(key)!=version:
            changed.append({'number':issue['number'],'updated_at':issue.get('updated_at',''),'feedback':data})
        seen[key]=version
    return {'needs_reading':changed,'next_state':{**state,'issues':seen},
            'note':'State proposal only: save after actual reading and profile update. No automatic interpretation.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['verify','feedback']);p.add_argument('--root',default='Privat/Pressespiegel/data');p.add_argument('--issues');p.add_argument('--state');a=p.parse_args()
    if a.action=='feedback':
        print(json.dumps(feedback_packet(json.loads(Path(a.issues).read_text()),json.loads(Path(a.state).read_text())),ensure_ascii=False,indent=2));return
    root=Path(a.root);dates=json.loads((root/'index.json').read_text())['dates']
    if dates!=sorted(set(dates),reverse=True):raise ValueError('Index must be unique and descending')
    if set(dates)!={x.stem for x in root.glob('????-??-??.json')}:raise ValueError('Index and editions differ')
    for day in dates:
        date.fromisoformat(day);ed=json.loads((root/(day+'.json')).read_text());validate(ed)
        if ed['date']!=day:raise ValueError('Date mismatch')
    print(f'PASS: {len(dates)} editions; structure only, editorial source review remains required')
if __name__=='__main__':main()
