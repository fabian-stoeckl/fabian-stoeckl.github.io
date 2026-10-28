/* Editions, deduplicated sections and unified feedback payload. */
'use strict';
const GitHubPaper = {
  canonical(url) {
    const u=new URL(url);
    if(u.protocol!=='https:'||u.username||u.password)throw Error('Ungültige Artikeladresse');
    const query=[...u.searchParams.entries()].filter(([key])=>!key.startsWith('utm_')&&!['fbclid','gclid'].includes(key)).sort(([a,av],[b,bv])=>a.localeCompare(b)||av.localeCompare(bv));
    const tail=query.length?'?'+new URLSearchParams(query):'';
    return 'https://'+u.host.toLowerCase()+u.pathname.replace(/\/+$/,'')+tail;
  },
  partition(edition) {
    const articles=Array.isArray(edition.articles)?edition.articles:[];
    const news=Array.isArray(edition.headlines)?edition.headlines:[];
    // Only exact canonical duplicate URLs are hidden at presentation time.
    // Editorially distinct articles about one event, or similar headlines
    // from other publishers, must never be silently removed by the reader.
    const seen=new Set(articles.map(a=>this.canonical(a.url)));
    const headlines=[];
    for(const item of news){
      const url=this.canonical(item.url);
      if(seen.has(url))continue;
      seen.add(url);
      headlines.push(item);
    }
    return {articles,headlines,duplicatesRemoved:news.length-headlines.length};
  },
  async ratingId(entry) {
    if(/^[a-f0-9]{16}$/.test(entry.id||''))return entry.id;
    const bytes=new TextEncoder().encode(this.canonical(entry.url));
    const digest=await crypto.subtle.digest('SHA-256',bytes);
    return [...new Uint8Array(digest)].slice(0,8).map(v=>v.toString(16).padStart(2,'0')).join('');
  },
  async json(path) {
    const r = await fetch(path, {cache:'no-store'});
    if (!r.ok) throw Error('Ausgabe nicht erreichbar (' + r.status + ')');
    return r.json();
  },
  async edition(date) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw Error('Ungültiges Ausgabedatum');
    const data = await this.json('./data/' + date + '.json');
    if (data.date !== date) throw Error('Ausgabe und Datum stimmen nicht überein');
    return data;
  }
};
if (typeof module !== 'undefined') module.exports = GitHubPaper;
