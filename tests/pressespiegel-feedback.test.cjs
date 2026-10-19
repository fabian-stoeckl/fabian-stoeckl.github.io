const assert=require('node:assert/strict');const feedback=require('../Privat/Pressespiegel/feedback.js');
(async()=>{
await assert.rejects(()=>feedback.send(null,{}),/noch nicht verbunden/);
await assert.rejects(()=>feedback.send('http://example.org/feedback',{}),/Ungültige/);
let calls=0;global.fetch=async(url,opts)=>{calls++;assert.equal(opts.credentials,'omit');assert.equal(opts.headers.Authorization,undefined);return {ok:true,json:async()=>({ok:true,existing:false})};};
assert.equal((await feedback.send('https://example.org/feedback',{feedback:'test'})).ok,true);assert.equal(calls,1);
global.fetch=async()=>({ok:false,json:async()=>({error:'Nicht gespeichert'})});await assert.rejects(()=>feedback.send('https://example.org/feedback',{}),/Nicht gespeichert/);
global.fetch=async()=>{throw Error('offline')};await assert.rejects(()=>feedback.send('https://example.org/feedback',{}),/Keine Bestätigung/);
console.log('Anonymous client: no credentials, success/failure and missing endpoint passed.');
})().catch(e=>{console.error(e);process.exit(1)});
