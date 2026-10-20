import assert from 'node:assert/strict';
import worker, {validate, fingerprint} from './worker.mjs';

const data = {date:'2026-10-19',ratings:[{id:'a'.repeat(16),value:'Sehr relevant',reason:'Handelsblatt'}],feedback:'Mehr Produktivität'};
assert.equal(validate(data),data);
for (const bad of [
  {...data,date:'2026-02-30'},
  {...data,feedback:'x'.repeat(4001)},
  {...data,ratings:data.ratings.concat(data.ratings)},
  {...data,ratings:[{...data.ratings[0],id:'INVALID'}]},
  {...data,feedback:'',ratings:[]}
]) assert.throws(()=>validate(bad));
const fp=await fingerprint(data);
assert.match(fp,/^[a-f0-9]{64}$/);

let privateRepo=true, list=[], searchItems=[], created=[];
globalThis.fetch=async(url, opts)=> {
  assert.equal(opts.headers.Authorization,'Bearer private-token');
  if(url.endsWith('/repos/fabian-stoeckl/morgenzeitung-feedback')) {
    return Response.json({private:privateRepo,full_name:'fabian-stoeckl/morgenzeitung-feedback'});
  }
  if(url.includes('/search/issues?')) return Response.json({items:searchItems});
  if(url.includes('/issues?')) return Response.json(list);
  if(url.endsWith('/issues') && opts.method==='POST') {
    const item=JSON.parse(opts.body);
    created.push(item);
    list=[{...item,created_at:new Date().toISOString()}];
    return Response.json({number:created.length});
  }
  throw Error('Unexpected GitHub API '+url);
};
const request=(origin='https://www.fabian-stoeckl.com')=>new Request('https://relay.example/feedback',{
  method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(data)
});
const env={GITHUB_FEEDBACK_TOKEN:'private-token'};
let response=await worker.fetch(request(),env);
assert.equal(response.status,200);
assert.deepEqual(await response.json(),{ok:true,existing:false});
assert.match(created[0].body,/Identität nicht verifiziert/);
assert.match(created[0].body,/BEGIN_STRUCTURED_FEEDBACK/);
assert.ok(!created[0].body.includes('private-token'));

response=await worker.fetch(request(),env);
assert.deepEqual(await response.json(),{ok:true,existing:true});
assert.equal(created.length,1);

response=await worker.fetch(request('https://other.example'),env);
assert.equal(response.status,403);
assert.equal(response.headers.get('Access-Control-Allow-Origin'),null);

response=await worker.fetch(request(),{});
assert.equal(response.status,503);

privateRepo=false;
response=await worker.fetch(request(),env);
assert.equal(response.status,502);
privateRepo=true;

list=Array.from({length:100},(_,i)=>({
  title:'[Morgenzeitung] Feedback other '+i,
  created_at:new Date().toISOString()
}));
response=await worker.fetch(request(),env);
assert.equal(response.status,429);
assert.equal(created.length,1);

list=[];
searchItems=[{title:created[0].title}];
response=await worker.fetch(request(),env);
assert.deepEqual(await response.json(),{ok:true,existing:true});
assert.equal(created.length,1);

console.log('Cloudflare relay validation, write-only private GitHub, retry, caps, origin, error cases passed.');
