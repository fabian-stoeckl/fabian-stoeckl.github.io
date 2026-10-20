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
    if(!/^(\/issues(?:\/\d+)?|)$/.test(path)) throw Error('Unzulässiger GitHub-Pfad.');
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
  function buildFeedback(date,ratings,feedback) {
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Array.isArray(ratings)||ratings.length>40||
       typeof feedback!=='string'||feedback.length>4000) throw Error('Ungültige Feedback-Daten.');
    const ids=new Set();
    for(const r of ratings) {
      if(!r||typeof r.id!=='string'||!/^[a-f0-9]{16,24}$/.test(r.id)||ids.has(r.id)||
         !['','Sehr relevant','Teilweise relevant','Nicht relevant'].includes(r.value||'')||
         typeof r.reason!=='string'||r.reason.length>600) throw Error('Ungültige Artikelbewertung.');
      ids.add(r.id);
    }
    if(!ratings.length&&!feedback.trim()) throw Error('Bitte mindestens eine Bewertung oder Feedback eingeben.');
    return {
      title:'[Morgenzeitung] Sammelbewertung '+date,
      body:GitHubPaper.batchBody(date,ratings,feedback)
    };
  }
  function parsePrevious(body,date){
    if(typeof body!=='string'||!body.startsWith('Typ: Sammelbewertung\nAusgabe: '+date+'\n'))
      throw Error('Vorheriges Feedback hat ein unerwartetes Format; nichts überschrieben.');
    const marker='\n\nFeedback:\n',cut=body.lastIndexOf(marker);
    if(cut<0)throw Error('Vorheriges Feedback ist unvollständig; nichts überschrieben.');
    const ratings=[];
    for(const line of body.slice(0,cut).split(/\n\n(?=Artikel-ID: )/)){
      if(!line.startsWith('Artikel-ID: '))continue;
      const m=/^Artikel-ID: ([a-f0-9]{16,24})\nBewertung: ([^\n]*)\nBegründung: ([\s\S]*)$/.exec(line);
      if(!m)throw Error('Vorherige Artikelbewertungen konnten nicht gelesen werden.');
      const v=m[2]==='Keine Auswahl'?'':m[2];
      if(!['','Sehr relevant','Teilweise relevant','Nicht relevant'].includes(v))
        throw Error('Unbekannte alte Artikelbewertung.');
      ratings.push({id:m[1],value:v,reason:m[3].trimEnd()==='–'?'':m[3].trimEnd()});
    }
    return {ratings,feedback:body.slice(cut+marker.length)};
  }
  async function submit(date,ratings,feedback,token,store=localStorage,transport=fetch,cryptoAPI=crypto) {
    const receipts=readReceipts(store),previous=receipts[date];
    const patch=previous&&Number.isSafeInteger(previous.number)&&previous.number>0;
    let combined=ratings,comment=feedback;
    if(patch){
      const remote=await request(token,'/issues/'+previous.number,'GET',undefined,transport);
      if(remote.number!==previous.number)throw Error('GitHub hat ein anderes Feedback-Issue geliefert.');
      const saved=parsePrevious(remote.body,date);
      const byId=new Map(saved.ratings.map(r=>[r.id,r]));
      for(const r of ratings)byId.set(r.id,r);
      combined=[...byId.values()];
      if(!comment.trim())comment=saved.feedback;
    }
    const issue=buildFeedback(date,combined,comment);
    const hash=await fingerprint(issue.body,cryptoAPI);
    if(previous?.hash===hash&&Number.isSafeInteger(previous.number)){
      return {ok:true,existing:true,html_url:previous.url};
    }
    let result;
    try {
      result=await request(token,patch?'/issues/'+previous.number:'/issues',patch?'PATCH':'POST',issue,transport);
    } catch(e) {throw e;} // Keep inputs and receipt unchanged on failure.
    if(!Number.isSafeInteger(result.number)||result.number<=0||
      typeof result.html_url!=='string'||
      !result.html_url.startsWith('https://github.com/'+REPO+'/issues/')) {
      throw Error('GitHub hat die Speicherung nicht vollständig bestätigt.');
    }
    receipts[date]={hash,number:result.number,url:result.html_url};
    store.setItem(RECEIPTS_KEY,JSON.stringify(receipts));
    return {ok:true,updated:patch,html_url:result.html_url};
  }
  return {REPO,TOKEN_KEY,RECEIPTS_KEY,readToken,saveToken,clearToken,verify,buildFeedback,submit,readReceipts};
})();
if(typeof module!=='undefined')module.exports=DirectFeedback;
