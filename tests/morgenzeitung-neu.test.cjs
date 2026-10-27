'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const root=path.join(__dirname,'..');
const base=path.join(root,'Privat/Morgenzeitung-neu');
const html=fs.readFileSync(path.join(base,'index.html'),'utf8');
const app=fs.readFileSync(path.join(base,'app.js'),'utf8');
const homepage=fs.readFileSync(path.join(root,'Privat/index.html'),'utf8');
assert.ok(homepage.includes('href="./Morgenzeitung-neu/"'),'Homepage tile missing');
for(const id of ['date','entries','show-deep','show-news','save','connection','learning','comment'])assert.ok(html.includes('id="'+id+'"'),'Missing '+id);
assert.ok(app.includes("MORGENZEITUNG_NEU_FEEDBACK_V1"));
assert.ok(app.includes('github-token:v1'),'Existing local connection should be reusable');
assert.ok(!app.includes('Linktest')&&!app.includes('HEAD'), 'no article link checker');
execFileSync(process.execPath,['--check',path.join(base,'app.js')]);
const dates=JSON.parse(fs.readFileSync(path.join(base,'data/index.json'),'utf8')).dates;
assert.ok(Array.isArray(dates)&&dates.length>0);
const uniqueDates=new Set(dates);
assert.equal(uniqueDates.size,dates.length);
for(const date of dates){
 assert.match(date,/^\d{4}-\d{2}-\d{2}$/);
 const data=JSON.parse(fs.readFileSync(path.join(base,'data',date+'.json'),'utf8'));
 assert.equal(data.date,date);assert.ok(typeof data.learning_note==='string'&&data.learning_note.length>20);
 assert.ok(data.articles.length>=10&&data.articles.length<=15,'10-15 deep items');
 assert.ok(data.headlines.length>=15&&data.headlines.length<=20,'15-20 headlines');
 const ids=new Set(),urls=new Set();
 for(const a of [...data.articles,...data.headlines]){
   assert.match(a.id,/^[a-f0-9]{16}$/);assert.ok(!ids.has(a.id),'Repeated ID');ids.add(a.id);
   assert.ok(a.title.length>8&&a.summary.length>25&&a.source.length>1);
   assert.ok(new URL(a.url).protocol==='https:');
   assert.ok(!urls.has(a.url),'Repeated URL');urls.add(a.url);
   assert.ok(!a.published_at||!Number.isNaN(new Date(a.published_at).valueOf()));
   if(a.evidence)assert.ok(['headline','teaser','read'].includes(a.evidence));
 }
 assert.ok(new Set(data.articles.map(a=>a.source)).size>=3,'Avoid publisher monoculture');
 console.log('PASS:',date,data.articles.length,'deep articles;',data.headlines.length,'headlines (no HTTP link checks)');
}
