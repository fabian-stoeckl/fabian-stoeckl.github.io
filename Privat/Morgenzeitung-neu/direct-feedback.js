/* Browser interface for Morgenzeitung neu. Identical reader UI; isolated JSON feedback backend.
   The old Morgenzeitung uses distinct issue titles and stays untouched. */
'use strict';
const DirectFeedback=(()=>{
  const REPO='fabian-stoeckl/morgenzeitung-feedback';
  const TOKEN_KEY='morgenzeitung:github-token:v1';
  const RESET_KEY='morgenzeitung:github-token-reset:2026-10-20';
  const RECEIPTS_KEY='morgenzeitung-neu:github-receipts:v1';
  const API='https://api.github.com/repos/'+REPO;
  const PREFIX='[Morgenzeitung neu] Feedback ';
  const MARKER='MORGENZEITUNG_NEU_FEEDBACK_V1\n';
  const VALID=['','Sehr relevant','Teilweise relevant','Nicht relevant'];
  function readToken(store=localStorage){try{return store.getItem(TOKEN_KEY)||'';}catch(_){return '';}}
  function clearToken(store=localStorage){store.removeItem(TOKEN_KEY);}
  function resetOldTokenOnce(store=localStorage){
    try{
      if(store.getItem(RESET_KEY)==='1')return false;
      const had=!!store.getItem(TOKEN_KEY);
      store.removeItem(TOKEN_KEY);store.setItem(RESET_KEY,'1');return had;
    }catch(_){return false;}
  }
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
    const items=await feedbackHistory(token,transport);
    return items.find(x=>x.date===date)||null;
  }
  async function submit(date,ratings,feedback,token,store=localStorage,transport=fetch){
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Array.isArray(ratings)||ratings.length>40||typeof feedback!=='string'||feedback.length>4000)throw Error('Ungültige Feedbackdaten');
    const latest=await savedFeedback(date,token,store,transport);
    const byId=new Map((latest?.ratings||[]).map(r=>[r.id,r]));
    for(const r of ratings){
      if(!r||!((typeof r.id==='string')&&/^[a-f0-9]{16}$/.test(r.id))||!VALID.includes(r.value||'')||typeof r.reason!=='string'||r.reason.length>600)throw Error('Ungültige Artikelbewertung');
      byId.set(r.id,{id:r.id,value:r.value||'',reason:r.reason,section:r.section==='Heute wichtig'?'Heute wichtig':'Vertiefungen'});
    }
    const combined=[...byId.values()];
    const comment=feedback.trim()||latest?.feedback||'';
    if(!combined.length&&!comment)throw Error('Bitte mindestens eine Bewertung oder Feedback eingeben.');
    const title=PREFIX+date;
    const payload={version:1,date,ratings:combined.map(r=>({id:r.id,section:r.section,rating:r.value,reason:r.reason})),
      comment,origin:'website-explicit'};
    const body=MARKER+JSON.stringify(payload,null,2);
    const existing=latest?.number;
    // Avoid a useless GitHub PATCH on repeated clicks; always keep cross-device canonical state.
    const record=existing?await request(token,'/issues/'+existing,'GET',undefined,transport):null;
    if(record?.body===body)return {ok:true,existing:true,html_url:record.html_url};
    const result=await request(token,existing?'/issues/'+existing:'/issues',existing?'PATCH':'POST',{title,body},transport);
    if(!Number.isSafeInteger(result.number)||!result.html_url?.startsWith('https://github.com/'+REPO+'/issues/'))throw Error('GitHub hat das Speichern nicht bestätigt.');
    try{const receipts=readReceipts(store);receipts[date]={number:result.number,url:result.html_url};store.setItem(RECEIPTS_KEY,JSON.stringify(receipts));}catch(_){}
    return {ok:true,updated:!!existing,html_url:result.html_url};
  }
  return {REPO,TOKEN_KEY,RESET_KEY,RECEIPTS_KEY,readToken,clearToken,saveToken,resetOldTokenOnce,verify,feedbackHistory,readReceipts,savedFeedback,submit};
})();
if(typeof module!=='undefined')module.exports=DirectFeedback;
