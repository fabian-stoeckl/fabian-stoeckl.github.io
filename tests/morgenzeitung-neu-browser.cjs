'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  for(const width of [390,1440]){
   const context=await browser.newContext({viewport:{width,height:900}});
   const page=await context.newPage(),errors=[];
   const issues=[];
   let overrideLatestDate=null;
   let holdIssueRead=false,releaseHeldRead=null,notifyHeldRead=null;
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
     // Snapshot at GET initiation; a late reply can be older than the issue.
     const snapshot=JSON.parse(JSON.stringify(issues));
     if(holdIssueRead){
      holdIssueRead=false; // only this request is deliberately held
      notifyHeldRead?.();
      await new Promise(resolve=>{releaseHeldRead=resolve;});
     }
     response=snapshot;
    }else{
     response={private:true,full_name:'fabian-stoeckl/morgenzeitung-feedback'};
    }
    await route.fulfill({status:200,json:response});
   });
   await page.route(/\/Privat\/Pressespiegel\/data\/index\.json(?:\?.*)?$/,async route=>{
    const response=await route.fetch(),data=await response.json();
    if(overrideLatestDate)data.dates=[overrideLatestDate,...data.dates.filter(d=>d!==overrideLatestDate)];
    await route.fulfill({response,json:data});
   });
   await page.route(/\/Privat\/Pressespiegel\/data\/\d{4}-\d{2}-\d{2}\.json(?:\?.*)?$/,async route=>{
     const response=await route.fetch();
     const sample=await response.json();
     sample.articles[0].related_article={title:'Independent follow-up',source:'Another publisher',url:'https://example.org/follow-up'};
     sample.preview=false; // Synthetic real-edition correction fixture.
     sample.new_topics=[{name:'New research area',why:'Previously overlooked question and original evidence',example_url:'https://example.org/topic'}];
     sample.new_sources=[{name:'Independent specialist source',why:'Different original dataset',example_url:'https://example.org/source'}];
     sample.articles[0].alternative_view={title:'A substantial alternative argument',
       source:'Independent analysis',url:'https://example.org/counter',why:'Tests a disputed causal mechanism'};
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
   await page.locator('#tab-discoveries').click();
   assert.equal(await page.locator('#discoveries').isVisible(),true);
   assert.equal(await page.locator('#discovery-count').innerText(),'2');
   assert.equal(await page.locator('#discoveries .source-trials li').count(),2);
   assert.doesNotMatch(await page.locator('#discoveries').innerText(),/A substantial alternative argument/);
   assert.equal(await page.locator('#feedback-section').isVisible(),false,'Read-only discovery tab does not post synthetic ratings');
   await page.locator('#tab-headlines').click();
   assert.equal(await page.locator('#feedback-section').isVisible(),true,'Returning to articles restores normal feedback');
   await page.locator('#tab-blogs').click();
   await page.waitForSelector('#blogs .blog-entry');
   assert.equal(await page.locator('#blogs .blog-entry').count(),5);
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
   await page.locator('#tab-headlines').click();
   assert.ok(await page.locator('.feedback-suggestions button').count()>=4);
   const suggestion=await page.locator('.feedback-suggestions button').first().innerText();
   await page.locator('.feedback-suggestions button').first().click();
   const general=page.locator('#feedback');
   await general.fill((await general.inputValue())+'\nFreie eigene Begründung zur Artikelwahl.');
   assert.match(await general.inputValue(),/Thema interessiert/);
   await page.locator('#tab-articles').click();
   assert.equal(await page.locator('#articles').isVisible(),true);
   assert.equal(await page.locator('#articles .article-correction').count(),1);
   assert.equal(await page.locator('#articles .alternative-view').count(),1);
   assert.match(await page.locator('#articles .alternative-view').innerText(),/A substantial alternative argument/);
   assert.equal(await page.locator('#headlines .alternative-view').count(),0,'Counterarguments are only attached to deep dives');
   assert.match(await page.locator('#articles .article-correction').innerText(),/unzutreffende Behauptung wurde berichtigt/);
   assert.equal(await page.getByRole('link',{name:'Beleg zur Berichtigung'}).getAttribute('href'),'https://example.org/evidence');
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
   const noteOnlyArticle=page.locator('#articles article').nth(1);
   const noteOnlyId=await noteOnlyArticle.getAttribute('data-article-id');
   await noteOnlyArticle.locator('.rating-reason textarea').fill('Bitte hier mehr konkrete wirtschaftliche Folgen erklären.');
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
   assert.ok(payload.ratings.some(r=>r.id===noteOnlyId&&r.rating===''&&
     r.reason==='Bitte hier mehr konkrete wirtschaftliche Folgen erklären.'),
     'Qualitative-only article text is saved without falsely choosing a relevance level');
   // A clicked phrase is a suggested reason only while it is retained
   // verbatim on its own line. Rewriting it as original prose removes the
   // provenance tag instead of misclassifying the user's words as a click.
   await group.locator('.rating-reason textarea').fill(
     'Eigene Formulierung: Zu juristisch für ein Randthema gilt hier nur als Teil eines eigenen Satzes.');
   await page.locator('#feedback-form button[type=submit]').click();
   await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('aktualisiert.'));
   const rewritten=JSON.parse(issues[0].body.slice(issues[0].body.indexOf('\n')+1));
   const rewrittenRow=rewritten.ratings.find(r=>r.id===correctedId);
   assert.ok(rewrittenRow.reason.includes('Zu juristisch für ein Randthema'));
   assert.ok(!rewrittenRow.suggested_reasons?.includes('Zu juristisch für ein Randthema'),
     'Rewritten free prose must not retain a clicked-template marker');

   await page.getByRole('link',{name:/Meine Präferenzen/}).first().click();
   await page.waitForURL(/praeferenzen.html/);
   await page.waitForSelector('#profile-text:not([hidden])');
   assert.match(await page.locator('#profile-text').innerText(),/wirtschaftliche Erkenntnisse/);
   assert.ok((await page.locator('#profile-changes').innerText()).includes('Startbeschreibung'));
   assert.equal(await page.locator('#preference-comment').isVisible(),true);
   await page.waitForFunction(()=>document.querySelector('#feedback-summary').textContent.includes('qualitative Artikelhinweise'));
   assert.match(await page.locator('#feedback-summary').innerText(),
     /1 qualitative Artikelhinweise ohne Relevanzstufe/,
     'Qualitative-only article notes remain visible and are not counted as relevance votes');
   await page.waitForFunction(()=>!document.querySelector('#learning-monitor').textContent.includes('geladen'));
   assert.match(await page.locator('#learning-monitor').innerText(),
     width===390?/Noch keine Lernbilanz vorhanden/:/Noch nicht beurteilbar/);
   assert.equal(await page.locator('#learning-monitor').isVisible(),true);

   const prefSuggestion=await page.locator('.feedback-suggestions button').first().innerText();
   await page.locator('.feedback-suggestions button').first().click();
   const pref=page.locator('#preference-comment');
   await pref.fill((await pref.inputValue())+'\nEigenständiger Hinweis von der Präferenzseite.');
   await page.locator('#preference-comment-form button[type=submit]').click();
   await page.waitForFunction(()=>document.querySelector('#preference-comment-status').textContent.startsWith('Gespeichert'));
   const revised=JSON.parse(issues[0].body.slice(issues[0].body.indexOf('\n')+1));
   assert.deepEqual(revised.comment_suggestions,[suggestion]);
   assert.equal(prefSuggestion,suggestion);
   assert.ok(revised.comment.includes('Eigenständiger Hinweis von der Präferenzseite.'));
   // Submit again after a new edition appears while the preferences page stays open.
   overrideLatestDate='2026-11-05';
   await pref.fill('Rückmeldung nach neuer Ausgabe ohne Neuladen der Präferenzseite.');
   await page.locator('#preference-comment-form button[type=submit]').click();
   await page.waitForFunction(()=>document.querySelector('#preference-comment-status').textContent.includes('2026-11-05'));
   const newIssue=issues.find(i=>i.title.endsWith('2026-11-05'));
   assert.ok(newIssue,'The newest edition must receive the newly submitted preference comment');
   assert.match(newIssue.body,/Rückmeldung nach neuer Ausgabe ohne Neuladen/);
   assert.ok(!issues[0].body.includes('Rückmeldung nach neuer Ausgabe ohne Neuladen'),
     'A stale page-load date cannot contaminate the earlier edition');
   overrideLatestDate=null;
   // An empty unsent local draft survives changing to a different edition and back.
   await page.goto(root);
   await page.waitForSelector('#feedback-section:not([hidden])');
   await page.waitForFunction(()=>document.querySelector('#feedback').value.includes('Eigenständiger Hinweis von der Präferenzseite.'));
   // Delayed GitHub read: a fast relevance click must preserve the saved reason.
   let notifyRead;
   const readStarted=new Promise(resolve=>{notifyRead=resolve;});
   notifyHeldRead=notifyRead;
   holdIssueRead=true;
   await page.reload();
   await page.waitForSelector('#feedback-section:not([hidden])');
   await readStarted;
   await page.locator('#tab-articles').click();
   const earlyGroup=page.locator('#articles .ratings').first();
   await earlyGroup.locator('input[type=radio][value="Teilweise relevant"]').check();
   holdIssueRead=false;releaseHeldRead();
   await page.waitForFunction(()=>document.querySelector('#articles .ratings textarea').value.includes('Zu juristisch für ein Randthema'));
   assert.equal(await earlyGroup.locator('input[type=radio][value="Teilweise relevant"]').isChecked(),true);
   assert.match(await earlyGroup.locator('textarea').inputValue(),/Zu juristisch für ein Randthema/,
     'A quick radio click cannot clear the previously saved article reason');
   // Reverse race: writing only a new explanation must retain the already
   // selected relevance value until the delayed issue state arrives.
   let notifySecondRead;
   const secondReadStarted=new Promise(resolve=>{notifySecondRead=resolve;});
   notifyHeldRead=notifySecondRead;
   holdIssueRead=true;
   await page.reload();
   await page.waitForSelector('#feedback-section:not([hidden])');
   await secondReadStarted;
   await page.locator('#tab-articles').click();
   const reasonOnlyGroup=page.locator('#articles .ratings').first();
   await reasonOnlyGroup.locator('textarea').fill('Neue eigene Erläuterung.');
   holdIssueRead=false;releaseHeldRead();
   await page.waitForFunction(()=>document.querySelector('#articles .ratings input[type=radio][value="Sehr relevant"]').checked);
   assert.equal(await reasonOnlyGroup.locator('textarea').inputValue(),'Neue eigene Erläuterung.');
   assert.equal(await reasonOnlyGroup.locator('input[type=radio][value="Sehr relevant"]').isChecked(),true,
     'A quick explanation edit cannot clear the previously saved relevance value');
   await page.waitForFunction(()=>document.querySelector('#feedback').value.includes('Eigenständiger Hinweis von der Präferenzseite.'));
   const datePicker=page.locator('#date'),originalDate=await datePicker.inputValue();
   const secondDate=await datePicker.locator('option').nth(1).getAttribute('value');
   await page.locator('#feedback').fill('');
   await datePicker.selectOption(secondDate);
   await page.waitForFunction(day=>document.querySelector('#edition-meta').textContent.includes(
     new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'})
       .format(new Date(day+'T12:00:00Z'))),secondDate);
   await datePicker.selectOption(originalDate);
   await page.waitForFunction(day=>document.querySelector('#edition-meta').textContent.includes(
     new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'})
       .format(new Date(day+'T12:00:00Z'))),originalDate);
   assert.equal(await page.locator('#feedback').inputValue(),'',
     'Unsent intentional clearing survives an edition round trip');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'No horizontal overflow');
   // An older delayed response for date A must NOT replace a newer
   // canonical answer after A -> B -> A.
   const storedBody=JSON.parse(issues[0].body.slice(issues[0].body.indexOf('\n')+1));
   const targetRow=storedBody.ratings.find(r=>r.id===correctedId);
   assert.ok(targetRow,'Fixture must retain the first deep-dive rating');
   const oldRelevance=targetRow.rating;
   let notifyStaleRead;
   const staleReadStarted=new Promise(resolve=>{notifyStaleRead=resolve;});
   notifyHeldRead=notifyStaleRead;
   holdIssueRead=true;
   await page.reload();
   await page.waitForSelector('#feedback-section:not([hidden])');
   await staleReadStarted;
   targetRow.rating=oldRelevance==='Nicht relevant'?'Sehr relevant':'Nicht relevant';
   issues[0].body='MORGENZEITUNG_NEU_FEEDBACK_V1\n'+JSON.stringify(storedBody);
   issues[0].updated_at='2026-11-04T20:00:00Z';
   const first=await page.locator('#date').inputValue();
   const second=await page.locator('#date option').nth(1).getAttribute('value');
   await page.locator('#date').selectOption(second);
   await page.waitForFunction(day=>document.querySelector('#date').value===day&&
     document.querySelector('#edition-meta').textContent.includes(
       new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'})
       .format(new Date(day+'T12:00:00Z'))),second);
   await page.locator('#date').selectOption(first);
   await page.waitForFunction(day=>document.querySelector('#date').value===day&&
     document.querySelector('#edition-meta').textContent.includes(
       new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'})
       .format(new Date(day+'T12:00:00Z'))),first);
   await page.waitForFunction(value=>[...document.querySelectorAll('#articles .ratings input[type=radio]')]
     .some(n=>n.value===value&&n.checked),targetRow.rating);
   releaseHeldRead();
   await page.waitForTimeout(100);
   assert.equal(await page.locator('#articles .ratings').first()
     .locator('input[type=radio][value="'+targetRow.rating+'"]').isChecked(),true,
     'Stale reply from an earlier render cannot clobber newer saved relevance');

   // A remote change after a previous read must refresh clean baselines on
   // A -> B -> A. Otherwise the reader displays an up-to-date rating but
   // rejects legitimate edits because its conflict baseline is outdated.
   targetRow.rating='Teilweise relevant';
   storedBody.comment+='\nNeuer bestätigter Text von einem anderen Gerät.';
   issues[0].body='MORGENZEITUNG_NEU_FEEDBACK_V1\n'+JSON.stringify(storedBody);
   issues[0].updated_at='2026-11-04T20:15:00Z';
   await page.locator('#date').selectOption(second);
   await page.waitForFunction(d=>document.querySelector('#date').value===d&&
     document.querySelector('#edition-meta').textContent.includes(
       new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'})
       .format(new Date(d+'T12:00:00Z'))),second);
   await page.locator('#date').selectOption(first);
   await page.waitForFunction(text=>document.querySelector('#feedback').value===text,storedBody.comment);
   await page.waitForFunction(()=>document.querySelector('#articles .ratings input[type=radio][value="Teilweise relevant"]').checked);
   await page.locator('#tab-articles').click();
   const refreshedGroup=page.locator('#articles .ratings').first();
   await refreshedGroup.locator('input[type=radio][value="Sehr relevant"]').check();
   await page.locator('#feedback').fill(storedBody.comment+'\nNeue eigene Ergänzung nach erneutem Laden.');
   await page.locator('#feedback-form button[type=submit]').click();
   await page.waitForFunction(()=>/gespeichert\.|aktualisiert\.|bleiben im Tab erhalten\./.test(document.querySelector('#feedback-status').textContent));
   const crossDeviceStatus=await page.locator('#feedback-status').innerText();
   assert.match(crossDeviceStatus,/gespeichert\.|aktualisiert\./);
   const refreshedPayload=JSON.parse(issues[0].body.slice(issues[0].body.indexOf('\n')+1));
   assert.equal(refreshedPayload.ratings.find(r=>r.id===correctedId).rating,'Sehr relevant',
     'Editing a freshly restored rating must use the new remote baseline, not an old one');
   assert.match(refreshedPayload.comment,/Neue eigene Ergänzung nach erneutem Laden/,
     'A refreshed remote comment must remain editable without a false conflict');
   // Keep a clean fixture for the following invalid-rubric test.
   storedBody.comment=refreshedPayload.comment;
   targetRow.rating='Sehr relevant';

   // Explicitly deleting the original GitHub feedback must clear clean,
   // cached ratings/comments when the reader returns to the edition.
   const removedIssue=issues.splice(0,1)[0];
   assert.ok(removedIssue,'Expected feedback issue to test remote removal');
   await page.locator('#date').selectOption(second);
   await page.waitForFunction(d=>document.querySelector('#edition-meta').textContent.includes(
     new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'})
     .format(new Date(d+'T12:00:00Z'))),second);
   await page.locator('#date').selectOption(first);
   await page.waitForFunction(()=>document.querySelector('#feedback').value===''&&
     !document.querySelector('#articles .ratings input[type=radio]:checked'));
   assert.equal(await page.locator('#articles .ratings').first()
     .locator('input[type=radio]:checked').count(),0,
     'Deleted remote feedback must not remain selected locally');
   issues.unshift(removedIssue);
   await page.locator('#date').selectOption(second);
   await page.waitForFunction(d=>document.querySelector('#edition-meta').textContent.includes(
     new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'})
     .format(new Date(d+'T12:00:00Z'))),second);
   await page.locator('#date').selectOption(first);
   await page.waitForFunction(()=>document.querySelector('#articles .ratings input[type=radio][value="Sehr relevant"]').checked);

   // A well-formed but semantically wrong rubric must not hydrate the story.
   targetRow.section='Heute wichtig';
   issues[0].body='MORGENZEITUNG_NEU_FEEDBACK_V1\n'+JSON.stringify(storedBody);
   await page.reload();
   await page.waitForFunction(()=>document.querySelector('#feedback-status').textContent.includes('falsche Rubrik'));
   assert.match(await page.locator('#feedback-status').innerText(),/falsche Rubrik/);
   targetRow.section='Vertiefungen';
   issues[0].body='MORGENZEITUNG_NEU_FEEDBACK_V1\n'+JSON.stringify(storedBody);

   // Privacy control must actually remove the stored GitHub token.
   await page.goto(root);
   await page.waitForSelector('#github-connected:not([hidden])');
   await page.locator('#github-disconnect').click();
   assert.equal(await page.evaluate(()=>localStorage.getItem('morgenzeitung:github-token:v1')),
     null,'Disconnect must clear the token from this device');
   assert.equal(await page.locator('#github-setup').isVisible(),true);
   assert.deepEqual(errors,[],'No JS page errors');
   await context.close();
  }
 }finally{await browser.close();}
 console.log('PASS: 390px and 1440px classic reader, review codes, open feedback and private description');
})().catch(err=>{console.error(err);process.exitCode=1;});
