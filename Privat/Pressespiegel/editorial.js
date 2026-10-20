/* Shared editorial rules: news and in-depth reports must never repeat the same item. */
'use strict';
const PaperEditorial=(()=>{
  const IGNORED=new Set(['der','die','das','dem','den','des','ein','eine','einen','einer','und','oder','von','mit','auf','für','über','aber','nach','aus','bei','mehr','noch','sich','jetzt','auch','wird','werden','nicht','schon','dass']);
  function canonical(url){
    const u=new URL(url);
    if(u.protocol!=='https:'||u.username||u.password)throw Error('Ungültige Artikel-URL');
    u.hash='';
    u.pathname=u.pathname.replace(/\/+$/,'')||'/';
    for(const key of [...u.searchParams.keys()]){
      if(/^utm_/i.test(key)||['fbclid','gclid','mc_cid','mc_eid'].includes(key.toLowerCase()))u.searchParams.delete(key);
    }
    u.searchParams.sort();
    return u.href;
  }
  function words(value){
    return new Set(String(value||'').toLowerCase().replace(/[^a-zäöüß0-9]+/g,' ').split(/\s+/).filter(x=>x.length>=4&&!IGNORED.has(x)));
  }
  function closeTitle(a,b){
    const x=words(a),y=words(b);
    if(x.size<2||y.size<2)return String(a||'').trim().toLowerCase()===String(b||'').trim().toLowerCase();
    const common=[...x].filter(k=>y.has(k)).length;
    const ratio=common/Math.max(x.size,y.size);
    return common>=2&&ratio>=0.75;
  }
  function sameStory(a,b){
    if(canonical(a.url)===canonical(b.url))return true;
    if(a.event&&b.event&&a.event===b.event)return true;
    return closeTitle(a.title,b.title);
  }
  function uniqueNews(edition){
    const selected=edition.articles||[];
    const news=[],removed=[];
    for(const item of edition.headlines||[]){
      if([...selected,...news].some(other=>sameStory(item,other)))removed.push(item);
      else news.push(item);
    }
    return {news,removed};
  }
  async function stableId(url,cryptoAPI=crypto){
    const buf=await cryptoAPI.subtle.digest('SHA-256',new TextEncoder().encode(canonical(url)));
    return [...new Uint8Array(buf)].map(n=>n.toString(16).padStart(2,'0')).join('').slice(0,16);
  }
  async function prepare(edition,cryptoAPI=crypto){
    const {news,removed}=uniqueNews(edition);
    const headlines=await Promise.all(news.map(async h=>({
      ...h,id:/^[a-f0-9]{16,24}$/.test(h.id||'')?h.id:await stableId(h.url,cryptoAPI)
    })));
    return {...edition,headlines,duplicateHeadlinesRemoved:removed.length};
  }
  return {canonical,closeTitle,sameStory,uniqueNews,stableId,prepare};
})();
if(typeof module!=='undefined')module.exports=PaperEditorial;
