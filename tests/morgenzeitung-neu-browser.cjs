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
    }else if(req.method()==='PATCH'&&/\/issues\/\d+$/.test(url.pathname)){
     const n=Number(url.pathname.split('/').at(-1)),idx=issues.findIndex(x=>x.number===n);
     const patch=req.postDataJSON();
     assert.notEqual(idx,-1,'PATCH must update an existing private Issue');
     issues[idx]={...issues[idx],...patch,updated_at:'2026-10-29T03:00:00Z'};
     response=issues[idx];
    }else if(/\/issues\/\d+$/.test(url.pathname)){
     response=issues.find(x=>x.number===Number(url.pathname.split('/').at(-1)))||{message:'not found'};
    }else if(url.pathname.endsWith('/issues')){
     response=issues;
    }else{
     response={private:true,full_name:'fabian-stoeckl/morgenzeitung-feedback'};
    }
    await route.fulfill({status:200,json:response});
   });
   await page.route(/\/Privat\/Morgenzeitung-Neu\/data\/\d{4}-\d{2}-\d{2}\.json(?:\?.*)?$/,async route=>{
     const response=await route.fetch();
     const sample=await response.json();
     sample.articles[0].related_article={title:'Independent follow-up',source:'Another publisher',url:'https://example.org/follow-up'};
     sample.preview=false; // Synthetic real-edition correction fixture.
     sample.articles[0].correction={
       corrected_at:'2026-10-29T12:00:00+01:00',
       previous_summary:'Falsche ursprüngliche Zusammenfassung',
       note:'Eine unzutreffende Behauptung wurde berichtigt.',
       source_url:'https://example.org/evidence'
     };
     await route.fulfill({response,json:sample});
   });
   const root=(process.env.PREVIEW_URL||'http://127.0.0.1:8766')+'/Privat/Morgenzeitung-Neu/';
   await page.goto(root);
   await page.waitForSelector('#feedback-section:not([hidden])');
   assert.equal(await page.locator('.value-proposition').count(),0,'Classic reader has no promotional introduction');
   assert.doesNotMatch(await page.locator('#publication-status').innerText(),/Archivierte Beispielausgabe|keine neue Recherche|kein Nachweis für das neue Lernkonzept/);
   assert.equal(await page.locator('#feedback').isVisible(),true,'Open feedback is always visible');
   assert.ok(await page.locator('.feedback-suggestions button').count()>=4);
   const suggestion=await page.locator('.feedback-suggestions button').first().innerText();
   await page.locator('.feedback-suggestions button').first().click();
   const general=page.locator('#feedback');
   await general.fill((await general.inputValue())+'\nFreie eigene Begründung zur Artikelwahl.');
   assert.match(await general.inputValue(),/Thema interessiert/);
   await page.locator('#tab-articles').click();
   assert.equal(await page.locator('#articles').isVisible(),true);
   assert.equal(await page.locator('#articles .article-correction').count(),1);
   assert.match(await page.locator('#articles .article-correction').innerText(),/unzutreffende Behauptung wurde berichtigt/);
   await page.locator('#articles .correction-history summary').first().click();
   assert.equal(await page.getByText('Falsche ursprüngliche Zusammenfassung').count(),1);
   assert.equal(await page.getByText('Weiterer Beitrag zum Thema:').count(),1,'Related reporting is separately marked');
   assert.equal(await page.getByRole('link',{name:'Independent follow-up'}).getAttribute('href'),'https://example.org/follow-up');
   const correctedId=await page.locator('#articles article').first().getAttribute('data-article-id');
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
   assert.ok(payload.ratings.some(r=>r.id===correctedId),'Correction retains same article rating identity');
   assert.deepEqual(payload.comment_suggestions,[suggestion]);
   assert.ok(payload.comment.includes('Freie eigene Begründung zur Artikelwahl.'));
   assert.ok(payload.ratings.some(r=>r.suggested_reasons?.includes('Zu juristisch für ein Randthema')));
   await page.getByRole('link',{name:/Meine Präferenzen/}).first().click();
   await page.waitForURL(/praeferenzen.html/);
   await page.waitForSelector('#profile-text:not([hidden])');
   assert.match(await page.locator('#profile-text').innerText(),/wirtschaftliche Erkenntnisse/);
   assert.ok((await page.locator('#profile-changes').innerText()).includes('Startbeschreibung'));
   assert.equal(await page.locator('#preference-comment').isVisible(),true);
   const prefSuggestion=await page.locator('.feedback-suggestions button').first().innerText();
   await page.locator('.feedback-suggestions button').first().click();
   const pref=page.locator('#preference-comment');
   await pref.fill((await pref.inputValue())+'\nEigenständiger Hinweis von der Präferenzseite.');
   await page.locator('#preference-comment-form button[type=submit]').click();
   await page.waitForFunction(()=>document.querySelector('#preference-comment-status').textContent.startsWith('Gespeichert.'));
   const revised=JSON.parse(issues[0].body.slice(issues[0].body.indexOf('\n')+1));
   assert.deepEqual(revised.comment_suggestions,[suggestion]);
   assert.equal(prefSuggestion,suggestion);
   assert.ok(revised.comment.includes('Eigenständiger Hinweis von der Präferenzseite.'));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'No horizontal overflow');
   assert.deepEqual(errors,[],'No JS page errors');
   await context.close();
  }
 }finally{await browser.close();}
 console.log('PASS: 390px and 1440px classic reader, review codes, open feedback and private description');
})().catch(err=>{console.error(err);process.exitCode=1;});
