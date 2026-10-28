'use strict';
// One offline browser journey. No requests to real GitHub or article publishers.
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 const context=await browser.newContext({viewport:{width:390,height:800}});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',err=>errors.push(err.message));
 await page.addInitScript(()=>{
   localStorage.setItem('morgenzeitung:github-token:v1','github_pat_V3_FAKE_LOCAL_TEST_ONLY_123456789');
   const original=window.fetch.bind(window);
   window.fetch=async(url,opts={})=>{
     const endpoint=String(url);
     const root='https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback';
     if(!endpoint.startsWith(root))return original(url,opts);
     const path=endpoint.slice(root.length);
     const method=opts.method||'GET';
     let result;
     if(path==='')result={full_name:'fabian-stoeckl/morgenzeitung-feedback',private:true};
     else if(method==='GET'&&path.startsWith('/issues?')){
       const saved=JSON.parse(sessionStorage.getItem('v3-mock-issue')||'null');
       result=saved?[saved]:[];
     }else if(method==='GET'&&path==='/issues/91'){
       result=JSON.parse(sessionStorage.getItem('v3-mock-issue')||'null');
     }else if((method==='POST'||method==='PATCH')&&/^\/issues(?:\/91)?$/.test(path)){
       const payload=JSON.parse(opts.body);
       const saved={...payload,number:91,updated_at:'2026-10-28T10:00:00Z',
         html_url:'https://github.com/fabian-stoeckl/morgenzeitung-feedback/issues/91'};
       sessionStorage.setItem('v3-mock-issue',JSON.stringify(saved));
       result=saved;
     }else throw Error('Unexpected private GitHub test request '+method+' '+endpoint);
     return new Response(JSON.stringify(result),{status:200,headers:{'Content-Type':'application/json'}});
   };
 });
 await page.goto('http://127.0.0.1:8766/Privat/Morgenzeitung-3/');
 await page.waitForSelector('#headlines .news-item .rating-dots input');
 assert.match(await page.locator('h1').first().innerText(),/Morgenzeitung/);
 assert.match(await page.locator('#publication-status').innerText(),/Beispielausgabe/);
 assert.equal(await page.locator('#github-connected').isHidden(),false);
 await page.locator('#headlines .news-item').first().getByLabel('Sehr relevant',{exact:true}).check();
 await page.locator('#tab-articles').click();
 await page.locator('#articles article').first().getByLabel('Nicht relevant',{exact:true}).check();
 await page.locator('#feedback-form button[type=submit]').click();
 await page.waitForFunction(()=>document.querySelector('#feedback-status')?.textContent.includes('erfolgreich'));
 const saved=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('v3-mock-issue')));
 assert.equal(saved.title,'[Morgenzeitung 3] Feedback 2026-10-27');
 assert.ok(saved.body.startsWith('MORGENZEITUNG_V3_FEEDBACK_V1\n'));
 const payload=JSON.parse(saved.body.split('\n').slice(1).join('\n'));
 assert.equal(payload.ratings.length,2);
 assert.deepEqual(payload.ratings.map(r=>r.rating).sort(),['Nicht relevant','Sehr relevant']);
 await page.goto('http://127.0.0.1:8766/Privat/Morgenzeitung-3/praeferenzen.html');
 await page.waitForFunction(()=>document.querySelector('#preference-feedback')?.textContent.includes('Artikelbewertungen'));
 assert.match(await page.locator('#preference-feedback').innerText(),/2 Artikelbewertungen/);
 assert.equal(errors.length,0,errors.join('\n'));
 await context.close();await browser.close();
 console.log('PASS V3 browser: mobile reader, both ratings, private API mock, preference history');
})().catch(e=>{console.error(e);process.exitCode=1;});
