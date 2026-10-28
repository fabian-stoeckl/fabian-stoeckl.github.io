/* Private, explicit GitHub feedback backend for the Persönliche Zeitung.
   Historical issue prefix and localStorage key remain stable for continuity. */
'use strict';
const DirectFeedback=(()=>{
  const REPO='fabian-stoeckl/morgenzeitung-feedback';
  const TOKEN_KEY='morgenzeitung:github-token:v1';
  const RECEIPTS_KEY='morgenzeitung-v3:github-receipts:v1';
  const API='https://api.github.com/repos/'+REPO;
  const PREFIX='[Morgenzeitung 3] Feedback ';
  const MARKER='MORGENZEITUNG_V3_FEEDBACK_V1\n';
  const VALID=['','Sehr relevant','Teilweise relevant','Nicht relevant'];
  function readToken(store=localStorage){try{return store.getItem(TOKEN_KEY)||'';}catch(_){return '';}}
  function clearToken(store=localStorage){store.removeItem(TOKEN_KEY);}
  function saveToken(token,store=localStorage){
    const value=String(token||'').trim();
    if(!/^github_pat_[A-Za-z0-9_]{20,500}$/.test(value))throw Error('Bitte ausschließlich einen eingeschränkten Fine-grained GitHub-Token verwenden.');
    store.setItem(TOKEN_KEY,value);return value;
  }
  async function request(token,path,method='GET',body,transport=fetch){
    if(!/^(?:|\/issues(?:\/\d+)?|\/issues\?state=all&per_page=100&page=(?:[1-9]|1[0-9]|20))$/.test(path))throw Error('Unzulässiger GitHub-Pfad.');
    const r=await transport(API+path,{method,credentials:'omit',cache:'no-store',redirect:'error',referrerPolicy:'no-referrer',
      headers:{'Accept':'application/vnd.github+json','Authorization':'Bearer '+token,...(body?{'Content-Type':'application/json'}:{})},
      ...(body?{body:JSON.stringify(body)}:{})});
    if(!r.ok){
      if(r.status===401)throw Error('GitHub-Zugang ungültig oder abgelaufen. Bitte Token erneuern.');
      if(r.status===403)throw Error('GitHub verweigert Zugriff. Bitte Berechtigungen prüfen.');
      throw Error('GitHub konnte die Rückmeldung nicht speichern (HTTP '+r.status+').');
    }
    return r.json();
  }
  async function verify(token,transport=fetch){
    const r=await request(token,'','GET',undefined,transport);
    if(r.full_name!==REPO||r.private!==true)throw Error('Nur das private Feedback-Repository ist erlaubt.');
    return true;
  }
  function parse(issue){
    if(!issue||typeof issue.body!=='string'||!issue.body.startsWith(MARKER)||!issue.title?.startsWith(PREFIX)||issue.pull_request)return null;
    try{
      const x=JSON.parse(issue.body.slice(MARKER.length));
      if(!/^\d{4}-\d{2}-\d{2}$/.test(x.date)||issue.title!==PREFIX+x.date||!Array.isArray(x.ratings)||issue.body.includes('TEST: true'))return null;
      const ratings=x.ratings.filter(r=>r&&/^[a-f0-9]{16}$/.test(r.id)&&VALID.includes(r.rating||'')).map(r=>({
        id:r.id,value:r.rating||'',reason:String(r.reason||'').slice(0,600),
        section:r.section==='Heute wichtig'?'Heute wichtig':'Vertiefungen'
      }));
      return {date:x.date,ratings,feedback:typeof x.comment==='string'?x.comment:'',number:issue.number,updated_at:issue.updated_at||''};
    }catch(_){return null;}
  }
  async function feedbackHistory(token,transport=fetch){
    const out=[];
    for(let page=1;page<=20;page++){
      const rows=await request(token,'/issues?state=all&per_page=100&page='+page,'GET',undefined,transport);
      if(!Array.isArray(rows))throw Error('Ungültige GitHub-Feedback-Antwort');
      for(const row of rows){const v=parse(row);if(v)out.push(v);}
      if(rows.length<100)break;
    }
    return out.sort((a,b)=>b.updated_at.localeCompare(a.updated_at));
  }
  function readReceipts(store=localStorage){
    try{const v=JSON.parse(store.getItem(RECEIPTS_KEY)||'{}');return v&&typeof v==='object'?v:{};}
    catch(_){return {};}
  }
  async function savedFeedback(date,token,store=localStorage,transport=fetch){
    // Fast path: use the recorded private issue number. Still GET the canonical
    // issue from GitHub, not a potentially stale browser cache.
    const receipt=readReceipts(store)[date];
    if(receipt && Number.isSafeInteger(receipt.number) && receipt.number>0){
      try{
        const current=parse(await request(token,'/issues/'+receipt.number,'GET',undefined,transport));
        if(current?.date===date)return current;
      }catch(err){
        // Authorization failures must not be silently swallowed.
        if(/ungültig oder abgelaufen|verweigert Zugriff/.test(err.message))throw err;
      }
    }
    const items=await feedbackHistory(token,transport);
    return items.find(x=>x.date===date)||null;
  }
  async function submit(date,ratings,feedback,token,store=localStorage,transport=fetch){
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Array.isArray(ratings)||
       ratings.length>100||typeof feedback!=='string'||feedback.length>4000)
      throw Error('Ungültige Feedbackdaten');
    const intended=new Map();
    for(const r of ratings){
      if(!r||typeof r.id!=='string'||!/^[a-f0-9]{16}$/.test(r.id)||
         !VALID.includes(r.value||'')||typeof r.reason!=='string'||r.reason.length>600)
        throw Error('Ungültige Artikelbewertung');
      intended.set(r.id,{id:r.id,value:r.value||'',reason:r.reason,
                         section:r.section==='Heute wichtig'?'Heute wichtig':'Vertiefungen'});
    }
    const comment=feedback.trim();
    let previousIssue=null;
    // Optimistic retries: read the canonical issue, merge intended changes,
    // write, then verify that the submitted ratings survived. GitHub Issues
    // PATCH has no atomic compare-and-swap; this is best effort, not a lock.
    for(let attempt=0;attempt<3;attempt++){
      const latest=attempt&&previousIssue?previousIssue:
        await savedFeedback(date,token,store,transport);
      const existing=latest?.number;
      const record=existing?await request(token,'/issues/'+existing,'GET',undefined,transport):null;
      const fresh=record?parse(record):null;
      if(existing&&!fresh)throw Error('Aktuelle GitHub-Bewertungen konnten nicht sicher gelesen werden.');
      const base=fresh||latest;
      const byId=new Map((base?.ratings||[]).map(r=>[r.id,r]));
      for(const [id,row] of intended)byId.set(id,row);
      const mergedComment=comment||base?.feedback||'';
      if(!byId.size&&!mergedComment)throw Error('Bitte mindestens eine Bewertung oder Feedback eingeben.');
      const title=PREFIX+date;
      const payload={version:1,date,
        ratings:[...byId.values()].map(r=>({id:r.id,section:r.section,rating:r.value,reason:r.reason})),
        comment:mergedComment,origin:'website-explicit'};
      const body=MARKER+JSON.stringify(payload,null,2);
      if(record?.body===body)return {ok:true,existing:true,html_url:record.html_url};
      const result=await request(token,existing?'/issues/'+existing:'/issues',
                                 existing?'PATCH':'POST',{title,body},transport);
      if(!Number.isSafeInteger(result.number)||
         !result.html_url?.startsWith('https://github.com/'+REPO+'/issues/'))
        throw Error('GitHub hat das Speichern nicht bestätigt.');
      const receipt={number:result.number,url:result.html_url};
      try{
        const receipts=readReceipts(store);
        receipts[date]=receipt;store.setItem(RECEIPTS_KEY,JSON.stringify(receipts));
      }catch(_){}
      const confirmed=await request(token,'/issues/'+result.number,'GET',undefined,transport);
      const verified=parse(confirmed);
      if(!verified)throw Error('Gespeichertes GitHub-Feedback konnte nicht nachgelesen werden.');
      const found=new Map(verified.ratings.map(row=>[row.id,row]));
      const preserved=[...intended].every(([id,row])=>
        found.has(id)&&found.get(id).value===row.value&&
        found.get(id).reason===row.reason&&found.get(id).section===row.section);
      if(preserved&&(!comment||verified.feedback===comment))
        return {ok:true,updated:!!existing,html_url:result.html_url};
      // A competing edit has won at least one write; merge it on the next read.
      previousIssue=verified;
    }
    throw Error('Gleichzeitige Änderungen konnten nicht sicher zusammengeführt werden. Bitte erneut speichern.');
  }
  return {REPO,TOKEN_KEY,RECEIPTS_KEY,readToken,clearToken,saveToken,verify,feedbackHistory,readReceipts,savedFeedback,submit};
})();
if(typeof module!=='undefined')module.exports=DirectFeedback;
