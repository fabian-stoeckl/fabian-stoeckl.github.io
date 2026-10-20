const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
 const context=await browser.newContext();
 await context.route('https://github.com/**',r=>r.fulfill({status:200,contentType:'text/html',body:'<!doctype html><title>GitHub mock</title>'}));
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/Privat/Pressespiegel/');
 await page.waitForSelector('article');
 assert.equal(await page.locator('#overview-list li').count(),3);
 assert.match(await page.locator('#overview').innerText(),/Universit.tsbudget/i);
 assert.equal(await page.locator('#headline-count').innerText(),'4');
 assert.equal(await page.locator('article').count(),5);
 await page.locator('article').first().getByLabel('Sehr relevant',{exact:true}).check();
 await page.locator('article').first().locator('textarea').fill('Mehr Zahlen');
 await page.locator('#feedback').fill('Mehr Handelsblatt');
 let popupPromise=page.waitForEvent('popup');
 await page.locator('#feedback-form button[type=submit]').click();
 let popup=await popupPromise;
 let url=new URL(popup.url());
 assert.equal(url.hostname,'github.com');
 assert.equal(url.pathname,'/fabian-stoeckl/morgenzeitung-feedback/issues/new');
 assert.match(url.searchParams.get('body'),/Mehr Zahlen/);
 assert.match(url.searchParams.get('body'),/Mehr Handelsblatt/);
 assert.match(url.searchParams.get('body'),/Artikel-ID:/);
 assert.match(await page.locator('#feedback-status').innerText(),/Erst dann ist dein Feedback gespeichert/);
 assert.equal(await page.locator('#feedback').inputValue(),'Mehr Handelsblatt');
 await popup.close();

 // Large feedback must remain available for a manual paste, without a truncated GitHub URL.
 await page.locator('#feedback').fill('z'.repeat(4000));
 for(const field of await page.locator('article .reason textarea').all())await field.fill('r'.repeat(600));
 popupPromise=page.waitForEvent('popup');
 await page.locator('#feedback-form button[type=submit]').click();
 popup=await popupPromise;url=new URL(popup.url());
 assert.equal(url.searchParams.get('body'),'');
 assert.equal(await page.locator('#manual-feedback').isVisible(),true);
 assert.match(await page.locator('#manual-feedback-body').inputValue(),/zzzzzzzz/);
 assert.match(await page.locator('#feedback-status').innerText(),/Noch nicht gespeichert/);
 await popup.close();
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:`artifacts/screenshots/morgenzeitung-github-${width}.png`,fullPage:true});
 }
 assert.deepEqual(errors,[]);
 await browser.close();
 console.log('GitHub prefilled form, overview, backup link and long feedback fallback passed.');
})().catch(e=>{console.error(e);process.exit(1)});
