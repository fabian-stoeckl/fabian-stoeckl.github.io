const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
 const errors=[];const page=await browser.newPage({viewport:{width:1440,height:1050}});
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/');await page.waitForSelector('article');
 assert.equal(await page.locator('article').count(),5);
 assert.equal(await page.locator('article .ratings button').count(),15);
 const first=page.locator('article').first();
 await first.getByRole('button',{name:'Sehr relevant',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('article .rating-state').textContent.startsWith('Gespeichert'));
 // A separate browser context represents another device using the same private store.
 const browser2=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});const second=await browser2.newPage();await second.goto('http://127.0.0.1:8765/');await second.waitForSelector('article');
 assert.equal(await second.locator('article').first().getByRole('button',{name:'Sehr relevant',exact:true}).getAttribute('aria-pressed'),'true');
 await first.getByRole('button',{name:'Nicht relevant',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('article .rating-state').textContent.startsWith('Gespeichert'));
 await page.reload();await page.waitForSelector('article');
 assert.equal(await page.locator('article').first().getByRole('button',{name:'Nicht relevant',exact:true}).getAttribute('aria-pressed'),'true');
 await page.getByRole('button',{name:'Heute wichtig'}).click();assert.equal(await page.locator('#headlines li').count(),4);
 await page.getByRole('button',{name:'Für dich ausgewählt'}).click();
 await page.locator('#feedback').fill('Browser-Test: Mehr über Produktivität');await page.getByRole('button',{name:'Feedback speichern'}).click();await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.startsWith('Gespeichert'));
 await page.getByRole('button',{name:'Interessenprofil',exact:true}).click();await page.waitForSelector('#profile:not([hidden])');
 await page.locator('#rules').fill('Testregel: belastbare Zahlen priorisieren.');await page.getByRole('button',{name:'Profil speichern'}).click();await page.waitForFunction(()=>document.querySelector('#profile-status').textContent.startsWith('Gespeichert'));
 await page.getByRole('button',{name:'Interessenprofil',exact:true}).click();
 // A failed write must remain visibly unsaved.
 await page.route('**/api/rating',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Speicherfehler'})}));
 await page.locator('article').first().getByRole('button',{name:'Teilweise relevant',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('article .rating-state').textContent.includes('nicht gespeichert'));
 await page.unroute('**/api/rating');await page.reload();await page.waitForSelector('article');
 assert.equal(await page.locator('article').first().getByRole('button',{name:'Nicht relevant',exact:true}).getAttribute('aria-pressed'),'true');
 const hrefs=await page.evaluate(()=>{const n=readingLinks({url:'https://www.diepresse.com/123/test?x=1&y=2',paywall:true});return [...n.querySelectorAll('a')].map(a=>[a.textContent,a.href]);});
 assert.equal(hrefs[1][0],'SMRY öffnen ↗');assert.equal(hrefs[1][1],'https://smry.ai/https://www.diepresse.com/123/test?x=1&y=2');assert.equal(hrefs[2][0],'Archivsuche ↗');
 fs.mkdirSync('artifacts/screenshots',{recursive:true});
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1050});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:`artifacts/screenshots/morgenzeitung-${width}.png`,fullPage:true});
 }
 assert.deepEqual(errors,[]);console.log('Browser: ratings, second client, feedback, profile, failure state, tabs, 1440/390px passed');await browser2.close();await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
