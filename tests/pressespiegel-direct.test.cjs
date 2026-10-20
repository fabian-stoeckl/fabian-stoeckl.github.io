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
let calls=[],fail=false,privateRepo=true, number=42,remoteBody='';
const transport=async(url,opts)=>{
  assert(url.startsWith('https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback'));
  assert.equal(opts.headers.Authorization,'Bearer github_pat_TESTTOKEN_example_123456789');
  assert.equal(opts.credentials,'omit');
  assert.equal(opts.redirect,'error');
  assert.equal(opts.headers['X-GitHub-Api-Version'],undefined); // Browser CORS preflight compatibility.
  calls.push({url,opts});
  if(fail)return {ok:false,status:500,json:async()=>({})};
  if(opts.method==='GET'){
    if(url.endsWith('/issues/'+number))return {ok:true,json:async()=>({number,body:remoteBody})};
    return {ok:true,json:async()=>({full_name:feedback.REPO,private:privateRepo})};
  }
  remoteBody=JSON.parse(opts.body).body;
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
const news={id:'b'.repeat(16),value:'Teilweise relevant',reason:'Wichtig für Überblick'};
result=await feedback.submit('2026-10-20',[news],'',token,s,transport,webcrypto);
assert.equal(result.updated,true);
assert.match(remoteBody,/Mehr Zahlen/);
assert.match(remoteBody,/Wichtig für Überblick/);
assert.match(remoteBody,/Mehr Handelsblatt und KI/);
assert.equal((remoteBody.match(/Artikel-ID:/g)||[]).length,2);
assert.equal(calls.filter(x=>x.opts.method==='PATCH').length,2);
assert(calls.find(x=>x.opts.method==='PATCH').url.endsWith('/issues/42'));
fail=true;
await assert.rejects(()=>feedback.submit('2026-10-20',data,'Andere Themen',token,s,transport,webcrypto),/nicht speichern/);
assert.equal(feedback.readReceipts(s)['2026-10-20'].number,42);
feedback.clearToken(s);assert.equal(feedback.readToken(s),'');
console.log('Direct-feedback token, private repository, create/update/no duplicate/error handling tests passed.');
})().catch(e=>{console.error(e);process.exit(1)});
