'use strict';
// Standalone, read-only newspaper + explicit private GitHub feedback.
// No article URL probes, no analytics, no secret in the published repository.
(function(){
  const REPO='fabian-stoeckl/morgenzeitung-feedback';
  const TOKEN_KEY='morgenzeitung:github-token:v1'; // Existing device connection, if any.
  const API='https://api.github.com/repos/'+REPO;
  const RATING=['Sehr relevant','Teilweise relevant','Nicht relevant'];
  const $=id=>document.getElementById(id);
  let edition=null, dates=[], active='articles', draft={ratings:{},comment:''};
  function status(msg){$('status').textContent=msg;}
  function feedbackStatus(msg){$('save-status').textContent=msg;}
  function token(){try{return localStorage.getItem(TOKEN_KEY)||'';}catch(_){return '';}}
  function draftKey(){return 'mz-neu:draft:'+edition.date;}
  function readDraft(){try{const x=JSON.parse(localStorage.getItem(draftKey())||'{}');return {ratings:x.ratings&&typeof x.ratings==='object'?x.ratings:{},comment:typeof x.comment==='string'?x.comment:''};}catch(_){return {ratings:{},comment:''};}}
  function persist(){try{localStorage.setItem(draftKey(),JSON.stringify(draft));}catch(_){}}
  function dateLabel(date){return /^\d{4}-\d{2}-\d{2}$/.test(date)?date.split('-').reverse().join('.') : date;}
  function validUrl(url){try{const u=new URL(url);return u.protocol==='https:'?u.href:null;}catch(_){return null;}}
  function element(tag,cls,value){const n=document.createElement(tag);if(cls)n.className=cls;if(value!==undefined)n.textContent=String(value);return n;}
  function showList(){
    if(!edition)return;
    $('show-deep').setAttribute('aria-pressed',String(active==='articles'));
    $('show-news').setAttribute('aria-pressed',String(active==='headlines'));
    const list=edition[active]||[], container=$('entries');container.replaceChildren();
    for(const a of list){
      const article=element('article','entry');article.id='item-'+a.id;
      const by=element('div','byline');
      by.append(element('span','',a.source||'Quelle nicht angegeben'));
      if(a.topic)by.append(element('span','',a.topic));
      if(a.published_at){
        const when=new Date(a.published_at);
        if(!Number.isNaN(when.valueOf()))by.append(element('span','',new Intl.DateTimeFormat('de-AT',{dateStyle:'short',timeZone:'Europe/Vienna'}).format(when)));
      }
      article.append(by);
      const h=element('h2');
      const href=validUrl(a.url);
      if(href){const link=element('a','',a.title);link.href=href;link.target='_blank';link.rel='noopener noreferrer';h.append(link);}
      else h.textContent=a.title||'Ohne Titel';
      article.append(h);
      article.append(element('p','summary',a.summary||'Über den zugänglichen Titel hinaus liegen keine gesicherten Details vor.'));
      if(a.evidence==='headline')article.append(element('p','source-note','Einordnung nur auf Basis von Titel und öffentlich bekannten Metadaten.'));
      else if(a.evidence==='teaser')article.append(element('p','source-note','Zusammenfassung auf Basis des zugänglichen Vorspanns.'));
      const vote=element('div','vote');
      vote.setAttribute('role','group');vote.setAttribute('aria-label','Relevanz: '+a.title);
      vote.append(element('span','question','Für mich:'));
      for(const val of RATING){
        const label=element('label');
        const radio=document.createElement('input');radio.type='radio';radio.name='rating-'+a.id;radio.value=val;radio.checked=draft.ratings[a.id]===val;
        radio.addEventListener('change',()=>{draft.ratings[a.id]=val;persist();feedbackStatus('Bewertung vorgemerkt – zum Übertragen unten speichern.');});
        label.append(radio,document.createTextNode(val));vote.append(label);
      }
      article.append(vote);container.append(article);
    }
    if(!list.length)container.append(element('p','status','Für diese Rubrik liegen noch keine Artikel vor.'));
  }
  function validate(data){
    if(!data||data.date!==$('date').value||!Array.isArray(data.articles)||!Array.isArray(data.headlines))throw Error('Die Ausgabedaten sind unvollständig.');
    for(const a of [...data.articles,...data.headlines]){
      if(typeof a.id!=='string'||!a.title||!a.source||!validUrl(a.url))throw Error('Eine Artikelangabe ist ungültig.');
    }
    return data;
  }
  async function openDate(date){
    $('date').value=date;status('Ausgabe wird geladen …');
    try{
      const res=await fetch('./data/'+encodeURIComponent(date)+'.json',{cache:'no-store'});
      if(!res.ok)throw Error('Die Ausgabe ist nicht abrufbar.');
      edition=validate(await res.json());draft=readDraft();$('comment').value=draft.comment;
      $('deep-count').textContent=String(edition.articles.length);
      $('news-count').textContent=String(edition.headlines.length);
      $('learning').textContent=edition.learning_note||'Die Artikelwahl orientiert sich an den bisher ausdrücklich bewerteten Interessen. Unbewertete Artikel bleiben neutral.';
      const note=edition.editorial_note||'';
      status('Ausgabe '+dateLabel(date)+(note?' · '+note:''));
      feedbackStatus('');$('saved-link').hidden=true;showList();
    }catch(err){edition=null;status('Ausgabe nicht verfügbar: '+err.message);$('entries').replaceChildren();}
  }
  async function init(){
    $('show-deep').onclick=()=>{active='articles';showList();};
    $('show-news').onclick=()=>{active='headlines';showList();};
    $('date').addEventListener('change',()=>openDate($('date').value));
    $('comment').addEventListener('input',()=>{if(!edition)return;draft.comment=$('comment').value;persist();});
    $('connect').onclick=connect;$('disconnect').onclick=disconnect;$('save').onclick=save;
    $('connection-status').textContent=token()?'Ein früher verbundener GitHub-Schlüssel ist auf diesem Gerät gespeichert.':'Noch kein Schlüssel auf diesem Gerät eingerichtet.';
    try{
      const res=await fetch('./data/index.json',{cache:'no-store'});
      if(!res.ok)throw Error('Ausgabenverzeichnis nicht verfügbar');
      const j=await res.json();dates=(j.dates||[]).filter(d=>/^\d{4}-\d{2}-\d{2}$/.test(d)).sort().reverse();
      if(!dates.length)throw Error('Noch keine Ausgabe veröffentlicht');
      $('date').replaceChildren();
      dates.forEach(d=>{const o=document.createElement('option');o.value=d;o.textContent=dateLabel(d);$('date').append(o);});
      await openDate(dates[0]);
    }catch(err){status('Noch keine Ausgabe verfügbar: '+err.message);}
  }
  function connect(){
    const value=$('token').value.trim();
    if(!/^github_pat_[A-Za-z0-9_]{20,}$/.test(value)||!$('consent').checked){
      $('connection-status').textContent='Bitte eingeschränkten Fine-grained-Token und die Speicherbestätigung angeben.';return;
    }
    try{localStorage.setItem(TOKEN_KEY,value);$('token').value='';$('connection-status').textContent='Schlüssel lokal gespeichert. Beim nächsten Feedback wird die Verbindung geprüft.';$('connection').open=false;}
    catch(_){$('connection-status').textContent='Speichern im Browser nicht möglich.';}
  }
  function disconnect(){try{localStorage.removeItem(TOKEN_KEY);}catch(_){}$('connection-status').textContent='Der Schlüssel wurde auf diesem Gerät entfernt.';}
  async function gh(path,method='GET',body){
    const opts={method,headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+token(),'X-GitHub-Api-Version':'2022-11-28'},cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'};
    if(body!==undefined){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(body);}
    const res=await fetch(API+path,opts);
    if(!res.ok)throw Error('Privates GitHub-Feedback konnte nicht gespeichert werden (HTTP '+res.status+'). Bitte Verbindung prüfen.');
    return res.json();
  }
  function parse(body){
    const marker='MORGENZEITUNG_NEU_FEEDBACK_V1\n';
    if(typeof body!=='string'||!body.startsWith(marker))return null;
    try{const data=JSON.parse(body.slice(marker.length));return data&&typeof data.date==='string'&&Array.isArray(data.ratings)?data:null;}
    catch(_){return null;}
  }
  async function existingIssue(title){
    for(let page=1;page<=20;page++){
      const list=await gh('/issues?state=all&per_page=100&page='+page);
      const match=list.find(i=>!i.pull_request&&i.title===title&&parse(i.body));
      if(match)return match;
      if(list.length<100)break;
    }
    return null;
  }
  async function save(){
    if(!edition)return;
    const known=new Map([...edition.articles.map(a=>[a.id,'Vertiefungen']),...edition.headlines.map(a=>[a.id,'Heute wichtig'])]);
    const ratings=Object.entries(draft.ratings).filter(([id,rating])=>known.has(id)&&RATING.includes(rating)).map(([id,rating])=>({id,section:known.get(id),rating}));
    const comment=draft.comment.trim();
    if(!ratings.length&&!comment){feedbackStatus('Bitte mindestens einen Artikel bewerten oder einen Wunsch schreiben.');return;}
    if(!token()){feedbackStatus('Für das private Speichern bitte einmalig den GitHub-Zugang unten verbinden.');$('connection').open=true;return;}
    $('save').disabled=true;feedbackStatus('Feedback wird privat gespeichert …');
    try{
      const repo=await gh('');
      if(repo.full_name!==REPO||repo.private!==true)throw Error('Das Ziel ist kein verifiziertes privates Repository.');
      const title='[Morgenzeitung neu] Feedback '+edition.date;
      const prev=await existingIssue(title);
      const earlier=prev?parse(prev.body):null;
      const combined=new Map((earlier?.ratings||[]).filter(x=>known.has(x.id)&&RATING.includes(x.rating)).map(x=>[x.id,x]));
      for(const r of ratings)combined.set(r.id,r);
      const payload={version:1,date:edition.date,ratings:[...combined.values()],comment:comment||earlier?.comment||'',origin:'website-explicit'};
      const result=await gh(prev?'/issues/'+prev.number:'/issues',prev?'PATCH':'POST',{
        title,body:'MORGENZEITUNG_NEU_FEEDBACK_V1\n'+JSON.stringify(payload,null,2)
      });
      if(!result.number||result.title!==title||!result.html_url||!result.html_url.startsWith('https://github.com/'+REPO+'/issues/'))throw Error('GitHub hat das Speichern nicht bestätigt.');
      feedbackStatus('Feedback für '+dateLabel(edition.date)+' privat gespeichert. Es wird bei der nächsten Recherche berücksichtigt.');
      const p=$('saved-link');p.replaceChildren();const a=element('a','','Gespeichertes Feedback auf GitHub ansehen');a.href=result.html_url;a.target='_blank';a.rel='noopener noreferrer';p.append(a);p.hidden=false;
    }catch(err){feedbackStatus(err.message+' Deine Auswahl bleibt lokal erhalten.');}
    finally{$('save').disabled=false;}
  }
  document.addEventListener('DOMContentLoaded',init);
})();