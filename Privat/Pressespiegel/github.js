/* Editions, deduplicated sections and unified feedback payload. */
'use strict';
const GitHubPaper = {
  issueURL(repo, title, body) {
    if (!/^[A-Za-z0-9][A-Za-z0-9-]*\/[A-Za-z0-9_.-]+$/.test(repo || '')) throw Error('Privates Feedback-Repository noch nicht verbunden.');
    const url = new URL('https://github.com/' + repo + '/issues/new');
    url.searchParams.set('title', title);
    url.searchParams.set('body', body);
    return url.href;
  },
  ratingURL(repo, edition, article, value, reason) {
    return this.issueURL(repo, '[Morgenzeitung] ' + article.id + ': ' + value,
      'Typ: Bewertung\nAusgabe: ' + edition.date + '\nArtikel-ID: ' + article.id +
      '\nURL: ' + article.url + '\nBewertung: ' + value + '\nGrund: ' + (reason || '–') +
      '\n\nOptionales Feedback:\n');
  },
  batchBody(date, ratings, feedback) {
    const rows=ratings.map(r=>'Bereich: '+(r.section||'Vertiefungen')+'\nArtikel-ID: '+r.id+'\nBewertung: '+(r.value||'Keine Auswahl')+'\nBegründung: '+(r.reason||'–')+'\n');
    return 'Typ: Sammelbewertung\nAusgabe: '+date+'\n\n'+rows.join('\n')+'\n\nFeedback:\n'+feedback.trim();
  },
  canonical(url) {
    const u=new URL(url);
    if(u.protocol!=='https:'||u.username||u.password)throw Error('Ungültige Artikeladresse');
    const query=[...u.searchParams.entries()].filter(([key])=>!key.startsWith('utm_')&&!['fbclid','gclid'].includes(key)).sort(([a,av],[b,bv])=>a.localeCompare(b)||av.localeCompare(bv));
    const tail=query.length?'?'+new URLSearchParams(query):'';
    return 'https://'+u.host.toLowerCase()+u.pathname.replace(/\/+$/,'')+tail;
  },
  similarTitles(a,b) {
    const stop=new Set(['eine','einen','einer','einem','über','dies','sich','auch','werden','wurde','sind','wird','dass','nicht','nach','mehr']);
    const tokens=t=>new Set((t.toLowerCase().match(/[\p{L}\p{N}]{4,}/gu)||[]).filter(w=>!stop.has(w)));
    const x=tokens(a),y=tokens(b);
    if(x.size<2||y.size<2)return false;
    const shared=[...x].filter(w=>y.has(w)).length;
    return shared/Math.max(1,new Set([...x,...y]).size)>=0.65;
  },
  partition(edition) {
    const articles=Array.isArray(edition.articles)?edition.articles:[];
    const news=Array.isArray(edition.headlines)?edition.headlines:[];
    const seenUrls=new Set(articles.map(a=>this.canonical(a.url)));
    const seenEvents=new Set(articles.map(a=>a.event).filter(Boolean));
    const seenTitles=articles.map(a=>a.title);
    const headlines=[];
    for(const item of news){
      const url=this.canonical(item.url);
      if(seenUrls.has(url)||(item.event&&seenEvents.has(item.event))||seenTitles.some(t=>this.similarTitles(t,item.title)))continue;
      headlines.push(item);
      seenUrls.add(url);if(item.event)seenEvents.add(item.event);seenTitles.push(item.title);
    }
    return {articles,headlines,duplicatesRemoved:news.length-headlines.length};
  },
  async ratingId(entry) {
    if(/^[a-f0-9]{16}$/.test(entry.id||''))return entry.id;
    const bytes=new TextEncoder().encode(this.canonical(entry.url));
    const digest=await crypto.subtle.digest('SHA-256',bytes);
    return [...new Uint8Array(digest)].slice(0,8).map(v=>v.toString(16).padStart(2,'0')).join('');
  },
  parseBatchBody(body) {
    if(typeof body!=='string')throw Error('Vorheriges Feedback ist nicht lesbar.');
    const head=body.match(/^Typ: Sammelbewertung\nAusgabe: (\d{4}-\d{2}-\d{2})\n/);
    if(!head)throw Error('Vorheriges Feedback hat ein unerwartetes Format.');
    const feedbackTag='\nFeedback:\n';
    const end=body.indexOf(feedbackTag);
    if(end<0)throw Error('Im vorherigen Feedback fehlt der Abschlusstext.');
    const entryPart=body.slice(0,end);
    const rows=[];
    const re=/(?:Bereich: (Heute wichtig|Vertiefungen)\n)?Artikel-ID: ([a-f0-9]{16})\nBewertung: (Sehr relevant|Teilweise relevant|Nicht relevant|Keine Auswahl)\nBegründung: ([^\n]*)/g;
    let hit;
    while((hit=re.exec(entryPart))!==null)rows.push({section:hit[1]||'Vertiefungen',id:hit[2],value:hit[3]==='Keine Auswahl'?'':hit[3],reason:hit[4]==='–'?'':hit[4]});
    return {date:head[1],ratings:rows,feedback:body.slice(end+feedbackTag.length)};
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
