'use strict';
const assert=require('node:assert/strict');
const Feedback=require('../Privat/Morgenzeitung-Neu/direct-feedback.js');
const PREFIX='MORGENZEITUNG_NEU_FEEDBACK_V1\n';
const SAMPLE='Mehr analytische Tiefe: Bitte Mechanismen und Folgen erklären.';
const storage={read:{},getItem(k){return this.read[k]||null;},setItem(k,v){this.read[k]=v;}};
let issue;
async function transport(url,opt={}){
  const path=new URL(url).pathname,method=opt.method||'GET';
  const response=(value,status=200)=>({ok:status>=200&&status<300,status,json:async()=>value});
  if(path.endsWith('/issues')&&method==='GET')return response(issue?[issue]:[]);
  if(/\/issues\/\d+$/.test(path)&&method==='GET')return issue?response(issue):response({},404);
  if((path.endsWith('/issues')&&method==='POST')||
     (/\/issues\/\d+$/.test(path)&&method==='PATCH')){
    const payload=JSON.parse(opt.body);
    issue={...payload,number:31,html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/31',
      updated_at:new Date().toISOString()};
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
  console.log('PASS: prompted vs independently authored feedback, edits, private persistence, append safeguards');
})().catch(e=>{console.error(e);process.exitCode=1;});
