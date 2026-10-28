const assert=require('node:assert/strict');const {chromium}=require('playwright');
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
for(const width of [390,1440]){
 const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 let issues=[],writes=0,failAfterCreate=true;
 await page.addInitScript(()=>localStorage.setItem('morgenzeitung:github-token:v1','fake-local-test-token'));
 await page.route('https://api.github.com/**',async route=>{
  const req=route.request(),url=new URL(req.url());let result;
  if(url.pathname.includes('/contents/'))result={content:Buffer.from('Ich suche wirtschaftliche Zusammenhänge.').toString('base64')};
  else if(req.method()==='POST'){
   writes++;const data=req.postDataJSON();const issue={...data,number:issues.length+1,html_url:'https://github.com/example/issue'};issues.push(issue);
   if(failAfterCreate){failAfterCreate=false;await route.abort();return;}result=issue;
  }else if(/\/issues\/\d+$/.test(url.pathname))result=issues.find(x=>x.number===Number(url.pathname.split('/').pop()));
  else if(url.pathname.endsWith('/issues'))result=issues;
  else result={private:true,full_name:'fabian-stoeckl/morgenzeitung-feedback'};
  await route.fulfill({json:result});
 });
 await page.goto((process.env.PREVIEW_URL||'http://127.0.0.1:8766')+'/Privat/Pressespiegel/');await page.waitForSelector('.story');await page.waitForSelector('#interest-text:not([hidden])');
 assert.match(await page.locator('#edition-meta').innerText(),/Übernommene Ausgabe/);
 assert.match(await page.locator('#interest-text').innerText(),/wirtschaftliche/);
 const rating=page.locator('.rating').first();await rating.locator('summary').click();await rating.getByLabel('Sehr relevant',{exact:true}).check();await rating.locator('textarea').fill('Gute Erklärung');await page.locator('#comment').fill('Mehr Einordnung');
 await page.locator('#save-feedback').click();await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('Erneutes Speichern'));
 await page.locator('#save-feedback').click();await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('gespeichert.'));
 assert.equal(writes,1,'Retry must find the already-created event');
 const data=JSON.parse(issues[0].body.split('\n').slice(1).join('\n'));assert.equal(data.ratings[0].reason,'Gute Erklärung');assert.equal(data.comment,'Mehr Einordnung');
 await page.locator('#save-feedback').click();assert.match(await page.locator('#feedback-status').innerText(),/zuerst einen Artikel/);
 await page.locator('#comment').fill('Neue Rückmeldung');await page.locator('#save-feedback').click();await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('gespeichert.'));assert.equal(writes,2);assert.equal(JSON.parse(issues[1].body.split('\n').slice(1).join('\n')).ratings.length,0);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 // Browser network abort above is intentional; no JavaScript page errors.
 assert.deepEqual(errors,[]);
 const fs=require('node:fs');fs.mkdirSync('artifacts/screenshots',{recursive:true});await page.screenshot({path:'artifacts/screenshots/pressespiegel-'+width+'.png',fullPage:true});
 await context.close();
}await browser.close();console.log('PASS Pressespiegel: mobile/desktop, profile reading, feedback and retry without duplicate');})().catch(e=>{console.error(e);process.exit(1)});
