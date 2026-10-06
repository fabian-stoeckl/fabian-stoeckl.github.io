const fs=require('fs'),assert=require('node:assert/strict');
const html=fs.readFileSync('Privat/ETFs/index.html','utf8');
const source=html.slice(html.indexOf('function currentDataLag('),html.indexOf('function addDataNote('));
const state=new Function('shortDate','payload',source+';return dataState;')(x=>x,{stale_tolerance_sessions:2});
const valid={series:{2026:[{date:'2026-10-02',price:100}]}};
assert.equal(state(valid).kind,'current');
assert.equal(state({...valid,stale:true,lag_sessions:3,expected_price_date:'2026-10-05'}).kind,'warning');
assert.match(state({...valid,lag_sessions:3,update_error:'unavailable'}).text,/Abruf fehlgeschlagen/);
assert.equal(state({series:{2026:[]}}).kind,'missing');
assert.equal(state({series:{2026:[{date:'2026-10-05',price:null}]}}).kind,'missing');
for(const lag_sessions of [0,1,2]){assert.equal(state({...valid,lag_sessions,update_error:'unavailable'}).kind,'current');}
console.log('PASS visible current, stale, failed-fetch and missing-data states');
const calendar={stale_tolerance_sessions:2,xetra_session_closes:[
{date:'2026-10-02',close:'2026-10-02T15:30:00Z'},
{date:'2026-10-05',close:'2026-10-05T15:30:00Z'},
{date:'2026-10-06',close:'2026-10-06T15:30:00Z'},
{date:'2026-10-07',close:'2026-10-07T15:30:00Z'}]};
const lag=new Function('payload',source+';return currentDataLag;')(calendar);
assert.equal(lag(valid,Date.parse('2026-10-04T20:00Z')).lag,0);
assert.equal(lag(valid,Date.parse('2026-10-06T09:00Z')).lag,1);
assert.equal(lag(valid,Date.parse('2026-10-06T16:00Z')).lag,2);
assert.equal(lag(valid,Date.parse('2026-10-07T16:00Z')).lag,3);
console.log('PASS browser aging against completed sessions and two-session grace');
