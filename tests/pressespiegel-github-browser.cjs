const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const GitHubPaper=require('../Privat/Pressespiegel/github.js');
const dataDir=path.join(__dirname,'../Privat/Pressespiegel/data');
const currentDate=JSON.parse(fs.readFileSync(path.join(dataDir,'index.json'),'utf8')).dates[0];
const fixture=JSON.parse(fs.readFileSync(path.join(dataDir,currentDate+'.json'),'utf8'));
const visible=GitHubPaper.partition(fixture);
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
 const context=await browser.newContext(),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 // Intercept only in this isolated test page: no outbound requests to GitHub and no real credentials.
 await page.addInitScript((mockDate)=>{
   // This simulates an existing owner's token in the browser before rollout.
   if(!sessionStorage.getItem('__oldTokenSeeded')){
     localStorage.setItem('morgenzeitung:github-token:v1','github_pat_STALE_BROWSER_ONLY_123456789');
     sessionStorage.setItem('__oldTokenSeeded','yes');
   }
   window.__feedbackTestDate=mockDate;
   window.__feedbackTestRequests=[];
   window.__failFeedbackTest=false;
   window.__feedbackTestIssueBody=sessionStorage.getItem('__feedbackMockIssueBody')||null;
   const originalFetch=window.fetch.bind(window);
   window.fetch=async(url,opts={})=>{
     const address=String(url);
     const prefix='https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback';
     if(!address.startsWith(prefix))return originalFetch(url,opts);
     const method=opts.method||'GET';
     window.__feedbackTestRequests.push({url:address,method,body:opts.body?JSON.parse(opts.body):null,
       authPresent:opts.headers?.Authorization==='Bearer github_pat_BROWSER_TEST_123456789'});
     if(window.__failFeedbackTest)return new Response(JSON.stringify({message:'offline'}),{status:503,headers:{'Content-Type':'application/json'}});
     if(method==='POST'||method==='PATCH'){
       window.__feedbackTestIssueBody=JSON.parse(opts.body).body;
       sessionStorage.setItem('__feedbackMockIssueBody',window.__feedbackTestIssueBody);
     }
     const result=method==='GET'?
       (address.includes('/issues?')?(window.__feedbackTestIssueBody?[{
         number:23,title:'[Morgenzeitung] Sammelbewertung '+window.__feedbackTestDate,body:window.__feedbackTestIssueBody,
         updated_at:'2026-10-20T02:00:00Z'
       },{number:3,title:'[TEST – NICHT AUSWERTEN] Kontrollfall',body:'TEST: true'}]:[]):
       address.endsWith('/issues/23')?{number:23,body:window.__feedbackTestIssueBody}:
       {private:true,full_name:'fabian-stoeckl/morgenzeitung-feedback'}):
       {number:23,html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/23'};
     return new Response(JSON.stringify(result),{status:200,headers:{'Content-Type':'application/json'}});
   };
 },currentDate);
 const calls=()=>page.evaluate(()=>window.__feedbackTestRequests);
 await page.goto('http://127.0.0.1:8765/Privat/Pressespiegel/');
 await page.waitForSelector('#headlines li a');
 assert.equal(await page.evaluate(()=>localStorage.getItem('morgenzeitung:github-token:v1')),null);
 assert.match(await page.locator('#github-setup-status').innerText(),/Alter lokal gespeicherter Token gelöscht/);
 await page.setViewportSize({width:1440,height:1000});
 const ratingPosition=async parent=>parent.evaluate(box=>{
   const labels=box.querySelectorAll(':scope > label');
   const summary=box.querySelector('.rating-reason summary');
   const last=labels[labels.length-1].getBoundingClientRect(),optional=summary.getBoundingClientRect();
   return {lastTop:last.top,optionalTop:optional.top,lastRight:last.right,optionalLeft:optional.left};
 });
 const headerPosition=await ratingPosition(page.locator('#headlines .news-item .rating-dots').first());
 assert(Math.abs(headerPosition.lastTop-headerPosition.optionalTop)<18,'News options and explanation must share desktop row');
 assert(headerPosition.optionalLeft>=headerPosition.lastRight&&headerPosition.optionalLeft-headerPosition.lastRight<30,'Optional explanation must sit directly after news options, not right-aligned');
 assert.equal(await page.locator('#headlines .news-item .news-summary').count(),visible.headlines.length);
 assert.equal(await page.locator('#headlines .news-item .news-summary').first().innerText(),visible.headlines[0].summary);
 assert(await page.locator('#notice').isHidden(),'Routine research limitations are not user-visible errors');
 assert.equal(await page.locator('nav.tabs').evaluate(el=>getComputedStyle(el).position),'sticky');
 await page.evaluate(()=>window.scrollTo(0,900));
 await page.waitForFunction(()=>scrollY>=850);
 assert(await page.locator('nav.tabs').evaluate(el=>Math.abs(el.getBoundingClientRect().top)<=2),'Section tabs remain fixed at the top when scrolling');
 await page.evaluate(()=>window.scrollTo(0,0));
 assert.equal(await page.locator('#overview').count(),0);
 assert.equal(await page.locator('.deck').count(),0);
 assert.equal(await page.locator('.tabs button').count(),2);
 assert.equal(await page.locator('#tab-headlines').getAttribute('aria-pressed'),'true');
 assert.equal(await page.locator('#headlines h2').allTextContents().then(a=>a.join(', ')),'Österreich, International');
 await page.locator('#headlines .news-item').first().getByLabel('Nicht relevant',{exact:true}).check();
 assert(await page.locator('#headlines .news-item').first().locator('textarea').isHidden());
 await page.locator('#headlines .news-item').first().locator('.rating-reason summary').click();
 await page.locator('#headlines .news-item').first().locator('textarea').fill('Doppelte Nachricht');
 await page.locator('#tab-articles').click();
 assert.equal(await page.locator('article').count(),visible.articles.length);
 assert.equal(await page.locator('#headlines .news-item').count(),visible.headlines.length);
 assert.equal(await page.locator('#feedback-settings #github-setup').count(),1);
 assert.equal(await page.evaluate(()=>document.querySelector('#feedback-settings').compareDocumentPosition(document.querySelector('#feedback-section'))&Node.DOCUMENT_POSITION_PRECEDING),2);
 assert(await page.locator('#github-setup').isVisible());
 const featurePosition=await ratingPosition(page.locator('#articles article .rating-dots').first());
 assert(Math.abs(featurePosition.lastTop-featurePosition.optionalTop)<18,'Feature options and explanation must share desktop row');
 assert(featurePosition.optionalLeft>=featurePosition.lastRight&&featurePosition.optionalLeft-featurePosition.lastRight<30,'Optional explanation must sit directly after feature options');
 await page.locator('article').first().getByLabel('Sehr relevant',{exact:true}).check();
 assert(await page.locator('article').first().locator('textarea').isHidden());
 await page.locator('article').first().locator('.rating-reason summary').click();
 await page.locator('article').first().locator('textarea').fill('Mehr Zahlen');
 assert.equal(await page.locator('article').first().locator('.links').count(),0);
 assert.equal(await page.locator('article').first().locator('.body > p.small').count(),fixture.articles[0].access==='teaser'?1:0);
 assert.equal(await page.locator('article').first().locator('.body > p.small').first().innerText().catch(()=>''),fixture.articles[0].access==='teaser'?'Zusammenfassung beruht ausschließlich auf dem zugänglichen Vorspann.':'');
 assert.equal(await page.locator('article').first().locator('h2 a').getAttribute('href'),visible.articles[0].url);
 const dateToday=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Vienna',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
 assert.equal(await page.locator('#window').count(),0,'Redundant research date window must be removed');
 const dateLine=await page.locator('#edition-meta').innerText();
 assert.match(dateLine,/Stand [0-2][0-9]:[0-5][0-9] Uhr \(Wien\)/);
 assert.doesNotMatch(dateLine,/bereitgestellt|Recherche:/);
 if(!fixture.preview&&fixture.date===dateToday){
   assert(await page.locator('#publication-status').isHidden(),'Today must not show a duplicate freshness/date line');
 }else{
   assert(await page.locator('#publication-status').isVisible(),'Old/demo edition must retain a useful warning');
 }
 await page.locator('#feedback').fill('Mehr Handelsblatt');
 await page.locator('#feedback-form button[type=submit]').click();
 assert.match(await page.locator('#feedback-status').innerText(),/einmalig/);
 assert.equal((await calls()).length,0);
 await page.locator('#github-token').fill('github_pat_BROWSER_TEST_123456789');
 await page.locator('#remember-token').check();
 await page.locator('#github-setup-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#github-connected')?.hidden===false);
 assert(await page.locator('#github-setup').isHidden());
 assert.equal((await calls())[0].method,'GET');
 await page.locator('#tab-headlines').click();
 await page.locator('#headlines .section-save button').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('erfolgreich'));
 const post=(await calls()).find(r=>r.method==='POST');
 assert(post && post.authPresent);
 assert.match(post.body.body,/Mehr Zahlen/);
 assert.match(post.body.body,/Doppelte Nachricht/);
 assert.match(post.body.body,/Bereich: Heute wichtig/);
 assert.match(post.body.body,/Bereich: Vertiefungen/);
 assert.match(post.body.body,/Mehr Handelsblatt/);
 assert.equal(new URL(post.url).pathname,'/repos/fabian-stoeckl/morgenzeitung-feedback/issues');
 assert.match(await page.locator('#feedback-issue-link').getAttribute('href'),/issues\/23/);
 await page.locator('#tab-articles').click();
 await page.locator('#articles .section-save button').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('bereits'));
 assert.equal((await calls()).filter(r=>r.method==='POST').length,1);
 await page.locator('#feedback').fill('Mehr KI und Industrie');
 await page.locator('#articles .section-save button').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('aktualisiert'));
 assert.match((await calls()).find(r=>r.method==='PATCH').body.body,/Bereich: Heute wichtig/);
 assert.equal((await calls()).filter(r=>r.method==='PATCH').length,1);
 assert(new URL((await calls()).find(r=>r.method==='PATCH').url).pathname.endsWith('/issues/23'));
 await page.evaluate(()=>{window.__failFeedbackTest=true;});
 await page.locator('#feedback').fill('Mehr zum Strommarkt');
 await page.locator('#feedback-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('nicht speichern'));
 assert.equal(await page.locator('#feedback').inputValue(),'Mehr zum Strommarkt');
 assert(await page.locator('#feedback-confirmation').isHidden());
 await page.evaluate(()=>{window.__failFeedbackTest=false;});
 await page.reload();
 await page.waitForSelector('#headlines li a');
 assert(await page.locator('#github-connected').isVisible());
 await page.waitForFunction(()=>document.querySelector('#headlines .news-item input[type=radio][value="Nicht relevant"]')?.checked===true);
 await page.locator('#tab-articles').click();
 await page.waitForFunction(()=>document.querySelector('#articles article input[type=radio][value="Sehr relevant"]')?.checked===true);
 await page.locator('#tab-headlines').click();
 for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:'artifacts/screenshots/morgenzeitung-news-'+width+'.png',fullPage:true});
   await page.locator('#tab-articles').click();
   await page.screenshot({path:'artifacts/screenshots/morgenzeitung-analysen-'+width+'.png',fullPage:true});
   await page.locator('#tab-headlines').click();
 }

 assert.equal(await page.locator('#github-disconnect').count(),0);
 assert.equal(await page.locator('#profile-toggle').innerText(),'Meine Präferenzen');
 await page.locator('#profile-toggle').click();
 assert(await page.locator('#profile').isVisible());
 assert.equal(await page.locator('#profile-toggle').getAttribute('aria-expanded'),'true');
 assert.equal(new URL(page.url()).hash,'#praeferenzen');
 assert.equal(await page.title(),'Meine Präferenzen · Pressespiegel');
 for(const selector of ['.editionline','#publication-status','#notice','nav.tabs','#headlines','#articles','#feedback-section','#feedback-settings','footer']){
   assert(await page.locator(selector).isHidden(),selector+' must disappear completely in preferences view');
 }
 assert(await page.locator('#profile-close').isVisible());
 assert.equal(await page.locator('#profile-toggle').innerText(),'← Zur Morgenzeitung');
 await page.setViewportSize({width:390,height:844});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Preferences page must fit on mobile');
 await page.screenshot({path:'artifacts/screenshots/morgenzeitung-preferences-mobile.png',fullPage:true});
 await page.setViewportSize({width:1440,height:1000});
 await page.waitForFunction(()=>document.querySelector('#preference-feedback')?.textContent.includes('2 Artikelbewertungen'));
 assert.match(await page.locator('#preference-learning-status').innerText(),/nicht verlässlich nachgewiesen/);
 assert.match(await page.locator('#preference-edition-changes').innerText(),/Noch keine zwei veröffentlichten Ausgaben|gegenüber/);
 await page.locator('#preference-comment').fill('Bitte mehr zu Arbeitsproduktivität berichten.');
 await page.locator('#preference-comment-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#preference-comment-status')?.textContent.includes('erfolgreich'));
 const afterPreference=(await calls()).filter(r=>r.method==='PATCH').at(-1);
 assert(afterPreference);
 assert.match(afterPreference.body.body,/Bitte mehr zu Arbeitsproduktivität berichten/);
 assert.match(afterPreference.body.body,/Bereich: Heute wichtig/);
 assert.match(afterPreference.body.body,/Bereich: Vertiefungen/);
 assert.match(afterPreference.body.body,/Mehr KI und Industrie/);
 assert.equal(await page.locator('#preference-comment').inputValue(),'');
 await page.goBack();
 await page.waitForFunction(()=>!document.body.classList.contains('preferences-view'));
 assert(await page.locator('nav.tabs').isVisible(),'Browser Back returns to news');
 assert(await page.locator('#profile').isHidden());
 await page.goForward();
 await page.waitForFunction(()=>document.body.classList.contains('preferences-view'));
 assert(await page.locator('#profile').isVisible(),'Browser Forward restores preferences');
 await page.reload();
 await page.waitForFunction(()=>document.body.classList.contains('preferences-view'));
 assert(await page.locator('nav.tabs').isHidden(),'Direct hash reload is still exclusive');
 await page.locator('#profile-close').click();
 assert(await page.locator('#profile').isHidden());
 assert.equal(new URL(page.url()).hash,'');
 assert(await page.locator('nav.tabs').isVisible(),'Closing preferences restores newspaper');
 assert.equal(await page.locator('#profile-toggle').getAttribute('aria-expanded'),'false');
 assert(await page.locator('#github-connected').isVisible());

 assert.deepEqual(errors,[]);
 await browser.close();
 console.log('GitHub direct-save UI tests with fully mocked API passed.');
})().catch(e=>{console.error(e);process.exit(1)});
