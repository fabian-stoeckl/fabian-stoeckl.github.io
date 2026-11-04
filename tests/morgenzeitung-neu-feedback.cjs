'use strict';
const assert=require('node:assert/strict');
const Feedback=require('../Privat/Pressespiegel/direct-feedback.js');
const PREFIX='MORGENZEITUNG_NEU_FEEDBACK_V1\n';
const SAMPLE='Mehr analytische Tiefe: Bitte Mechanismen und Folgen erklären.';
const storage={read:{},getItem(k){return this.read[k]||null;},setItem(k,v){this.read[k]=v;}};
let issue, duplicateIssue=null,injectPostDuplicate=false;
async function transport(url,opt={}){
  const path=new URL(url).pathname,method=opt.method||'GET';
  const response=(value,status=200)=>({ok:status>=200&&status<300,status,json:async()=>value});
  if(path.endsWith('/issues')&&method==='GET')return response([...(issue?[issue]:[]),...(duplicateIssue?[duplicateIssue]:[])]);
  if(/\/issues\/\d+$/.test(path)&&method==='GET')return issue?response(issue):response({},404);
  if((path.endsWith('/issues')&&method==='POST')||
     (/\/issues\/\d+$/.test(path)&&method==='PATCH')){
    const payload=JSON.parse(opt.body);
    issue={...payload,number:31,html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/31',
      updated_at:new Date().toISOString()};
    if(injectPostDuplicate&&method==='POST'){
      duplicateIssue={...issue,number:32,html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/32'};
      injectPostDuplicate=false;
    }
    return response(issue);
  }
  throw Error('Unexpected API path '+method+' '+path);
}
(async()=>{
  let result=await Feedback.appendComment('2026-10-29',SAMPLE+'\nMein eigener, konkreter Wunsch.',
    'token',storage,transport,{commentSuggestions:[SAMPLE]});
  assert.ok(result.ok);
  let payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.deepEqual(payload.comment_suggestions,[SAMPLE]);
  assert.equal(payload.comment.includes('Mein eigener, konkreter Wunsch.'),true);
  const parsed=Feedback.feedbackHistory('token',transport);
  assert.deepEqual((await parsed)[0].comment_suggestions,[SAMPLE]);
  result=await Feedback.submit('2026-10-29',[],'Ich möchte mehr Interviews.\n'+SAMPLE,
    'token',storage,transport,{commentSuggestions:[]});
  assert.ok(result.ok);
  payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.deepEqual(payload.comment_suggestions,[SAMPLE],
    'An already established prompted line must survive an unrelated edit');
  await Feedback.submit('2026-10-29',[],'Ich möchte mehr Interviews.',
    'token',storage,transport,{commentSuggestions:[]});
  payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.ok(!('comment_suggestions' in payload),'Removing the prompted line removes provenance');
  await Feedback.submit('2026-10-29',[],'Ich möchte mehr Interviews.\n'+SAMPLE,
    'token',storage,transport,{commentSuggestions:[]});
  payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.ok(!('comment_suggestions' in payload),'Typing the same phrase without clicking is not a prompted vote');
  await Feedback.appendComment('2026-10-29','Bisher noch nicht gesehen.', 'token',storage,transport,
    {commentSuggestions:[SAMPLE]});
  payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.ok(!('comment_suggestions' in payload),'Cannot tag a phrase not present in appended comment');
  // A rating and its free-text reason are one article vote, not two.
  const row={id:'1234567890abcdef',section:'Vertiefungen',value:'Sehr relevant',
    reason:'Erklärt die wirtschaftlichen Folgen gut.',reason_codes:['more_of_this'],
    suggested_reasons:['Zu juristisch für ein Randthema']};
  let previous=payload.comment;
  await Feedback.submit('2026-10-29',[row],'Meine eigene allgemeine Rückmeldung.',
    'token',storage,transport,{replaceComment:true,baselineComment:previous});
  payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.equal(payload.ratings.length,1);
  assert.equal(payload.ratings[0].reason,row.reason);
  assert.deepEqual(payload.ratings[0].reason_codes,['more_of_this']);
  assert.equal(payload.comment,'Meine eigene allgemeine Rückmeldung.');
  // Erasing a saved comment must not silently restore it.
  previous=payload.comment;
  await Feedback.submit('2026-10-29',[],'','token',storage,transport,
    {replaceComment:true,baselineComment:previous});
  payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.equal(payload.comment,'','Explicit empty edit removes saved general free text');
  assert.equal(payload.ratings.length,1,'Article rating and its free-text reason survive');
  assert.ok(!('comment_suggestions' in payload));
  // A rating-only save must NOT remove general prose from a different device.
  await Feedback.appendComment('2026-10-29','Auch gesellschaftliche Folgen beachten.',
    'token',storage,transport);
  previous=JSON.parse(issue.body.slice(PREFIX.length)).comment;
  const changed={...row,value:'Teilweise relevant',reason:'Mehr Daten wären hilfreich.'};
  await Feedback.submit('2026-10-29',[changed],'','token',storage,transport,
    {comparisonOnly:true});
  payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.equal(payload.comment,previous,'Rating-only edit keeps stored general feedback');
  assert.equal(payload.ratings.length,1);
  assert.equal(payload.ratings[0].reason,changed.reason);
  await assert.rejects(
    Feedback.submit('2026-10-29',[],'Veralteter Kommentar','token',storage,transport,
      {replaceComment:true,baselineComment:'Ein vorheriger anderer Text'}),
    /auf einem anderen Gerät geändert/,
    'Must not overwrite a newer comment from another device');
  // Qualitative article feedback without selecting a relevance level is valid,
  // but must not increase the count of selected relevance votes.
  const noteOnly={id:'abcdefabcdef1234',section:'Heute wichtig',value:'',
    reason:'Diese Nachricht ist schon bekannt; bitte mehr neue Entwicklung.',
    reason_codes:['already_known'],suggested_reasons:[]};
  await Feedback.submit('2026-10-29',[noteOnly],'','token',storage,transport,
    {comparisonOnly:true});
  payload=JSON.parse(issue.body.slice(PREFIX.length));
  assert.equal(payload.ratings.length,2,'Both existing rating and qualitative-only entry remain');
  assert.equal(payload.ratings.filter(x=>x.rating).length,1,
    'Only the entry with a selected relevance level is a relevance vote');
  assert.equal(payload.ratings.find(x=>x.id===noteOnly.id).reason,noteOnly.reason);
  const canonical=(await Feedback.feedbackHistory('token',transport))[0];
  assert.equal(canonical.ratings.find(x=>x.id===noteOnly.id).value,'');
  assert.equal(canonical.ratings.find(x=>x.id===noteOnly.id).reason,noteOnly.reason);
  // Multiple valid issues for one date must not silently discard another
  // device's comments/ratings, regardless of a local issue receipt.
  duplicateIssue={...issue,number:32,
    html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/32'};
  await assert.rejects(
    Feedback.savedFeedback('2026-10-29','token',storage,transport),
    /Mehrere gültige Feedback-Issues/,
    'A receipt from one device must not hide another valid same-date issue');
  await assert.rejects(
    Feedback.submit('2026-10-29',[changed],'','token',storage,transport,
      {comparisonOnly:true}),
    /Mehrere gültige Feedback-Issues/,
    'Do not overwrite a same-date duplicate until feedback is reconciled');
  duplicateIssue={...issue,number:issue.number};
  const deduped=await Feedback.feedbackHistory('token',transport);
  assert.equal(deduped.filter(x=>x.date==='2026-10-29').length,1,
    'A repeated page-row for the SAME issue number must not count as a second issue');
  duplicateIssue=null;
  // Race during a first POST: the second issue can appear after the initial
  // discovery check. Read back the full index before reporting success.
  injectPostDuplicate=true;
  await assert.rejects(
    Feedback.submit('2026-10-30',[row],'Neue Ausgabe.','token',storage,transport),
    /Mehrere gültige Feedback-Issues/,
    'First-time issue creation must detect a same-date second issue');
  duplicateIssue=null;
  // Bad original fields must block writes, not disappear from the reader
  // and then be silently lost on a later PATCH.
  const originalBody=issue.body;
  const makeBad=transform=>{
    const v=JSON.parse(originalBody.slice(PREFIX.length));
    transform(v);
    issue.body=PREFIX+JSON.stringify(v);
  };
  makeBad(v=>{v.ratings[0].section='Unbekannte Rubrik';});
  await assert.rejects(Feedback.feedbackHistory('token',transport),
    /nicht eindeutig lesbar.*Ungültige Artikelbewertung/,
    'Invalid source section must stop reading instead of being changed to Vertiefungen');
  await assert.rejects(Feedback.submit('2026-10-30',[row],'','token',storage,transport,{comparisonOnly:true}),
    /nicht eindeutig lesbar/,
    'Cannot overwrite a malformed canonical issue');
  makeBad(v=>{v.ratings.push({...v.ratings[0]});});
  await assert.rejects(Feedback.feedbackHistory('token',transport),/Doppelte Artikel-ID/,
    'Duplicate source article IDs must not collapse silently into one vote');
  makeBad(v=>{v.version=2;});
  await assert.rejects(Feedback.feedbackHistory('token',transport),/Ungültiges Format, Datum oder Version/);
  issue.body=originalBody;
  // Even manually renamed GitHub Issues must be reported, never silently
  // dropped from the dataset and overwritten by a newly created same-day issue.
  const originalTitle=issue.title;
  issue.title='[Pressespiegel] Feedback renumbered';
  await assert.rejects(Feedback.feedbackHistory('token',transport),
    /nicht eindeutig lesbar.*Ungültiges Format, Datum oder Version/,
    'Renamed valid feedback must fail closed, not be treated as nonexistent');
  await assert.rejects(Feedback.submit('2026-10-30',[row],'','token',storage,transport,{comparisonOnly:true}),
    /nicht eindeutig lesbar/,
    'Browser must not create a new issue when the original was renamed');
  issue.title=originalTitle;
  await assert.rejects(Feedback.submit('2026-10-30',[row,row],'','token',storage,transport),
    /doppelte Artikel-ID/,
    'Duplicate IDs in an outgoing draft must be rejected rather than overwritten');
  await assert.rejects(Feedback.submit('2026-10-30',[{...row,section:'Falsch'}],'','token',storage,transport),
    /Ungültige oder doppelte Artikel-ID/,
    'Outgoing drafts cannot silently change unknown sections into Vertiefungen');
  console.log('PASS: prompted vs independent feedback, malformed-issue fail-closed, duplicate protection and private persistence');
})().catch(e=>{console.error(e);process.exitCode=1;});
