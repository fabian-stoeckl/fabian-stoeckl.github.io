'use strict';
const assert=require('node:assert/strict');
const D=require('../Privat/Morgenzeitung-3/direct-feedback.js');
const issues=[{number:1,title:'[Morgenzeitung neu] Feedback 2026-10-27',body:'MORGENZEITUNG_NEU_FEEDBACK_V1\n{}'}];
const store={map:new Map(),getItem(k){return this.map.get(k)||null},setItem(k,v){this.map.set(k,v)},removeItem(k){this.map.delete(k)}};
const response=x=>({ok:true,json:async()=>JSON.parse(JSON.stringify(x))});
async function transport(url,options){
 const u=new URL(url),body=options.body?JSON.parse(options.body):null;
 if(u.pathname.endsWith('/morgenzeitung-feedback'))return response({full_name:D.REPO,private:true});
 if(options.method==='GET'&&u.pathname.endsWith('/issues'))return response(issues);
 if(options.method==='GET'&&u.pathname.includes('/issues/'))return response(issues.find(x=>x.number===Number(u.pathname.split('/').at(-1))));
 if(options.method==='POST'&&u.pathname.endsWith('/issues')){
  const created={...body,number:2,updated_at:'2026-10-28T09:00:00Z',html_url:'https://github.com/'+D.REPO+'/issues/2'};
  issues.unshift(created);return response(created);
 }
 if(options.method==='PATCH'&&u.pathname.endsWith('/issues/2')){
  const x=issues[0];Object.assign(x,body,{updated_at:'2026-10-28T09:10:00Z'});return response(x);
 }
 throw Error('unexpected call');
}
(async()=>{
 assert.equal(await D.verify('token',transport),true);
 const date='2026-10-28',a='a'.repeat(16),b='b'.repeat(16);
 await D.submit(date,[{id:a,value:'Sehr relevant',reason:'Spannend',section:'Vertiefungen'}],'','token',store,transport);
 assert.equal(issues.length,2);assert.ok(issues[0].body.startsWith('MORGENZEITUNG_V3_FEEDBACK_V1\n'));
 await D.submit(date,[{id:b,value:'Nicht relevant',reason:'Schon bekannt',section:'Heute wichtig'}],'Mehr Vielfalt','token',store,transport);
 const history=await D.feedbackHistory('token',transport);
 assert.equal(history.length,1);assert.equal(history[0].ratings.length,2);
 assert.equal(history[0].feedback,'Mehr Vielfalt');assert.equal(issues.length,2);
 store.setItem(D.TOKEN_KEY,'existing-restricted-token');
 assert.equal(D.resetOldTokenOnce(store),false);
 assert.equal(store.getItem(D.TOKEN_KEY),'existing-restricted-token','V3 must not wipe an existing private reader token');
 // A stale issues-list response must never erase a newer rating saved elsewhere.
 const stale=JSON.parse(JSON.stringify(issues[0]));
 const data=JSON.parse(stale.body.slice('MORGENZEITUNG_V3_FEEDBACK_V1\n'.length));
 data.ratings=data.ratings.slice(0,1);
 stale.body='MORGENZEITUNG_V3_FEEDBACK_V1\n'+JSON.stringify(data);
 const staleList=async(url,opts)=>{
   if((opts.method||'GET')==='GET'&&String(url).includes('/issues?'))return response([stale,issues[1]]);
   return transport(url,opts);
 };
 await D.submit(date,[{id:'c'.repeat(16),value:'Sehr relevant',reason:'Frische Bewertung',section:'Vertiefungen'}],
   '', 'token',store,staleList);
 const consolidated=await D.feedbackHistory('token',transport);
 assert.equal(consolidated[0].ratings.length,3,'Fresh issue body must preserve ratings added on another device');
 assert.equal(consolidated[0].ratings.find(x=>x.id===b).value,'Nicht relevant');
 assert.equal(D.TOKEN_KEY,'morgenzeitung:github-token:v1');
 assert.equal(D.RECEIPTS_KEY,'morgenzeitung-v3:github-receipts:v1');
 // Additional same-day V3 learning edition must not replace prior feedback.
 const fs=require('node:fs');
 const regular=JSON.parse(fs.readFileSync('Privat/Morgenzeitung-3/data/2026-10-28.json','utf8'));
 const extra=JSON.parse(fs.readFileSync('Privat/Morgenzeitung-3/lern-ausgabe-2026-10-28/data/2026-10-28.json','utf8'));
 const earlierIds=new Set([...regular.articles,...regular.headlines].map(r=>r.id));
 const extraIds=[...extra.articles,...extra.headlines].map(r=>r.id);
 assert.equal(extra.date,regular.date);
 assert.equal(extra.articles.length,12);
 assert.equal(extra.headlines.length,6);
 assert.equal(new Set(extraIds).size,extraIds.length);
 assert.ok(extraIds.every(id=>/^[a-f0-9]{16}$/.test(id)&&!earlierIds.has(id)));
 await D.submit(date,[{id:extra.articles[0].id,value:'Sehr relevant',reason:'Echte Zusatzbewertung',section:'Vertiefungen'}],
  '', 'token',store,transport);
 const sameDay=await D.feedbackHistory('token',transport);
 assert.equal(sameDay.length,1);
 assert.equal(sameDay[0].ratings.length,4);
 assert.equal(sameDay[0].ratings.find(r=>r.id===b).value,'Nicht relevant');
 assert.equal(sameDay[0].ratings.find(r=>r.id===extra.articles[0].id).value,'Sehr relevant');
 console.log('PASS: V3 feedback isolated, issue updated, old/v2 filtered');
})().catch(e=>{console.error(e);process.exitCode=1});
