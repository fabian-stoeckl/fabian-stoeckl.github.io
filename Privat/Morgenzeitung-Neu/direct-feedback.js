/* Private, explicit GitHub feedback backend for the Morgenzeitung Neu.
   Historical issue prefix and localStorage key remain stable for continuity. */
'use strict';
const DirectFeedback=(()=>{
  const REPO='fabian-stoeckl/morgenzeitung-feedback';
  const TOKEN_KEY='morgenzeitung:github-token:v1';
  const RECEIPTS_KEY='morgenzeitung-neu:github-receipts:v1';
  const API='https://api.github.com/repos/'+REPO;
  const PREFIX='[Morgenzeitung Neu] Feedback ';
  const MARKER='MORGENZEITUNG_NEU_FEEDBACK_V1\n';
  const VALID=['','Sehr relevant','Teilweise relevant','Nicht relevant'];
  const CODES=['topic_dislike','too_shallow','already_known','too_niche','one_sided','more_of_this'];
  const codes=r=>Array.isArray(r.reason_codes)?[...new Set(r.reason_codes.filter(c=>CODES.includes(c)))].sort():[];
  const suggested=r=>Array.isArray(r?.suggested_reasons)?[...new Set(r.suggested_reasons.filter(x=>typeof x==='string'&&x.length>0&&x.length<=120))].slice(0,5):[];
  // Mark only whole sentences actually clicked; ordinary typed text remains independent.
  const commentSuggestions=(items,comment)=>[...new Set((Array.isArray(items)?items:[])
    .filter(s=>typeof s==='string'&&s.length<=160&&s.length>0
      &&String(comment).split('\n').some(line=>line.trim()===s)))].slice(0,12);
  const sameRating=(a,b)=>!a&&!b||!!a&&!!b&&a.value===b.value&&a.reason===b.reason&&a.section===b.section&&JSON.stringify(codes(a))===JSON.stringify(codes(b))&&JSON.stringify(suggested(a))===JSON.stringify(suggested(b));
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
      if(!/^\d{4}-\d{2}-\d{2}$/.test(x.date)||issue.title!==PREFIX+x.date||
         !Array.isArray(x.ratings)||x.origin!=='website-explicit'||x.test===true)return null;
      const ratings=x.ratings.filter(r=>r&&/^[a-f0-9]{16}$/.test(r.id)&&VALID.includes(r.rating||'')).map(r=>({
        id:r.id,value:r.rating||'',reason:String(r.reason||'').slice(0,600),
        section:r.section==='Heute wichtig'?'Heute wichtig':'Vertiefungen',reason_codes:codes(r),suggested_reasons:suggested(r)
      }));
      const feedback=typeof x.comment==='string'?x.comment:'';
      return {date:x.date,ratings,feedback,comment_suggestions:commentSuggestions(x.comment_suggestions,feedback),
        number:issue.number,updated_at:issue.updated_at||''};
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
  const COMPARISON_NOTE=/^\[V3-Vergleich (\d{4}-\d{2}-\d{2} [a-zA-Z0-9_-]{1,90}): (?:published|alternative|equal)\]$/;
  function preserveComparisonNotes(previous,incoming){
    // An old comparison remains valid even when that optional UI is absent
    // later. Explicitly selected answers replace only the same pair.
    const text=String(incoming||'').trim(), base=String(previous||'').trim();
    const chosen=new Set();
    for(const line of text.split('\n')){
      const match=line.trim().match(COMPARISON_NOTE);
      if(match)chosen.add(match[1]);
    }
    const missing=base.split('\n').filter(line=>{
      const match=line.trim().match(COMPARISON_NOTE);
      return match&&!chosen.has(match[1]);
    });
    // Deduplicate old notes and preserve the reader's authored text unchanged.
    return [text,...new Set(missing)].filter(Boolean).join('\n').trim();
  }
  function mergeComparisonOnly(previous,incoming){
    // A rating/comment save may submit ONLY the optional comparison votes.
    // Preserve all prose written earlier, including newer prose from another
    // device that this browser never saw.
    const lines=String(incoming||'').trim().split('\n').filter(Boolean);
    const chosen=new Map();
    for(const line of lines){
      const m=line.match(COMPARISON_NOTE);
      if(!m)throw Error('Ungültige Vergleichsrückmeldung.');
      chosen.set(m[1],line);
    }
    const saved=String(previous||'').split('\n').filter(line=>{
      const m=line.trim().match(COMPARISON_NOTE);
      return !m||!chosen.has(m[1]);
    });
    return [...saved,...chosen.values()].join('\n').trim();
  }
  function appendOnce(previous,fragment){
    const base=String(previous||'').trim(), fresh=String(fragment||'').trim();
    if(!fresh)return base;
    // A retry after a saved but unacknowledged write is idempotent.
    const at=base.indexOf(fresh);
    if(at>=0&&(at===0||base.slice(at-2,at)==='\n\n')&&
       (at+fresh.length===base.length||base.slice(at+fresh.length,at+fresh.length+2)==='\n\n'))
      return base;
    return [base,fresh].filter(Boolean).join('\n\n');
  }
  async function submit(date,ratings,feedback,token,store=localStorage,transport=fetch,options={}){
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Array.isArray(ratings)||
       ratings.length>100||typeof feedback!=='string'||feedback.length>4000)
      throw Error('Ungültige Feedbackdaten');
    const intended=new Map();
    for(const r of ratings){
      if(!r||typeof r.id!=='string'||!/^[a-f0-9]{16}$/.test(r.id)||
         !VALID.includes(r.value||'')||typeof r.reason!=='string'||r.reason.length>600)
        throw Error('Ungültige Artikelbewertung');
      intended.set(r.id,{id:r.id,value:r.value||'',reason:r.reason,
                         section:r.section==='Heute wichtig'?'Heute wichtig':'Vertiefungen',reason_codes:codes(r),suggested_reasons:suggested(r)});
    }
    const comment=feedback.trim();
    const appendText=options?.appendComment===undefined?'':String(options.appendComment).trim();
    if(appendText.length>4000||appendText&&comment||
       options.comparisonOnly&&appendText)
      throw Error('Kommentar bitte entweder anhängen oder ausdrücklich ersetzen.');
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
      for(const [id,row] of intended){
        if(options.baselineRatings&&Object.hasOwn(options.baselineRatings,id)&&
           !sameRating(byId.get(id),options.baselineRatings[id])&&!sameRating(byId.get(id),row))
          throw Error('Diese Artikelbewertung wurde auf einem anderen Gerät geändert. Bitte den aktuellen Stand neu laden und deine Änderung erneut auswählen.');
        byId.set(id,row);
      }
      const mergedComment=appendText?appendOnce(base?.feedback,appendText):
        options.comparisonOnly?mergeComparisonOnly(base?.feedback,comment):
        comment?preserveComparisonNotes(base?.feedback,comment):(base?.feedback||'');
      if(mergedComment.length>4000)throw Error('Der gespeicherte Kommentar überschreitet 4000 Zeichen. Bitte kürzen.');
      if(!byId.size&&!mergedComment)throw Error('Bitte mindestens eine Bewertung oder Feedback eingeben.');
      const freshPhraseSource=appendText||comment;
      const newSuggestions=(appendText&&mergedComment===(base?.feedback||''))||options.comparisonOnly
        ?[]:commentSuggestions(options.commentSuggestions,freshPhraseSource);
      const tagged=commentSuggestions([...(base?.comment_suggestions||[]),...newSuggestions],mergedComment);
      const title=PREFIX+date;
      const payload={version:1,date,
        ratings:[...byId.values()].map(r=>({id:r.id,section:r.section,rating:r.value,reason:r.reason,...(codes(r).length?{reason_codes:codes(r)}:{}),...(suggested(r).length?{suggested_reasons:suggested(r)}:{})})),
        comment:mergedComment,...(tagged.length?{comment_suggestions:tagged}:{}),origin:'website-explicit'};
      const body=MARKER+JSON.stringify(payload,null,2);
      if(record?.body===body)return {ok:true,existing:true,html_url:record.html_url,
        feedback:mergedComment,comment_suggestions:tagged};
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
        found.has(id)&&sameRating(found.get(id),row));
      if(preserved&&verified.feedback===mergedComment&&
         JSON.stringify(verified.comment_suggestions)===JSON.stringify(tagged))
        return {ok:true,updated:!!existing,html_url:result.html_url,
          feedback:verified.feedback,comment_suggestions:verified.comment_suggestions};
      // A competing edit has won at least one write; merge it on the next read.
      previousIssue=verified;
    }
    throw Error('Gleichzeitige Änderungen konnten nicht sicher zusammengeführt werden. Bitte erneut speichern.');
  }
  async function appendComment(date,text,token,store=localStorage,transport=fetch,options={}){
    return submit(date,[],'',token,store,transport,
      {appendComment:text,commentSuggestions:options.commentSuggestions||[]});
  }
  return {REPO,TOKEN_KEY,RECEIPTS_KEY,readToken,clearToken,saveToken,verify,feedbackHistory,readReceipts,savedFeedback,submit,appendComment,preserveComparisonNotes};
})();
if(typeof module!=='undefined')module.exports=DirectFeedback;
