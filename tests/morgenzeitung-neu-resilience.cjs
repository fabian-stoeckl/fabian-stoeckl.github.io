'use strict';
/* Verify browser fallback when the independent blogs-live feed is unavailable. */
const assert=require('node:assert/strict');
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://raw.githubusercontent.com/**/blogs-live/**',r=>r.abort('failed'));
  const root=(process.env.PREVIEW_URL||'http://127.0.0.1:8766')+'/Privat/Pressespiegel/';
  await page.goto(root);
  await page.locator('#tab-blogs').click();
  await page.waitForSelector('#blogs .blog-entry',{timeout:10000});
  assert.equal(await page.locator('#blogs .blog-entry').count(),5,'Fallback shows last five known blog posts');
  assert.match(await page.locator('#blogs').innerText(),/letzte gespeicherte Liste/,'Fallback clearly labeled');
  assert.equal(await page.locator('#blogs .rating-dots').count(),0,'Blog posts have no ratings');
  assert.equal(await page.locator('#blogs .blog-more').count(),1,'Older cached posts can be expanded');
  await page.locator('#blogs .blog-more').click();
  assert.equal(await page.locator('#blogs .blog-entry').count(),15);
  assert.deepEqual(errors,[],'No uncaught browser errors in fallback');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
