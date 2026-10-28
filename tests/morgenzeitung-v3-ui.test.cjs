'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {execFileSync}=require('node:child_process');
const base='Privat/Morgenzeitung-3/';
const html=fs.readFileSync(base+'index.html','utf8'),home=fs.readFileSync('Privat/index.html','utf8');
const old=fs.readFileSync('Privat/Pressespiegel/index.html','utf8');
const pref=fs.readFileSync(base+'praeferenzen.html','utf8');
const js=fs.readFileSync(base+'direct-feedback.js','utf8');
assert.equal((home.match(/href="\.\/Morgenzeitung-3\/"/g)||[]).length,1);
for(const x of ['href="./Morgenzeitung-neu/"','href="./Pressespiegel/"'])assert.ok(home.includes(x));
for(const id of ['date','headlines','articles','feedback-section','github-setup','tab-headlines','tab-articles','profile-toggle']){
  assert.ok(html.includes('id="'+id+'"'));assert.ok(old.includes('id="'+id+'"'));
}
for(const src of ['../Pressespiegel/style.css','../Pressespiegel/app.js','../Pressespiegel/github.js','./direct-feedback.js'])assert.ok(html.includes(src));
assert.ok(pref.includes('src="../Pressespiegel/preferences.js?v=20261028v3"'));
assert.ok(js.includes('MORGENZEITUNG_V3_FEEDBACK_V1'));
assert.ok(js.includes('[Morgenzeitung 3] Feedback '));
assert.ok(!js.includes('MORGENZEITUNG_NEU_FEEDBACK_V1'));
assert.ok(!/\b(?:XMLHttpRequest|HEAD|no-cors)\b/.test(js));
const index=JSON.parse(fs.readFileSync(base+'data/index.json','utf8'));
for(const date of index.dates){
 const e=JSON.parse(fs.readFileSync(base+'data/'+date+'.json','utf8'));
 assert.equal(e.date,date);assert.ok(e.articles.length&&e.headlines.length);
 assert.equal(typeof e.preview,'boolean');
 assert.ok(e.fact_audit&&e.selection_audit);
 if(e.preview)assert.notEqual(e.fact_audit.status,'pass');
 else {assert.equal(e.fact_audit.status,'pass');assert.equal(e.fact_audit.warning_count,0);}
 const ids=new Set(),urls=new Set();
 for(const [section,items] of [['articles',e.articles],['headlines',e.headlines]])for(const x of items){
  assert.match(x.id,/^[a-f0-9]{16}$/);assert.ok(x.title&&x.summary&&x.source&&x.published_at);
  assert.equal(new URL(x.url).protocol,'https:');
  assert.ok(!ids.has(x.id)&&!urls.has(x.url));ids.add(x.id);urls.add(x.url);
  if(section==='articles')assert.ok(x.topic);
  else assert.ok(['Österreich','International'].includes(x.region));
 }
}
execFileSync(process.execPath,['--check',base+'direct-feedback.js']);
console.log('PASS V3 shared UI, separated feedback, correct JSON schema; NO link tests');
