/* Direct browser-to-GitHub feedback. Never embed access tokens in public files. */
'use strict';
const DirectFeedback = (() => {
  const REPO='fabian-stoeckl/morgenzeitung-feedback';
  const TOKEN_KEY='morgenzeitung:github-token:v1';
  const RECEIPTS_KEY='morgenzeitung:github-receipts:v1';
  const API='https://api.github.com/repos/'+REPO;
  function readToken(store=localStorage) {
    try {return store.getItem(TOKEN_KEY)||'';} catch (_) {return '';}
  }
  function clearToken(store=localStorage) {store.removeItem(TOKEN_KEY);}
  function saveToken(token,store=localStorage) {
    const value=String(token||'').trim();
    if(!value.startsWith('github_pat_')||value.length<30||value.length>500||/\s/.test(value)) throw Error('Bitte ausschließlich einen eingeschränkten Fine-grained GitHub-Token verwenden.');
    store.setItem(TOKEN_KEY,value);
    return value;
  }
  async function request(token,path,method='GET',body,transport=fetch) {
    if(!/^(\/issues(?:\/\d+)?|\/issues\?state=all&per_page=100&page=[123]|)$/.test(path)) throw Error('Unzulässiger GitHub-Pfad.');
    if(path.includes('?')&&method!=='GET')throw Error('Nur lesender Aufruf erlaubt.');
    const response=await transport(API+path,{
      method,credentials:'omit',redirect:'error',referrerPolicy:'no-referrer',
      cache:'no-store',
      headers:{
        'Accept':'application/vnd.github+json',
        'Authorization':'Bearer '+token,
        ...(body?{'Content-Type':'application/json'}:{})
      },
      ...(body?{body:JSON.stringify(body)}:{})
    });
    if(!response.ok) {
      if(response.status===401) throw Error('GitHub-Zugang ungültig oder abgelaufen. Bitte Token erneuern.');
      if(response.status===403) throw Error('GitHub verweigert den Zugriff. Bitte Repository und Issues-Schreibrechte prüfen.');
      if(response.status===404) throw Error('Feedback-Repository oder früherer Eintrag nicht gefunden.');
      if(response.status===422) throw Error('GitHub lehnt diese Rückmeldung ab. Bitte Angaben prüfen.');
      if(response.status===429) throw Error('GitHub-Limit erreicht. Später erneut versuchen.');
      throw Error('GitHub konnte die Rückmeldung nicht speichern (HTTP '+response.status+').');
    }
    return response.json();
  }
  async function verify(token,transport=fetch) {
    const result=await request(token,'','GET',undefined,transport);
    if(result.full_name!==REPO||result.private!==true)
      throw Error('Nur das vereinbarte private Feedback-Repository ist erlaubt.');
    return true;
  }
  function readReceipts(store=localStorage) {
    try {const r=JSON.parse(store.getItem(RECEIPTS_KEY)||'{}');return r&&typeof r==='object'&&!Array.isArray(r)?r:{};}
    catch (_) {return {};}
  }
  async function fingerprint(value,cryptoAPI=crypto) {
    const bytes=new TextEncoder().encode(value);
    const hash=await cryptoAPI.subtle.digest('SHA-256',bytes);
    return [...new Uint8Array(hash)].map(v=>v.toString(16).padStart(2,'0')).join('');
  }
  async function feedbackHistory(token,transport=fetch) {
    const issues=[];
    for(let page=1;page<=3;page++){
      const batch=await request(token,'/issues?state=all&per_page=100&page='+page,'GET',undefined,transport);
      if(!Array.isArray(batch))throw Error('GitHub hat keine gültige Feedback-Liste zurückgegeben.');
      for(const issue of batch){
        if(!/^\[Morgenzeitung\] Sammelbewertung \d{4}-\d{2}-\d{2}$/.test(issue.title||'')||
           typeof issue.body!=='string'||issue.body.includes('TEST: true')||issue.pull_request)continue;
        try {
          const parsed=GitHubPaper.parseBatchBody(issue.body);
          if(issue.title.endsWith(parsed.date))
            issues.push({number:issue.number,updated_at:issue.updated_at||'',...parsed});
        }catch(_){/* Skip malformed records; never interpret them as user preferences. */}
      }
      if(batch.length<100)break;
    }
    const latest=new Map();
    for(const item of issues){
      const old=latest.get(item.date);
      if(!old||item.updated_at>=old.updated_at)latest.set(item.date,item);
    }
    return [...latest.values()].sort((a,b)=>b.date.localeCompare(a.date));
  }
  function buildFeedback(date,ratings,feedback) {
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Array.isArray(ratings)||ratings.length>40||
       typeof feedback!=='string'||feedback.length>4000) throw Error('Ungültige Feedback-Daten.');
    const ids=new Set();
    for(const r of ratings) {
      if(!r||typeof r.id!=='string'||!/^[a-f0-9]{16}$/.test(r.id)||ids.has(r.id)||
         !['','Sehr relevant','Teilweise relevant','Nicht relevant'].includes(r.value||'')||
         typeof r.reason!=='string'||r.reason.length>600||
         (r.section!==undefined&&!['Heute wichtig','Vertiefungen'].includes(r.section))) throw Error('Ungültige Artikelbewertung.');
      ids.add(r.id);
    }
    if(!ratings.length&&!feedback.trim()) throw Error('Bitte mindestens eine Bewertung oder Feedback eingeben.');
    return {
      title:'[Morgenzeitung] Sammelbewertung '+date,
      body:GitHubPaper.batchBody(date,ratings,feedback)
    };
  }
  async function savedFeedback(date,token,store=localStorage,transport=fetch) {
    const previous=readReceipts(store)[date];
    if(!previous||!Number.isSafeInteger(previous.number)||previous.number<=0)return null;
    const existing=await request(token,'/issues/'+previous.number,'GET',undefined,transport);
    const parsed=GitHubPaper.parseBatchBody(existing.body);
    if(parsed.date!==date)throw Error('Frühere Bewertung gehört zu einer anderen Ausgabe. Nichts überschrieben.');
    return parsed;
  }
  async function submit(date,ratings,feedback,token,store=localStorage,transport=fetch,cryptoAPI=crypto) {
    const receipts=readReceipts(store),previous=receipts[date];
    // Reload the canonical saved issue before patching: an update from either tab
    // must never erase ratings previously submitted in the other tab.
    const saved=await savedFeedback(date,token,store,transport);
    const merged=new Map((saved?.ratings||[]).map(r=>[r.id,r]));
    for(const r of ratings)merged.set(r.id,r);
    const combined=[...merged.values()];
    const combinedFeedback=feedback.trim()?feedback:saved?.feedback||'';
    const issue=buildFeedback(date,combined,combinedFeedback);
    const hash=await fingerprint(issue.body,cryptoAPI);
    if(previous?.hash===hash&&Number.isSafeInteger(previous.number)) {
      return {ok:true,existing:true,html_url:previous.url};
    }
    const patch=!!(previous&&Number.isSafeInteger(previous.number)&&previous.number>0);
    const result=await request(token,patch?'/issues/'+previous.number:'/issues',patch?'PATCH':'POST',issue,transport);
    if(!Number.isSafeInteger(result.number)||result.number<=0||
      typeof result.html_url!=='string'||
      !result.html_url.startsWith('https://github.com/'+REPO+'/issues/')) {
      throw Error('GitHub hat die Speicherung nicht vollständig bestätigt.');
    }
    receipts[date]={hash,number:result.number,url:result.html_url};
    store.setItem(RECEIPTS_KEY,JSON.stringify(receipts));
    return {ok:true,updated:patch,html_url:result.html_url};
  }
  return {REPO,TOKEN_KEY,RECEIPTS_KEY,readToken,saveToken,clearToken,verify,buildFeedback,submit,savedFeedback,feedbackHistory,readReceipts};
})();
if(typeof module!=='undefined')module.exports=DirectFeedback;
