'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  for(const width of [390,1440]){
   const context=await browser.newContext({viewport:{width,height:900}});
   const page=await context.newPage(),errors=[];
   const issues=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.addInitScript(()=>localStorage.setItem('morgenzeitung:github-token:v1','github_pat_'+'A'.repeat(42)));
   await page.route('https://api.github.com/**',async route=>{
    const req=route.request(),url=new URL(req.url());
    let response;
    if(url.pathname.includes('/contents/morgenzeitung-neu/')){
     const responseText=url.pathname.endsWith('begruendungsvorschlaege.json')?JSON.stringify({version:1,suggestions:['Zu juristisch für ein Randthema']}):url.pathname.endsWith('interessen.md')?'Ich interessiere mich für gut belegte Analysen und neue wirtschaftliche Erkenntnisse.':'28.10.2026: Startbeschreibung aus früherem Feedback übernommen.';
     response={content:Buffer.from(responseText).toString('base64')};
    }else if(req.method()==='POST'&&url.pathname.endsWith('/issues')){
     const body=req.postDataJSON();
     response={...body,number:50+issues.length,html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/'+(50+issues.length),updated_at:'2026-10-28T16:00:00Z'};
     issues.push(response);
    }else if(/\/issues\/\d+$/.test(url.pathname)){
     response=issues.find(x=>x.number===Number(url.pathname.split('/').at(-1)))||{message:'not found'};
    }else if(url.pathname.endsWith('/issues')){
     response=issues;
    }else{
     response={private:true,full_name:'fabian-stoeckl/morgenzeitung-feedback'};
    }
    await route.fulfill({status:200,json:response});
   });
   await page.route('**/Privat/Morgenzeitung-Neu/data/2026-10-28.json',async route=>{
     const response=await route.fetch();
     const sample=await response.json();
     sample.articles[0].related_article={title:'Independent follow-up',source:'Another publisher',url:'https://example.org/follow-up'};
     await route.fulfill({response,json:sample});
   });
   const root=(process.env.PREVIEW_URL||'http://127.0.0.1:8766')+'/Privat/Morgenzeitung-Neu/';
   await page.goto(root);
   await page.waitForSelector('#feedback-section:not([hidden])');
   assert.equal(await page.locator('.value-proposition').count(),0,'Classic reader has no promotional introduction');
   assert.equal(await page.locator('#publication-status').isVisible(),false);
   assert.equal(await page.locator('#feedback').isVisible(),true,'Open feedback is always visible');
   assert.ok(await page.locator('.feedback-suggestions button').count()>=4);
   await page.locator('.feedback-suggestions button').first().click();
   assert.match(await page.locator('#feedback').inputValue(),/Thema interessiert/);
   await page.locator('#tab-articles').click();
   assert.equal(await page.locator('#articles').isVisible(),true);
   assert.equal(await page.getByText('Weiterer Beitrag zum Thema:').count(),1,'Related reporting is separately marked');
   assert.equal(await page.getByRole('link',{name:'Independent follow-up'}).getAttribute('href'),'https://example.org/follow-up');
   const group=page.locator('#articles .ratings').first();
   await group.locator('input[type=radio][value="Sehr relevant"]').check();
   assert.equal(await group.locator('.rating-reason').evaluate(el=>el.open),true);
   assert.equal(await group.getByText('Deine Begründung').count(),0);
   assert.equal(await group.getByText('Optionale Gründe auswählen; eigener Text bleibt separat:').count(),0);
   await group.locator('.v3-reason-choice').first().click();
   await group.locator('.personal-reason-choice').first().click();
   await page.locator('#feedback-form button[type=submit]').click();
   await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('gespeichert.'));
   assert.equal(issues.length,1);
   assert.match(issues[0].body,/MORGENZEITUNG_NEU_FEEDBACK_V1/);
   const payload=JSON.parse(issues[0].body.slice(issues[0].body.indexOf('\n')+1));
   assert.ok(payload.ratings.length>=1&&payload.comment.includes('Thema interessiert'));
   assert.ok(payload.ratings.some(r=>r.suggested_reasons?.includes('Zu juristisch für ein Randthema')));
   await page.getByRole('link',{name:/Meine Präferenzen/}).first().click();
   await page.waitForURL(/praeferenzen.html/);
   await page.waitForSelector('#profile-text:not([hidden])');
   assert.match(await page.locator('#profile-text').innerText(),/wirtschaftliche Erkenntnisse/);
   assert.ok((await page.locator('#profile-changes').innerText()).includes('Startbeschreibung'));
   assert.equal(await page.locator('#preference-comment').isVisible(),true);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'No horizontal overflow');
   assert.deepEqual(errors,[],'No JS page errors');
   await context.close();
  }
 }finally{await browser.close();}
 console.log('PASS: 390px and 1440px classic reader, review codes, open feedback and private description');
})().catch(err=>{console.error(err);process.exitCode=1;});
