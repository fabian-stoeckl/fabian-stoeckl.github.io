const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
 const context=await browser.newContext(),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 // Intercept only in this isolated test page: no outbound requests to GitHub and no real credentials.
 await page.addInitScript(()=>{
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
       (address.endsWith('/issues/23')?{number:23,body:window.__feedbackTestIssueBody}:{private:true,full_name:'fabian-stoeckl/morgenzeitung-feedback'}):
       {number:23,html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/23'};
     return new Response(JSON.stringify(result),{status:200,headers:{'Content-Type':'application/json'}});
   };
 });
 const calls=()=>page.evaluate(()=>window.__feedbackTestRequests);
 await page.goto('http://127.0.0.1:8765/Privat/Pressespiegel/');
 await page.waitForSelector('#headlines li a');
 assert.equal(await page.locator('#overview').count(),0);
 assert.equal(await page.locator('.deck').count(),0);
 assert.equal(await page.locator('.tabs button').count(),2);
 assert.equal(await page.locator('#tab-headlines').getAttribute('aria-pressed'),'true');
 assert.equal(await page.locator('#headlines h2').allTextContents().then(a=>a.join(', ')),'Österreich, International');
 await page.locator('#headlines .news-item').first().getByLabel('Nicht relevant',{exact:true}).check();
 await page.locator('#headlines .news-item').first().locator('textarea').fill('Doppelte Nachricht');
 await page.locator('#tab-articles').click();
 assert.equal(await page.locator('article').count(),2);
 assert.equal(await page.locator('#headlines .news-item').count(),3);
 assert.equal(await page.locator('#feedback-settings #github-setup').count(),1);
 assert.equal(await page.evaluate(()=>document.querySelector('#feedback-settings').compareDocumentPosition(document.querySelector('#feedback-section'))&Node.DOCUMENT_POSITION_PRECEDING),2);
 assert(await page.locator('#github-setup').isVisible());
 await page.locator('article').first().getByLabel('Sehr relevant',{exact:true}).check();
 await page.locator('article').first().locator('textarea').fill('Mehr Zahlen');
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
 await page.locator('#github-disconnect').click();
 assert(await page.locator('#github-setup').isVisible());
 assert.equal(await page.evaluate(()=>localStorage.getItem('morgenzeitung:github-token:v1')),null);
 assert.deepEqual(errors,[]);
 await browser.close();
 console.log('GitHub direct-save UI tests with fully mocked API passed.');
})().catch(e=>{console.error(e);process.exit(1)});
