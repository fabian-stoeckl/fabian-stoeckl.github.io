const assert=require('node:assert/strict');
const paper=require('../Privat/Pressespiegel/github.js');
assert.throws(()=>paper.issueURL(null,'x','x'));
assert.throws(()=>paper.issueURL('https://evil.test','x','x'));
const url=new URL(paper.ratingURL('fabian-stoeckl/morgenzeitung-feedback',{date:'2026-10-18'},{id:'abc',url:'https://orf.at/stories/1/'},'Sehr relevant','Mehr davon'));
assert.equal(url.origin,'https://github.com');
assert.equal(url.pathname,'/fabian-stoeckl/morgenzeitung-feedback/issues/new');
assert.match(url.searchParams.get('body'),/Artikel-ID: abc\n/);
assert.match(url.searchParams.get('body'),/Bewertung: Sehr relevant/);
assert.match(url.searchParams.get('body'),/Grund: Mehr davon/);
console.log('GitHub feedback URL checks passed');
const batch=paper.batchBody('2026-10-19',[{id:'abc',value:'Sehr relevant',reason:'Mehr davon'},{id:'def',value:'Nicht relevant'}],' Mehr Handelsblatt ');
assert.match(batch,/abc\nBewertung: Sehr relevant\nBegründung: Mehr davon/);assert.match(batch,/def\nBewertung: Nicht relevant\nBegründung: –/);assert(batch.endsWith('Mehr Handelsblatt'));

const both=paper.batchBody('2026-10-20',[
  {id:'a'.repeat(16),value:'Sehr relevant',reason:'Analyse',section:'Vertiefungen'},
  {id:'b'.repeat(16),value:'Teilweise relevant',reason:'Zu häufig',section:'Heute wichtig'}],'Gesamt');
const parsed=paper.parseBatchBody(both);
assert.equal(parsed.date,'2026-10-20');
assert.equal(parsed.ratings.length,2);
assert.equal(parsed.ratings[1].section,'Heute wichtig');
assert.equal(parsed.feedback,'Gesamt');
const legacy=paper.parseBatchBody(paper.batchBody('2026-10-18',[{id:'a'.repeat(16),value:'Nicht relevant',reason:''}],''));
assert.equal(legacy.ratings[0].value,'Nicht relevant');
const data={
 articles:[{url:'https://a.example/article/1/',event:'one',title:'Klimapolitik bringt neue Kosten für Industrie'}],
 headlines:[
 {url:'https://a.example/article/1?utm_source=foo',event:'old',title:'Ein anderer Titel'},
 {url:'https://b.example/test',event:'one',title:'Eine neue Meldung'},
 {url:'https://c.example/test',event:'new',title:'Klimapolitik bringt neue Kosten für Industrie'},
 {url:'https://d.example/story',event:'only-new',title:'Heute neue Themen im Nationalrat'}
]};
const parts=paper.partition(data);
assert.equal(parts.articles.length,1);
assert.equal(parts.headlines.length,1);
assert.equal(parts.duplicatesRemoved,3);
assert.equal(parts.headlines[0].event,'only-new');
assert.throws(()=>paper.parseBatchBody('bad'),/Format/);
