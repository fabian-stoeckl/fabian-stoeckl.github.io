'use strict';
// One offline browser journey. No requests to real GitHub or article publishers.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{
 const latest=JSON.parse(fs.readFileSync('Privat/Persoenliche-Zeitung/data/index.json','utf8')).dates[0];
 const edition=JSON.parse(fs.readFileSync('Privat/Persoenliche-Zeitung/data/'+latest+'.json','utf8'));
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const context=await browser.newContext({viewport:{width:390,height:800}});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',err=>errors.push(err.message));
 await page.addInitScript(()=>{
   localStorage.setItem('morgenzeitung:github-token:v1','github_pat_V3_FAKE_LOCAL_TEST_ONLY_123456789');
   const original=window.fetch.bind(window);
   window.fetch=async(url,opts={})=>{
     const endpoint=String(url);
     const root='https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback';
     if(!endpoint.startsWith(root))return original(url,opts);
     const path=endpoint.slice(root.length);
     const method=opts.method||'GET';
     let result;
     if(path==='')result={full_name:'fabian-stoeckl/morgenzeitung-feedback',private:true};
     else if(method==='GET'&&path.startsWith('/issues?')){
       const saved=JSON.parse(sessionStorage.getItem('v3-mock-issue')||'null');
       result=saved?[saved]:[];
     }else if(method==='GET'&&path==='/issues/91'){
       result=JSON.parse(sessionStorage.getItem('v3-mock-issue')||'null');
     }else if((method==='POST'||method==='PATCH')&&/^\/issues(?:\/91)?$/.test(path)){
       const payload=JSON.parse(opts.body);
       sessionStorage.setItem('v3-mock-write-count',String(
         1+Number(sessionStorage.getItem('v3-mock-write-count')||0)));
       const saved={...payload,number:91,updated_at:'2026-10-28T10:00:00Z',
         html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/91'};
       sessionStorage.setItem('v3-mock-issue',JSON.stringify(saved));
       result=saved;
     }else throw Error('Unexpected private GitHub test request '+method+' '+endpoint);
     return new Response(JSON.stringify(result),{status:200,headers:{'Content-Type':'application/json'}});
   };
 });
 // The current newspaper must load directly, never through an old-URL
 // 404 page or a client-side redirect.
 const direct = await page.goto('http://127.0.0.1:8766/Privat/Persoenliche-Zeitung/');
 assert.equal(direct.status(),200);
 assert.equal(new URL(page.url()).pathname,'/Privat/Persoenliche-Zeitung/');
 await page.waitForSelector('#headlines .news-item .rating-dots input');
 assert.match(await page.locator('h1').first().innerText(),/Persönliche Zeitung/);
 const publicationStatus=await page.locator('#publication-status').innerText();
 if(edition.preview)assert.match(publicationStatus,/Beispielausgabe/);
 else assert.doesNotMatch(publicationStatus,/Beispielausgabe/);
 assert.equal(await page.locator('#github-connected').isHidden(),false);
 await page.locator('#headlines .news-item').first().getByLabel('Sehr relevant',{exact:true}).check();
 await page.locator('#tab-articles').click();
 await page.locator('#articles article').first().getByLabel('Nicht relevant',{exact:true}).check();
 // Simultaneous submissions from different save buttons within the same
 // tab must result in one API write, never duplicate same-date Issues.
 await page.evaluate(()=>{
   const form=document.getElementById('feedback-form');
   form.requestSubmit();
   form.requestSubmit();
 });
 await page.waitForFunction(()=>document.querySelector('#feedback-status')?.textContent.includes('erfolgreich'));
 assert.equal(await page.evaluate(()=>Number(sessionStorage.getItem('v3-mock-write-count'))),
              1,'One tab must not start duplicate concurrent feedback writes');
 const saved=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('v3-mock-issue')));
 assert.equal(saved.title,'[Morgenzeitung 3] Feedback '+latest);
 assert.ok(saved.body.startsWith('MORGENZEITUNG_V3_FEEDBACK_V1\n'));
 const payload=JSON.parse(saved.body.split('\n').slice(1).join('\n'));
 assert.equal(payload.ratings.length,2);
 assert.deepEqual(payload.ratings.map(r=>r.rating).sort(),['Nicht relevant','Sehr relevant']);
 // The old access="full" flag never proves the editorial team read that text.
 await page.evaluate(()=>{
   edition.articles[0].access='full';
   delete edition.articles[0].evidence_level;
   render();
 });
 await page.waitForFunction(()=>document.querySelector('#articles article .v3-extra-context')?.textContent.includes('nicht dokumentiert'));
 // V3.5: Only genuine edition-provided editorial notes and comparisons show.
 await page.evaluate(()=>{
   edition.articles[0].article_type='analysis';
   edition.articles[0].evidence_level='teaser';
   edition.articles[0].why_selected='Dokumentiert einen belegten wirtschaftlichen Mechanismus.';
   edition.editorial_comparisons=[{
     id:'fedcba9876543210',
     selected_title:edition.articles[0].title,
     selected_url:edition.articles[0].url,
     alternative_title:'Alternative, öffentlich recherchierte Analyse',
     alternative_url:'https://example.org/verified-alternative'
   }];
   render();
 });
 await page.waitForSelector('#v3-comparisons fieldset');
 assert.match(await page.locator('#articles article .v3-why').first().innerText(),
              /Warum ausgewählt.*wirtschaftlichen Mechanismus/);
 assert.match(await page.locator('#articles article .v3-extra-context').first().innerText(),
              /analysis.*Vorspann/);
 assert.equal(await page.locator('#v3-comparisons fieldset').count(),1);
 // Lead/rest ordering can differ from edition order when a story is a treat.
 // Every context note must follow its immutable article ID, not DOM index.
 await page.evaluate(()=>{
   edition.articles[1].treat=true;
   edition.articles[1].article_type='interview';
   edition.articles[1].why_selected='Gesondert belegte Perspektive aus einem Interview.';
   render();
 });
 const secondId=edition.articles[1].id;
 const second=page.locator('#articles article[data-article-id="'+secondId+'"]');
 assert.equal(await second.count(),1);
 assert.match(await second.locator('.v3-extra-context').first().innerText(),/interview/);
 assert.match(await second.locator('.v3-why').first().innerText(),/Gesondert belegte Perspektive/);
 assert.ok(await second.evaluate(node=>node.parentElement.classList.contains('article-list')));

 await page.locator('#v3-comparisons input[value=alternative]').check();
 await page.locator('#feedback-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status')?.textContent.includes('aktualisiert'));
 const comparisonIssue=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('v3-mock-issue')));
 const comparisonData=JSON.parse(comparisonIssue.body.split('\n').slice(1).join('\n'));
 assert.match(comparisonData.comment,/V3-Vergleich.*alternative/);
 assert.equal(comparisonData.ratings.length,2,'Comparisons never create fabricated article ratings');
 // Later general feedback must not erase previously recorded comparisons.
 await page.evaluate(()=>{delete edition.editorial_comparisons;render();});
 await page.locator('#feedback').fill('Weitere eigene Gedanken');
 await page.locator('#feedback-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status')?.textContent.includes('aktualisiert'));
 const followUp=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('v3-mock-issue')));
 const notes=JSON.parse(followUp.body.split('\n').slice(1).join('\n')).comment;
 assert.match(notes,/Weitere eigene Gedanken/);
 assert.match(notes,/V3-Vergleich.*alternative/);

 // Unsent free-text must stay attached to its originating edition, not leak
 // into an issue from another date when the reader uses the date dropdown.
 await page.locator('#feedback').fill('Ungesendete Gedanken 28. Oktober');
 await page.evaluate(()=>{
   const date='2026-10-29';
   const option=document.createElement('option');option.value=date;option.textContent=date;
   document.getElementById('date').append(option);
   const existing=GitHubPaper.edition;
   GitHubPaper.edition=async day=>day===date?{...edition,date}:existing(day);
 });
 await page.locator('#date').selectOption('2026-10-29');
 await page.waitForFunction(()=>edition.date==='2026-10-29');
 assert.equal(await page.locator('#feedback').inputValue(),'');
 await page.locator('#feedback').fill('Ungesendeter Kommentar 29. Oktober');
 await page.locator('#date').selectOption(latest);
 await page.waitForFunction(d=>edition.date===d,latest);
 assert.equal(await page.locator('#feedback').inputValue(),'Ungesendete Gedanken 28. Oktober');
 await page.locator('#date').selectOption('2026-10-29');
 await page.waitForFunction(()=>edition.date==='2026-10-29');
 assert.equal(await page.locator('#feedback').inputValue(),'Ungesendeter Kommentar 29. Oktober');

 await page.goto('http://127.0.0.1:8766/Privat/Persoenliche-Zeitung/praeferenzen.html');
 await page.waitForFunction(()=>document.querySelector('#preference-feedback')?.textContent.includes('Artikelbewertungen'));
 assert.match(await page.locator('#preference-feedback').innerText(),/2 Artikelbewertungen/);
 assert.equal(errors.length,0,errors.join('\n'));
 await context.close();await browser.close();
 console.log('PASS V3 browser: mobile reader, both ratings, private API mock, preference history');
})().catch(e=>{console.error(e);process.exit(1);});
