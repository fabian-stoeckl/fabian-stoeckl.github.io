/* One-time or recurring read-only post-deployment smoke test.
 * No personal access token; no feedback issue writes; no personal user data.
 */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root='https://www.fabian-stoeckl.com/Privat/Pressespiegel/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function get(url) {
  const response=await fetch(url,{redirect:'follow',signal:AbortSignal.timeout(15000),cache:'no-store',
    headers:{'User-Agent':'Morgenzeitung-Public-Smoke-Test/1.0'}});
  assert.equal(response.status,200,url+' returned '+response.status);
  return response.text();
}
async function eventual(url,test,label) {
  let last;
  for(let n=1;n<=6;n++){
    try{
      const content=await get(url);
      test(content);
      console.log('PASS '+label+' on attempt '+n);
      return;
    }catch(e){
      last=e;
      console.log('RETRY '+label+' attempt '+n+': '+e.message);
      if(n<6)await sleep(10000);
    }
  }
  throw Error(label+' failed after 6 attempts: '+last.message);
}
(async()=>{
 await eventual(root,html=>{
   assert.match(html,/id="tab-headlines"/);
   assert.match(html,/id="tab-articles"/);
   assert.match(html,/>Heute wichtig/);
   assert.match(html,/>Vertiefungen/);
   assert(!html.includes('id="overview"'),'Obsolete highlighted overview still deployed');
   assert(!html.includes('Ein klarer Blick auf Wirtschaft'),'Obsolete promotional subtitle still deployed');
   assert.match(html,/direct-feedback\.js/);
   assert.match(html,/github-setup/);
 },'Live HTML sections');
 await eventual(root+'direct-feedback.js',js=>{
   assert.match(js,/https:\/\/api\.github\.com\/repos/);
   assert.match(js,/\/issues/);
   assert.match(js,/localStorage/);
   assert(!js.includes('X-GitHub-Api-Version'),'Old CORS-sensitive header deployed');
 },'Live direct feedback script');
 await eventual(root+'config.json',contents=>{
   const cfg=JSON.parse(contents);
   assert.equal(cfg.mode,'github');
   assert.equal(cfg.feedback_repository,'fabian-stoeckl/morgenzeitung-feedback');
   assert.equal(cfg.api,null);
 },'Live config');
 await eventual(root+'data/index.json',contents=>{
   const data=JSON.parse(contents);
   assert(Array.isArray(data.dates) && data.dates.length>0);
 },'Live edition index');
 // Confirm the public daily JSON is EXACTLY the committed edition, not merely
 // the same article IDs or a stale previous deployment.
 const expectedIndex=JSON.parse(fs.readFileSync(path.join(__dirname,'../Privat/Pressespiegel/data/index.json'),'utf8'));
 const latest=expectedIndex.dates[0];
 const expectedEdition=JSON.parse(fs.readFileSync(path.join(__dirname,'../Privat/Pressespiegel/data',latest+'.json'),'utf8'));
 await eventual(root+'data/'+latest+'.json',contents=>{
   const actual=JSON.parse(contents);
   assert.deepEqual(actual,expectedEdition,'Live HTTPS edition differs from committed '+latest);
   assert.equal(actual.date,latest);
   assert.equal(actual.preview,false);
   assert.equal(actual.articles.length,expectedEdition.articles.length);
   assert.equal(actual.headlines.length,expectedEdition.headlines.length);
 },'Live latest edition exact JSON parity');
 // This test deliberately DOES NOT validate authenticated GitHub POST from user's browser.
 console.log('PUBLIC WEBSITE SMOKE TEST PASSED – authenticated personal browser submission remains untested.');
})().catch(e=>{console.error('PUBLIC WEBSITE SMOKE TEST FAILED:',e.message);process.exitCode=1});
