'use strict';
const assert=require('node:assert/strict');
const DirectFeedback=require('../Privat/Morgenzeitung-neu/direct-feedback.js');
const issues=[
 {number:9,title:'[Morgenzeitung] Sammelbewertung 2026-10-27',body:'old-paper-feedback',updated_at:'2026-10-27T12:00:00Z'}
];
const store={data:new Map(),getItem(k){return this.data.get(k)||null;},setItem(k,v){this.data.set(k,v);},removeItem(k){this.data.delete(k);}};
function response(data){return {ok:true,json:async()=>JSON.parse(JSON.stringify(data))};}
const transport=async (url,opts)=>{
 const u=new URL(url),path=u.pathname.split('/').slice(-1)[0],body=opts.body?JSON.parse(opts.body):null;
 if(u.pathname.endsWith('/morgenzeitung-feedback'))return response({full_name:DirectFeedback.REPO,private:true});
 if(opts.method==='GET'&&u.pathname.endsWith('/issues'))return response(issues);
 if(opts.method==='GET'&&u.pathname.includes('/issues/')){
  const found=issues.find(i=>i.number===Number(path));return response(found);
 }
 if(opts.method==='POST'&&u.pathname.endsWith('/issues')){
  const created={...body,number:10,updated_at:'2026-10-28T09:00:00Z',html_url:'https://github.com/'+DirectFeedback.REPO+'/issues/10'};
  issues.unshift(created);return response(created);
 }
 if(opts.method==='PATCH'&&u.pathname.endsWith('/issues/10')){
  const target=issues.find(i=>i.number===10);
  Object.assign(target,body,{updated_at:'2026-10-28T09:02:00Z'});
  return response(target);
 }
 throw Error('Unexpected API call '+opts.method+' '+url);
};
(async()=>{
 assert.equal(await DirectFeedback.verify('token',transport),true);
 const date='2026-10-28',a='a'.repeat(16),b='b'.repeat(16);
 await DirectFeedback.submit(date,[{id:a,value:'Sehr relevant',reason:'Tiefe Einordnung',section:'Vertiefungen'}],'', 'token',store,transport);
 let history=await DirectFeedback.feedbackHistory('token',transport);
 assert.equal(history.length,1,'old-paper feedback never mixed');
 assert.equal(history[0].ratings[0].reason,'Tiefe Einordnung');
 assert.ok(issues[0].body.startsWith('MORGENZEITUNG_NEU_FEEDBACK_V1\\n'.replace('\\n','\n')));
 await DirectFeedback.submit(date,[{id:b,value:'Nicht relevant',reason:'Zu randständig',section:'Heute wichtig'}],'Mehr produktive Themen','token',store,transport);
 history=await DirectFeedback.feedbackHistory('token',transport);
 assert.equal(issues.length,2,'same issue updated not duplicated');
 assert.equal(history[0].ratings.length,2,'previous rating retained');
 assert.equal(history[0].feedback,'Mehr produktive Themen');
 assert.equal(history[0].ratings.find(x=>x.id===a).value,'Sehr relevant');
 assert.equal(history[0].ratings.find(x=>x.id===b).value,'Nicht relevant');
 console.log('PASS: feedback isolation, real data shape, merge, updated rating, comments');
})().catch(e=>{console.error(e);process.exitCode=1;});
