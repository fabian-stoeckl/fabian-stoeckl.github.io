'use strict';
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage();
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://**/*',r=>r.abort());
  const root=(process.env.PREVIEW_URL||'http://127.0.0.1:8766')+'/Privat/Pressespiegel/';
  await page.goto(root);
  await page.waitForSelector('#feedback-section:not([hidden])');
  await page.evaluate(async()=>{
   const story=readerState.visibleArticles[0],key=draftKey(story);
   const row={id:story.id,value:'',reason:'Saved reason only',section:'Vertiefungen',reason_codes:[],suggested_reasons:[]};
   readerState.ratingBaselines[key]=row;
   readerState.ratingDrafts[key]={...row,dirty:false};
   render();
  });
  await page.locator('#tab-articles').click();
  await page.locator('#articles .ratings textarea').first().fill('');
  const rows=await page.evaluate(()=>collectDraftRatings(edition.date,[[readerState.visibleArticles,'Vertiefungen']]));
  assert.equal(rows.length,1,'Deleting the last reason must submit an empty replacement');
  assert.equal(rows[0].reason,'');assert.equal(rows[0].value,'');

  await page.goto(root+'praeferenzen.html');
  await page.evaluate(()=>{
   DirectFeedback.readToken=()=> 'mock-token';
   window.originalPaperJson=GitHubPaper.json;
   GitHubPaper.json=async()=>({dates:['2026-11-04']});
   window.submissions=[];
   DirectFeedback.appendComment=async(...args)=>{
    window.submissions.push(args);
    return new Promise(resolve=>{window.finishSave=resolve;});
   };
   DirectFeedback.feedbackHistory=async()=>[];
  });
  await page.locator('#preference-comment').fill('First submitted thought');
  await page.locator('#preference-comment-form button[type=submit]').click();
  await page.waitForFunction(()=>window.submissions.length===1);
  await page.locator('#preference-comment').fill('New thought while saving');
  await page.evaluate(()=>document.querySelector('#preference-comment-form').requestSubmit());
  assert.equal(await page.evaluate(()=>window.submissions.length),1,'One in-flight save per form');
  await page.evaluate(()=>window.finishSave({ok:true}));
  await page.waitForFunction(()=>document.querySelector('#preference-comment-status').textContent.startsWith('Gespeichert'));
  assert.equal(await page.locator('#preference-comment').inputValue(),'New thought while saving',
   'Confirmed earlier save must not erase a newer unsent draft');
  const timeoutResult=await page.evaluate(async()=>{
   const originalTimeout=AbortSignal.timeout.bind(AbortSignal),originalFetch=window.fetch;
   AbortSignal.timeout=()=>originalTimeout(20);
   const hanging=(_url,options)=>new Promise((_resolve,reject)=>{
    if(!options.signal){reject(Error('Missing abort signal'));return;}
    options.signal.addEventListener('abort',()=>reject(options.signal.reason),{once:true});
   });
   try{
    window.fetch=hanging;
    GitHubPaper.json=window.originalPaperJson;
    // The unmocked backend verification and an edition fetch must settle.
    const results=await Promise.allSettled([
     DirectFeedback.verify('mock-token',hanging),
     GitHubPaper.edition('2026-11-04')
    ]);
    return results.map(r=>({status:r.status,name:r.reason?.name}));
   }finally{AbortSignal.timeout=originalTimeout;window.fetch=originalFetch;}
  });
  assert.deepEqual(timeoutResult[1],{status:'rejected',name:'TimeoutError'});
  assert.deepEqual(timeoutResult[0],{status:'rejected',name:'TimeoutError'});
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
 console.log('PASS: reason-only removal, concurrent preference submits and in-flight draft preservation');
})().catch(e=>{console.error(e);process.exitCode=1;});
