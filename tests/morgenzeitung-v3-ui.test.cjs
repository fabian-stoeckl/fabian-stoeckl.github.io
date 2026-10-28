'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs');
const {execFileSync}=require('node:child_process');
const base='Privat/Morgenzeitung-3/';
const html=fs.readFileSync(base+'index.html','utf8'),home=fs.readFileSync('Privat/index.html','utf8');
const pref=fs.readFileSync(base+'praeferenzen.html','utf8');
const js=fs.readFileSync(base+'direct-feedback.js','utf8');
assert.equal((home.match(/href="\.\/Morgenzeitung-3\/"/g)||[]).length,1);
assert.ok(!home.includes('href="./Pressespiegel/"')&&!home.includes('href="./Morgenzeitung-neu/"'));
for(const id of ['date','headlines','articles','feedback-section','github-setup','tab-headlines','tab-articles','profile-toggle'])assert.ok(html.includes('id="'+id+'"'));
for(const src of ['./style.css','./app.js','./github.js','./direct-feedback.js'])assert.ok(html.includes(src));
for(const src of ['./preferences.js','./preference-timeline.js'])assert.ok(pref.includes(src));
for(const path of ['app.js','github.js','style.css','preferences.js','preference-timeline.js'])assert.ok(fs.existsSync(base+path));
assert.ok(!html.includes('Pressespiegel/')&&!pref.includes('Pressespiegel/'));
assert.ok(js.includes('MORGENZEITUNG_V3_FEEDBACK_V1'));
assert.ok(!js.includes('MORGENZEITUNG_NEU_FEEDBACK_V1'));
const index=JSON.parse(fs.readFileSync(base+'data/index.json','utf8'));
for(const date of index.dates){
 const e=JSON.parse(fs.readFileSync(base+'data/'+date+'.json','utf8'));
 assert.equal(e.date,date);assert.ok(e.articles.length&&e.headlines.length);
 assert.equal(typeof e.preview,'boolean');
 const ids=new Set(),urls=new Set();
 for(const [section,items] of [['articles',e.articles],['headlines',e.headlines]])for(const x of items){
  assert.match(x.id,/^[a-f0-9]{16}$/);assert.ok(x.title&&x.summary&&x.source&&x.published_at);
  assert.equal(new URL(x.url).protocol,'https:');
  assert.ok(!ids.has(x.id)&&!urls.has(x.url));ids.add(x.id);urls.add(x.url);
  if(section==='articles')assert.ok(x.topic);
  else assert.ok(['Österreich','International'].includes(x.region));
 }
}
for(const path of ['app.js','github.js','direct-feedback.js','preferences.js','preference-timeline.js'])
 execFileSync(process.execPath,['--check',base+path]);
console.log('PASS: only V3 dashboard, independent local reader and feedback, valid editions');
