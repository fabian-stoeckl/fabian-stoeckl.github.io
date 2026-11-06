'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const fs=require('node:fs');
const latestFixtureDay=JSON.parse(fs.readFileSync('Privat/Pressespiegel/data/index.json','utf8')).dates[0];
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
    if(url.pathname.endsWith('/lernmonitoring.md')&&width===390){
     await route.fulfill({status:404,json:{message:'Not Found'}});return;
    }
    if(url.pathname.includes('/contents/morgenzeitung-neu/')){
     const responseText=url.pathname.endsWith('lernmonitoring.md')?'Lernbilanz · Morgenzeitung Neu\nNoch nicht beurteilbar.':url.pathname.endsWith('begruendungsvorschlaege.json')?JSON.stringify({version:1,suggestions:['Zu juristisch für ein Randthema']}):url.pathname.endsWith('interessen.md')?'Ich interessiere mich für gut belegte Analysen und neue wirtschaftliche Erkenntnisse.':'28.10.2026: Startbeschreibung aus früherem Feedback übernommen.';
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
   await page.route(/\/Privat\/Pressespiegel\/data\/\d{4}-\d{2}-\d{2}\.json(?:\?.*)?$/,async route=>{
     const response=await route.fetch();
     const sample=await response.json();
     sample.articles[0].related_article={title:'Independent follow-up',source:'Another publisher',url:'https://example.org/follow-up'};
     // Synthetic, explicitly independent opposing source (browser test only).
     sample.articles[0].counterposition={
       responds_to:'The main commentary argues that taxing wealthy residents cannot be designed efficiently.',
       argument:'A separately sourced economic analysis instead finds that tax incidence, avoidance and administrative design can materially alter the effect, so universal claims are not warranted.',
       source:'Independent Institute',source_title:'Evidence on tax design and economic behaviour',
       url:'https://evidence.example.org/independent-analysis',evidence_level:'read'
     };
     sample.preview=false; // Synthetic real-edition correction fixture.
     // Synthetic Neues example: tested only, NEVER written to public edition.
     if(sample.date===latestFixtureDay&&sample.articles.length>=3){
       sample.articles.at(-2).new_perspective='A source-based counterintuitive link between productive innovation and public policy.';
       sample.articles.at(-1).new_perspective='A documented unconventional perspective on familiar economic trade-offs and institutions.';
     }
     sample.articles[0].correction={
       corrected_at:'2026-10-29T12:00:00+01:00',
       previous_summary:'Falsche ursprüngliche Zusammenfassung',
       note:'Eine unzutreffende Behauptung wurde berichtigt.',
       source_url:'https://example.org/evidence'
     };
     await route.fulfill({response,json:sample});
   });
   await page.route('https://raw.githubusercontent.com/**/blogs-live/**',async route=>{
     const payload=JSON.parse(fs.readFileSync('Privat/Pressespiegel/data/blogs.json','utf8'));
     // Simulate a retained RSS archive with 28 posts, including guest authors.
     payload.posts=payload.posts.slice(0,5);
     // Test-only 108-word fixture, never published.
     const fixtureText=Array.from({length:12},
       ()=> 'The article examines economic mechanisms and describes practical tradeoffs.'
     ).join(' ');
     payload.posts[0].summary_text=fixtureText;
     payload.posts[0].summary_source='article';
     payload.posts[0].summary_language='en';
     payload.posts[0].summary_access='visible_text_only';
     payload.posts[0].summary_generated_at='2026-11-06T12:00:00+01:00';
     payload.posts[0].summary_evidence_url=payload.posts[0].url;
     for(let n=5;n<28;n++)payload.posts.push({
       title:'Older Noahpinion entry '+n,
       url:'https://www.noahpinion.blog/p/test-archive-'+n,
       published_at:'2026-10-20',
       author:n%2?'Guest Contributor':'Noah Smith',
       description:'Feed summary for item '+n
     });
     await route.fulfill({status:200,json:payload});
   });
   const root=(process.env.PREVIEW_URL||'http://127.0.0.1:8766')+'/Privat/Pressespiegel/';
   await page.goto(root);
   await page.waitForSelector('#feedback-section:not([hidden])');
   assert.equal(await page.locator('.value-proposition').count(),0,'Classic reader has no promotional introduction');
   assert.doesNotMatch(await page.locator('#publication-status').innerText(),/Archivierte Beispielausgabe|keine neue Recherche|kein Nachweis für das neue Lernkonzept/);
   assert.equal(await page.locator('#feedback').isVisible(),true,'Open feedback is always visible');
   await page.locator('#tab-blogs').click();
   await page.waitForSelector('#blogs .blog-entry');
   assert.equal(await page.locator('#blogs .blog-entry').count(),5);
   assert.match(await page.locator('#blogs .blog-entry').first().locator('.blog-description').innerText(),
     /economic mechanisms/,'Article-checked English summary is displayed');
   assert.equal(await page.locator('#blogs .blog-entry').first().locator('.blog-summary').getAttribute('lang'),'en');
   assert.match(await page.locator('#blogs .blog-entry').first().locator('.blog-summary-origin').innerText(),/Redaktionelle Zusammenfassung/);
   assert.match(await page.locator('#blogs .blog-entry').nth(1).locator('.blog-summary-origin').innerText(),/RSS-Auszug/);
   assert.equal(await page.locator('#blogs .blog-entry').nth(1).locator('.blog-summary').count(),0,
     'Unverified RSS excerpt must not be called article summary');
   const firstBlogUrl=await page.locator('#blogs .blog-entry h3 a').first().getAttribute('href');
   const cross=page.locator('#blogs .blog-delete').first();
   assert.equal(await cross.locator('svg path').count(),1,'Delete is a centered SVG icon, not a font glyph');
   const buttonBox=await cross.boundingBox(),iconBox=await cross.locator('svg').boundingBox();
   assert.ok(Math.abs((buttonBox.x+buttonBox.width/2)-(iconBox.x+iconBox.width/2))<1,'X is horizontally centered');
   assert.ok(Math.abs((buttonBox.y+buttonBox.height/2)-(iconBox.y+iconBox.height/2))<1,'X is vertically centered');
   await cross.click();
   assert.equal(await page.locator('#blogs .blog-entry').count(),5,'Deleted post is replaced by next visible post');
   assert.notEqual(await page.locator('#blogs .blog-entry h3 a').first().getAttribute('href'),firstBlogUrl);
   const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem('pressespiegel:deleted-blog-posts:v1')));
   assert.equal(stored.length,1,'Deleted article persists locally');
   await page.locator('#blog-trash-open').click();
   assert.equal(await page.locator('#blog-trash-dialog').isVisible(),true);
   assert.equal(await page.locator('#blog-trash-list .blog-trash-entry').count(),1);
   await page.locator('#blog-trash-list .blog-restore').click();
   assert.equal(await page.locator('#blogs .blog-entry h3 a').first().getAttribute('href'),firstBlogUrl,'Restoring preserves original feed order');
   assert.equal(await page.locator('#blog-trash-list .blog-trash-entry').count(),0);
   await page.locator('#blog-trash-close').click();
   assert.equal(await page.locator('#blogs .blog-more').count(),1);
   await page.locator('#blogs .blog-more').click();
   assert.equal(await page.locator('#blogs .blog-entry').count(),15);
   await page.locator('#blogs .blog-more').click();
   assert.equal(await page.locator('#blogs .blog-entry').count(),25);
   await page.locator('#blogs .blog-more').click();
   assert.equal(await page.locator('#blogs .blog-entry').count(),28);
   assert.equal(await page.locator('#blogs .blog-more').count(),0,'No more button after archive end');
   assert.equal(await page.locator('#blogs .rating-dots').count(),0,'Blogs must never have article ratings');
   assert.equal(await page.locator('#feedback-section').isVisible(),false,'Blogs have no feedback controls');
   assert.equal(await page.locator('#blogs .blog-entry a').first().getAttribute('href'),'https://www.noahpinion.blog/p/anthropics-moat-is-claude');
   await page.locator('#tab-headlines').click();
   assert.equal(await page.locator('#feedback-section').isVisible(),true,'Newspaper ratings remain available');
   await page.locator('#tab-blogs').click();
   assert.equal(await page.locator('#blogs .blog-entry').count(),28,'Expanded archive persists across tabs');
   await page.locator('#blogs .blog-delete').first().click();
   assert.equal(await page.locator('#blogs .blog-entry').count(),27);
   assert.equal(await page.locator('#blogs .blog-more').count(),0,'Deletion does not reset expanded list');
   await page.locator('#tab-headlines').click();
   await page.locator('#tab-blogs').click();
   assert.equal(await page.locator('#blogs .blog-entry').count(),27,'Deleted state and expansion persist across tabs');
   await page.reload();
   await page.locator('#tab-blogs').click();
   await page.waitForSelector('#blogs .blog-entry');
   assert.equal(await page.locator('#blogs .blog-entry').count(),5,'Deletion persists across a reload');
   await page.locator('#blog-trash-open').click();
   assert.equal(await page.locator('#blog-trash-list .blog-trash-entry').count(),1);
   await page.locator('#blog-trash-list .blog-restore').click();
   await page.locator('#blog-trash-close').click();
   assert.equal(await page.locator('#blogs .blog-entry h3 a').first().getAttribute('href'),firstBlogUrl,'Restored post returns to original order on reload');

   await page.locator('#tab-headlines').click();
   assert.ok(await page.locator('.feedback-suggestions button').count()>=4);
   const suggestion=await page.locator('.feedback-suggestions button').first().innerText();
   await page.locator('.feedback-suggestions button').first().click();
   const general=page.locator('#feedback');
   await general.fill((await general.inputValue())+'\nFreie eigene Begründung zur Artikelwahl.');
   assert.match(await general.inputValue(),/Thema interessiert/);
   await page.locator('#tab-articles').click();
   assert.equal(await page.locator('#articles').isVisible(),true);
   const published=JSON.parse(fs.readFileSync('Privat/Pressespiegel/data/'+latestFixtureDay+'.json','utf8'));
   assert.equal(await page.locator('#neues').isVisible(),true,'Neues appears only with editorial selections');
   assert.equal(await page.locator('#neues > h2').innerText(),'Neues');
   assert.equal(await page.locator('#neues article').count(),2,'Only the selected two articles appear under Neues');
   assert.equal(await page.locator('#articles article').count(),published.articles.length,'No duplicated or lost article');
   assert.equal(await page.locator('#articles > .lead-grid article, #articles > .article-list article').count(),published.articles.length-2,
     'Neues items must not reappear in the ordinary article list');
   assert.equal(await page.locator('#neues article .new-perspective-rationale').count(),2);
   assert.equal(await page.locator('#neues').evaluate(el=>el.nextElementSibling.classList.contains('section-save')),true,
     'Neues must be at the END of Vertiefungen, before the shared save button');
   const firstNovelId=await page.locator('#neues article').first().getAttribute('data-article-id');
   assert.equal(await page.locator('#neues article').first().getAttribute('data-section'),'Vertiefungen');
   assert.equal(await page.locator('#articles .article-correction').count(),1);
   assert.match(await page.locator('#articles .article-correction').innerText(),/unzutreffende Behauptung wurde berichtigt/);
   assert.equal(await page.getByRole('link',{name:'Beleg zur Berichtigung'}).getAttribute('href'),'https://example.org/evidence');
   await page.locator('#articles .correction-history summary').first().click();
   assert.equal(await page.getByText('Falsche ursprüngliche Zusammenfassung').count(),1);
   assert.equal(await page.getByText('Weiterer Beitrag zum Thema:').count(),1,'Related reporting is separately marked');
   assert.equal(await page.getByRole('link',{name:'Independent follow-up'}).getAttribute('href'),'https://example.org/follow-up');
   const opposing=page.locator('#articles article').first().locator('.article-counterposition');
   assert.equal(await opposing.count(),1,'Only one counterposition is shown under its parent article');
   assert.equal(await opposing.locator('h3').innerText(),'Eine andere Perspektive');
   assert.match(await opposing.innerText(),/tax incidence, avoidance and administrative design/);
   assert.equal(await opposing.locator('a').getAttribute('href'),'https://evidence.example.org/independent-analysis');
   assert.equal(await opposing.evaluate(el=>el.nextElementSibling.classList.contains('ratings')),true,
     'Contrary source must appear below the article but directly before the single rating');
   assert.equal(await page.locator('#articles .article-counterposition').count(),1,
     'No detached second article or extra rating created');
   const correctedId=await page.locator('#articles article').first().getAttribute('data-article-id');
   const group=page.locator('#articles .ratings').first();
   await group.locator('input[type=radio][value="Sehr relevant"]').check();
   await page.locator('#neues article .ratings').first()
     .locator('input[type=radio][value="Teilweise relevant"]').check();
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
   assert.ok(payload.ratings.some(r=>r.id===firstNovelId&&r.section==='Vertiefungen'&&r.rating==='Teilweise relevant'),
     'Neues feedback must persist under original article ID and same Vertiefungen section');
   assert.deepEqual(payload.comment_suggestions,[suggestion]);
   assert.ok(payload.comment.includes('Freie eigene Begründung zur Artikelwahl.'));
   assert.ok(payload.ratings.some(r=>r.suggested_reasons?.includes('Zu juristisch für ein Randthema')));
   // Older genuine editions lack the optional Neues markers; no empty section.
   const older=JSON.parse(fs.readFileSync('Privat/Pressespiegel/data/index.json','utf8')).dates[1];
   await page.locator('#date').selectOption(older);
   await page.waitForFunction(date=>{
     const formatted=new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'})
       .format(new Date(date+'T12:00:00Z'));
     return document.querySelector('#edition-meta').textContent.includes(formatted)&&!document.querySelector('#neues');
   },older);
   assert.equal(await page.locator('#neues').count(),0,'Historical editions without markers show no Neues section');
   assert.equal(await page.locator('#articles .article-counterposition').count(),0,
     'Historical issues without counterposition metadata show no stray alternative boxes');
   await page.locator('#date').selectOption(latestFixtureDay);
   await page.waitForSelector('#neues');
   assert.equal(await page.locator('#neues article').count(),2,'Switching back restores exactly the selected items');
   assert.equal(await page.locator('#articles .article-counterposition').count(),1,
     'Returning to the latest edition re-creates just the original linked counterposition');
   await page.getByRole('link',{name:/Meine Präferenzen/}).first().click();
   await page.waitForURL(/praeferenzen.html/);
   await page.waitForSelector('#profile-text:not([hidden])');
   assert.match(await page.locator('#profile-text').innerText(),/wirtschaftliche Erkenntnisse/);
   assert.ok((await page.locator('#profile-changes').innerText()).includes('Startbeschreibung'));
   assert.equal(await page.locator('#preference-comment').isVisible(),true);
   await page.waitForFunction(()=>!document.querySelector('#learning-monitor').textContent.includes('geladen'));
   assert.match(await page.locator('#learning-monitor').innerText(),
     width===390?/Noch keine Lernbilanz vorhanden/:/Noch nicht beurteilbar/);
   assert.equal(await page.locator('#learning-monitor').isVisible(),true);

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
   // Prior release stored hidden URL paths under a different localStorage key.
   // The restored selection must survive upgrading to the new independent dialog.
   await page.evaluate(()=>{
     localStorage.removeItem('pressespiegel:deleted-blog-posts:v1');
     localStorage.setItem('pressespiegel-hidden-blog-posts-v1',JSON.stringify(['/p/anthropics-moat-is-claude']));
   });
   await page.goto(root);
   await page.locator('#tab-blogs').click();
   await page.waitForSelector('#blogs .blog-entry');
   assert.notEqual(await page.locator('#blogs .blog-entry h3 a').first().getAttribute('href'),
     'https://www.noahpinion.blog/p/anthropics-moat-is-claude','Legacy hidden posts must stay hidden');
   await page.locator('#blog-trash-open').click();
   assert.equal(await page.locator('#blog-trash-list .blog-trash-entry').count(),1,'Old hidden list migrates');
   await page.locator('#blog-trash-list .blog-restore').click();
   await page.locator('#blog-trash-close').click();
   assert.equal(await page.locator('#blogs .blog-entry h3 a').first().getAttribute('href'),
     'https://www.noahpinion.blog/p/anthropics-moat-is-claude','Legacy hide can be restored');
   await page.reload();
   await page.locator('#tab-blogs').click();
   await page.waitForSelector('#blogs .blog-entry');
   assert.equal(await page.locator('#blogs .blog-entry h3 a').first().getAttribute('href'),
     'https://www.noahpinion.blog/p/anthropics-moat-is-claude','Legacy state is not imported twice');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'No horizontal overflow');
   assert.deepEqual(errors,[],'No JS page errors');
   await context.close();
  }
 }finally{await browser.close();}
 console.log('PASS: 390px and 1440px classic reader, review codes, open feedback and private description');
})().catch(err=>{console.error(err);process.exitCode=1;});
