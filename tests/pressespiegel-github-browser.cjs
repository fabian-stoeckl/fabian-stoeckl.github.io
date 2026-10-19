const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8765/Privat/Pressespiegel/');await page.waitForSelector('article');
assert.equal(await page.locator('article').count(),5);assert.equal(await page.locator('input[type=radio]').count(),15);
assert.equal(await page.locator('input[type=radio]:checked').count(),0);
await page.locator('article').nth(0).getByLabel('Sehr relevant',{exact:true}).check();
await page.locator('article').nth(1).getByLabel('Teilweise relevant',{exact:true}).check();
await page.locator('article').nth(0).locator('textarea').fill('Mehr davon, besonders konkrete Zahlen.');
await page.locator('#feedback').fill('Mehr Handelsblatt, bitte.');
await page.locator('#feedback-form button').click();
let url=new URL(await page.locator('#feedback-status a').getAttribute('href'));
const body=url.searchParams.get('body');assert.match(body,/c56eb5eba8a468cf\nBewertung: Sehr relevant\nBegründung: Mehr davon/);assert.match(body,/4a5e7776fa335965\nBewertung: Teilweise relevant/);assert.match(body,/Mehr Handelsblatt/);assert(!body.includes('c9ca944621bdc3ef'));
await page.locator('article').nth(0).getByLabel('Nicht relevant',{exact:true}).check();assert.equal(await page.locator('#feedback-status a').count(),0);
await page.locator('#feedback').fill('');await page.locator('#feedback-form button').click();assert.equal(await page.locator('#feedback-status a').count(),1);
for(const width of [1440,390]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));const boxes=await page.locator('article').evaluateAll(ns=>ns.slice(0,3).map(n=>({x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y})));assert.equal(boxes[0].x,boxes[1].x);assert(boxes[1].y>boxes[0].y);await page.screenshot({path:`artifacts/screenshots/morgenzeitung-simple-${width}.png`,fullPage:true});}
assert.deepEqual(errors,[]);await browser.close();console.log('Single column, radio selection and combined GitHub feedback passed; no submission.');
})().catch(e=>{console.error(e);process.exit(1)});
