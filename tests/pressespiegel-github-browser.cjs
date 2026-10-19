const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--single-process']});
const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8765/Privat/Pressespiegel/');
await page.waitForSelector('article');assert.equal(await page.locator('article').count(),5);
assert.equal(await page.locator('.ratings button:disabled').count(),15);
for(const width of [1440,390]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:`artifacts/screenshots/morgenzeitung-github-${width}.png`,fullPage:true});}
await page.route('**/config.json',r=>r.fulfill({json:{mode:'github',feedback_repository:'fabian-stoeckl/morgenzeitung-feedback',api:null,preview:true}}));
await page.reload();await page.waitForSelector('.ratings a');
const first=page.locator('.ratings').first();await first.locator('select').selectOption('Schon bekannt');
let target=new URL(await first.locator('a').first().getAttribute('href'));assert.match(target.searchParams.get('body'),/Grund: Schon bekannt/);
assert.equal(target.hostname,'github.com');assert.equal(await first.locator('a').count(),3);
await page.locator('#feedback').fill('Mehr zu Produktivität & Forschung.');
await page.locator('#feedback-form button').click();
target=new URL(await page.locator('#feedback-status a').getAttribute('href'));assert.match(target.searchParams.get('body'),/Produktivität & Forschung/);
assert(!await page.locator('#feedback-status').innerText().then(t=>t.includes('Gespeichert')));
await page.locator('#tab-headlines').click();assert.equal(await page.locator('#headlines li').count(),4);
assert.deepEqual(errors,[]);await browser.close();console.log('Static feed and GitHub handoff passed at desktop/mobile; no GitHub submission performed.');
})().catch(e=>{console.error(e);process.exit(1)});
