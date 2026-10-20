const assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto');
globalThis.GitHubPaper=require('../Privat/Pressespiegel/github.js');
const feedback=require('../Privat/Pressespiegel/direct-feedback.js');
function store(){let m=new Map();return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v),removeItem:k=>m.delete(k)};}
(async()=>{
const s=store();
assert.equal(feedback.readToken(s),'');
assert.throws(()=>feedback.saveToken('bad',s));
assert.equal(feedback.saveToken('github_pat_TESTTOKEN_example_123456789',s),'github_pat_TESTTOKEN_example_123456789');
assert.match(feedback.readToken(s),/^github_pat_/);
const a='a'.repeat(16);
const data=[{id:a,value:'Sehr relevant',reason:'Mehr Zahlen'}];
assert.match(feedback.buildFeedback('2026-10-20',data,'Mehr Handelsblatt').body,/Mehr Handelsblatt/);
assert.throws(()=>feedback.buildFeedback('no',data,''));
assert.throws(()=>feedback.buildFeedback('2026-10-20',[],''),/Bitte/);
let calls=[],fail=false,privateRepo=true, number=42, issueBody=null;
const transport=async(url,opts)=>{
  assert(url.startsWith('https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback'));
  assert.equal(opts.headers.Authorization,'Bearer github_pat_TESTTOKEN_example_123456789');
  assert.equal(opts.credentials,'omit');
  assert.equal(opts.redirect,'error');
  assert.equal(opts.headers['X-GitHub-Api-Version'],undefined); // Browser CORS preflight compatibility.
  calls.push({url,opts});
  if(fail)return {ok:false,status:500,json:async()=>({})};
  if(opts.method==='GET'&&url.endsWith('/issues/'+number))return {ok:true,json:async()=>({body:issueBody,number})};
  if(opts.method==='GET')return {ok:true,json:async()=>({full_name:feedback.REPO,private:privateRepo})};
  issueBody=JSON.parse(opts.body).body;
  return {ok:true,json:async()=>({number,html_url:'https://github.com/'+feedback.REPO+'/issues/'+number})};
};
const token=feedback.readToken(s);
await feedback.verify(token,transport);
privateRepo=false;await assert.rejects(()=>feedback.verify(token,transport),/private/);
privateRepo=true;
let result=await feedback.submit('2026-10-20',data,'Mehr Handelsblatt',token,s,transport,webcrypto);
assert.equal(result.ok,true);assert.equal(result.updated,undefined);
assert.equal(calls.filter(x=>x.opts.method==='POST').length,1);
result=await feedback.submit('2026-10-20',data,'Mehr Handelsblatt',token,s,transport,webcrypto);
assert.equal(result.existing,true);assert.equal(calls.filter(x=>x.opts.method==='POST').length,1);
result=await feedback.submit('2026-10-20',data,'Mehr Handelsblatt und KI',token,s,transport,webcrypto);
assert.equal(result.updated,true);
assert.equal(calls.filter(x=>x.opts.method==='PATCH').length,1);
assert(calls.find(x=>x.opts.method==='PATCH').url.endsWith('/issues/42'));
const headline={id:'b'.repeat(16),value:'Nicht relevant',reason:'Zu redundant',section:'Heute wichtig'};
result=await feedback.submit('2026-10-20',[headline],'',token,s,transport,webcrypto);
assert.equal(result.updated,true);
assert.match(issueBody,/Artikel-ID: aaaaaaaaaaaaaaaa/);
assert.match(issueBody,/Bereich: Heute wichtig\nArtikel-ID: bbbbbbbbbbbbbbbb/);
assert.match(issueBody,/Mehr Handelsblatt und KI/); // old free text was not dropped
const saved=await feedback.savedFeedback('2026-10-20',token,s,transport);
assert.equal(saved.ratings.length,2);
assert(saved.ratings.some(r=>r.id==='b'.repeat(16)&&r.section==='Heute wichtig'));
assert.equal(saved.feedback,'Mehr Handelsblatt und KI');
const forty=Array.from({length:35},(_,i)=>({id:i.toString(16).padStart(16,'0'),value:'Sehr relevant',reason:'',section:'Heute wichtig'}));
assert.equal(feedback.buildFeedback('2026-10-20',forty,'').title,'[Morgenzeitung] Sammelbewertung 2026-10-20');

fail=true;
await assert.rejects(()=>feedback.submit('2026-10-20',data,'Andere Themen',token,s,transport,webcrypto),/nicht speichern/);
assert.equal(feedback.readReceipts(s)['2026-10-20'].number,42);
feedback.clearToken(s);assert.equal(feedback.readToken(s),'');
console.log('Direct-feedback token, private repository, create/update/no duplicate/error handling tests passed.');
})().catch(e=>{console.error(e);process.exit(1)});
