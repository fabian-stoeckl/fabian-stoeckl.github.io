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
   const originalFetch=window.fetch.bind(window);
   window.fetch=async(url,opts={})=>{
     const address=String(url);
     const prefix='https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback';
     if(!address.startsWith(prefix))return originalFetch(url,opts);
     const method=opts.method||'GET';
     window.__feedbackTestRequests.push({url:address,method,body:opts.body?JSON.parse(opts.body):null,
       authPresent:opts.headers?.Authorization==='Bearer github_pat_BROWSER_TEST_123456789'});
     if(window.__failFeedbackTest)return new Response(JSON.stringify({message:'offline'}),{status:503,headers:{'Content-Type':'application/json'}});
     const result=method==='GET'?{private:true,full_name:'fabian-stoeckl/morgenzeitung-feedback'}:
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
 await page.locator('#tab-articles').click();
 assert.equal(await page.locator('article').count(),5);
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
 await page.locator('#feedback-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('Erfolgreich'));
 const post=(await calls()).find(r=>r.method==='POST');
 assert(post && post.authPresent);
 assert.match(post.body.body,/Mehr Zahlen/);
 assert.match(post.body.body,/Mehr Handelsblatt/);
 assert.equal(new URL(post.url).pathname,'/repos/fabian-stoeckl/morgenzeitung-feedback/issues');
 assert.match(await page.locator('#feedback-issue-link').getAttribute('href'),/issues\/23/);
 await page.locator('#feedback-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('Bereits'));
 assert.equal((await calls()).filter(r=>r.method==='POST').length,1);
 await page.locator('#feedback').fill('Mehr KI und Industrie');
 await page.locator('#feedback-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('aktualisiert'));
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
