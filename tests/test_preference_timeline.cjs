const test=require('node:test');
const assert=require('node:assert/strict');
const timeline=require('../Privat/Persoenliche-Zeitung/preference-timeline.js');
test('chronological score changes, corrected vote, no geographic topic inference',()=>{
 const metadata=new Map([['2026-10-21:a',{topic:'KI',title:'AI'}],
 ['2026-10-22:b',{topic:'KI',title:'AI 2'}],
 ['2026-10-22:c',{title:'Local',topic:null}]]);
 const history=[
 {date:'2026-10-22',updated_at:'2026-10-22T12:00:00Z',ratings:[{id:'b',value:'Nicht relevant'},{id:'c',value:'Sehr relevant'}]},
 {date:'2026-10-21',updated_at:'2026-10-21T12:00:00Z',ratings:[{id:'a',value:'Sehr relevant'}]},
 {date:'2026-10-22',updated_at:'2026-10-22T13:00:00Z',ratings:[{id:'b',value:'Sehr relevant'}]}];
 const result=timeline.calculate(history,metadata);
 assert.deepEqual(result.map(x=>x.date),['2026-10-22','2026-10-21']);
 assert.deepEqual(result.map(x=>x.entries[0].after),[2,1]);
 assert.equal(result[0].entries.length,1);
});
test('replayed identical ratings do not duplicate',()=>{
 const m=new Map([['2026-10-21:a',{topic:'Industrie'}]]);
 const issue={date:'2026-10-21',updated_at:'2026-10-21T12:00:00Z',ratings:[{id:'a',value:'Sehr relevant'}]};
 assert.equal(timeline.calculate([issue,issue],m)[0].entries[0].after,1);
});

test('summary uses only latest revision of each article, consistent with timeline',()=>{
 const h=[
  {date:'2026-10-22',updated_at:'2026-10-22T09:00:00Z',ratings:[{id:'a',value:'Nicht relevant'}]},
  {date:'2026-10-22',updated_at:'2026-10-22T12:00:00Z',ratings:[{id:'a',value:'Sehr relevant'}]},
  {date:'2026-10-23',updated_at:'2026-10-23T12:00:00Z',ratings:[{id:'b',value:'Teilweise relevant'}]}];
 const rows=timeline.reconcile(h);
 assert.equal(rows.length,2);
 assert.equal(rows.find(r=>r.id==='a').value,'Sehr relevant');
 assert.equal(rows.find(r=>r.id==='b').value,'Teilweise relevant');
 const m=new Map([['2026-10-22:a',{topic:'KI'}],['2026-10-23:b',{topic:'KI'}]]);
 const events=timeline.calculate(h,m);
 assert.equal(events[0].entries[0].after,1);
});
