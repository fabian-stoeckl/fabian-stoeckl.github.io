'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const base='Privat/Morgenzeitung-neu/';
const html=fs.readFileSync(base+'index.html','utf8');
const prefs=fs.readFileSync(base+'praeferenzen.html','utf8');
const bridge=fs.readFileSync(base+'direct-feedback.js','utf8');
const old=fs.readFileSync('Privat/Pressespiegel/index.html','utf8');
const homepage=fs.readFileSync('Privat/index.html','utf8');
assert.ok(homepage.includes('href="./Morgenzeitung-neu/"'));
assert.equal(homepage.split('href="./Morgenzeitung-neu/"').length-1,1,'Only one tile');
assert.ok(!homepage.includes('href="./Pressespiegel-neu/"'));
for(const id of ['date','headlines','articles','feedback-section','github-setup','tab-headlines','tab-articles','profile-toggle']){
 assert.ok(html.includes('id="'+id+'"'),'Missing identical old reader element '+id);
 assert.ok(old.includes('id="'+id+'"'),'Missing old reader element '+id);
}
assert.ok(html.includes('href="../Pressespiegel/style.css'));
assert.ok(html.includes('src="../Pressespiegel/app.js'));
assert.ok(html.includes('src="./direct-feedback.js"'));
assert.ok(prefs.includes('src="../Pressespiegel/preferences.js'));
assert.ok(bridge.includes('MORGENZEITUNG_NEU_FEEDBACK_V1'));
assert.ok(bridge.includes('[Morgenzeitung neu] Feedback '));
assert.ok(bridge.includes('github-token:v1'));
assert.ok(!bridge.includes('HEAD')&&!bridge.includes('Linktest'));
execFileSync(process.execPath,['--check',base+'direct-feedback.js']);
for(const d of JSON.parse(fs.readFileSync(base+'data/index.json','utf8')).dates){
 const e=JSON.parse(fs.readFileSync(base+'data/'+d+'.json','utf8'));
 assert.equal(e.date,d);
 assert.ok(e.articles.length>=10&&e.articles.length<=15);
 assert.ok(e.headlines.length>=15&&e.headlines.length<=20);
 assert.ok(e.researched_at&&!Number.isNaN(new Date(e.researched_at).valueOf()));
 assert.ok(e.available_at&&!Number.isNaN(new Date(e.available_at).valueOf()));
 assert.equal(typeof e.preview,'boolean');
 const ids=new Set(),urls=new Set();
 for(const [section,items] of [['articles',e.articles],['headlines',e.headlines]]){
  for(const a of items){
   assert.match(a.id,/^[a-f0-9]{16}$/);
   assert.ok(a.title&&a.url&&a.summary&&a.source&&a.published_at);
   assert.ok(new URL(a.url).protocol==='https:'); // syntax only; NO HTTP URL checks
   assert.ok(!ids.has(a.id)&&!urls.has(a.url));
   if(section==='headlines')assert.ok(['Österreich','International'].includes(a.region));
   if(section==='articles')assert.ok(a.topic);
   ids.add(a.id);urls.add(a.url);
  }
 }
}
console.log('PASS: identical shared UI, isolated feedback, edition schema, no HTTP article tests');
