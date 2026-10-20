'use strict';
let config, secret='', currentProfile, ratings={}, edition, latestDate;
function readDrafts(key){try{const data=JSON.parse(localStorage.getItem(key)||'{}');return data&&typeof data==='object'&&!Array.isArray(data)?data:{};}catch(_){return {};}}
const ratingDrafts=readDrafts('morgenzeitung:rating-drafts:v2');
const feedbackDrafts=readDrafts('morgenzeitung:feedback-drafts:v2');
function persistDrafts(){try{localStorage.setItem('morgenzeitung:rating-drafts:v2',JSON.stringify(ratingDrafts));}catch(_){}}
function persistComments(){try{localStorage.setItem('morgenzeitung:feedback-drafts:v2',JSON.stringify(feedbackDrafts));}catch(_){}}
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const fmt=v=>new Intl.DateTimeFormat('de-AT',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Vienna'}).format(new Date(v));
function safeURL(value){const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password)throw Error('Ungültiger Link');return u.href;}
function link(text,url){const n=el('a',text);n.href=safeURL(url);n.target='_blank';n.rel='noopener noreferrer';return n;}
async function api(path, data){const response=await fetch(config.api+path,{method:data?'POST':'GET',cache:'no-store',headers:{'Authorization':'Bearer '+secret,...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{})});const result=await response.json();if(!response.ok)throw Error(result.error||'Verbindung fehlgeschlagen');return result;}
function status(text){$('notice').textContent=text;}
function readingLinks(a){const box=el('div',undefined,'links');box.append(link('Original lesen ↗',a.url));if(a.paywall){const archive=link('Archivsuche ↗','https://archive.is/'+safeURL(a.url));const smry=link('SMRY öffnen ↗','https://smry.ai/'+safeURL(a.url));const isPresse=/(^|\.)diepresse\.com$/.test(new URL(a.url).hostname);box.append(...(isPresse?[smry,archive]:[archive,smry]));}return box;}
function githubRating(a) {
  const box=el('fieldset',undefined,'ratings rating-dots');
  box.append(el('legend','Wie relevant ist dieser Artikel?'));
  const key=edition.date+':'+a.id;
  for(const value of ['Sehr relevant','Teilweise relevant','Nicht relevant']) {
    const label=el('label');const input=el('input');input.type='radio';input.name='rating-'+a.id;
    input.value=value;input.checked=ratingDrafts[key]?.value===value;
    input.onchange=()=>{ratingDrafts[key]={id:a.id,value,reason:ratingDrafts[key]?.reason||''};persistDrafts();$('feedback-status').textContent='Auswahl vorgemerkt · beide Rubriken werden zusammen gespeichert.';};
    label.append(input,el('span',value));box.append(label);
  }
  const label=el('label','Optional: Warum? ','reason');const reason=el('textarea');
  reason.rows=2;reason.maxLength=600;reason.placeholder='Was war hilfreich oder hat dir gefehlt?';
  reason.value=ratingDrafts[key]?.reason||'';
  reason.oninput=()=>{ratingDrafts[key]={id:a.id,value:ratingDrafts[key]?.value,reason:reason.value};persistDrafts();$('feedback-status').textContent='Änderung vorgemerkt · beide Rubriken werden zusammen gespeichert.';};label.append(reason);box.append(label);
  return box;
}
function article(a,index){const node=el('article',undefined,a.treat?'treat':'');const intro=el('div');intro.append(el('span',a.treat?'DAS ZUCKERL':a.topic,'eyebrow'));const meta=el('p',a.source+' · '+a.kind+'\n'+fmt(a.published_at)+(a.paywall?' · Paywall':''),'meta');intro.append(meta);const body=el('div',undefined,'body');const title=el('h2');title.append(link(a.title,a.url));body.append(title,el('p',a.summary));if(a.access==='teaser')body.append(el('p','Zusammenfassung beruht ausschließlich auf dem zugänglichen Vorspann.','small'));if(a.novelty)body.append(el('p','Neu gegenüber der bisherigen Berichterstattung: '+a.novelty,'novelty'));body.append(readingLinks(a));if(config.mode==='github'){body.append(githubRating(a));node.append(intro,body);return node;}const controls=el('div',undefined,'ratings');controls.setAttribute('aria-label','Relevanz bewerten');const state=el('p','','rating-state');state.setAttribute('role','status');const reasonLabel=el('label','Optionaler Grund ','reason');const reason=el('select');reason.setAttribute('aria-label','Grund für die Bewertung');for(const t of ['','Mehr davon','Schon bekannt','Zu oberflächlich','Thema interessiert mich nicht']){const o=el('option',t||'–');o.value=t;reason.append(o);}reasonLabel.append(reason);let saved=ratings[a.id];reason.value=saved?.reason||'';const buttons=[];function refresh(){for(const [b,v] of buttons)b.setAttribute('aria-pressed',String(saved?.value===v));state.textContent=saved?'Gespeichert · jederzeit änderbar':'';reason.disabled=!saved;}
async function save(value){buttons.forEach(([b])=>b.disabled=true);reason.disabled=true;state.textContent='Wird gespeichert …';try{await api('/api/rating',{id:a.id,value,reason:reason.value});saved={value,reason:reason.value};ratings[a.id]=saved;refresh();}catch(e){state.textContent=e.message+' – nicht gespeichert';reason.value=saved?.reason||'';}finally{buttons.forEach(([b])=>b.disabled=false);reason.disabled=!saved;}}
for(const [text,value] of [['Sehr relevant',1],['Teilweise relevant',0],['Nicht relevant',-1]]){const b=el('button',text);b.type='button';b.onclick=()=>save(value);controls.append(b);buttons.push([b,value]);}reason.onchange=()=>save(saved.value);refresh();body.append(controls,state,reasonLabel);node.append(intro,body);return node;}
function sectionSave(section,other){
  const box=el('div',undefined,'section-save');
  const button=el('button','Alle Bewertungen speichern');button.type='button';
  button.className='save-all-feedback';
  button.onclick=()=>{$('feedback-form').requestSubmit();$('feedback-section').scrollIntoView({behavior:'smooth'});};
  box.append(button,el('p','Übermittelt auch Bewertungen aus '+other+'.','small'));
  section.append(box);
}
function render(){
  const e=edition;
  $('articles').replaceChildren();
  const lead=el('div',undefined,'lead-grid'),rest=el('div',undefined,'article-list');
  e.articles.forEach((a,i)=>(i<3&&!a.treat?lead:rest).append(article(a,i)));
  $('articles').append(lead,rest);
  sectionSave($('articles'),'„Heute wichtig“');
  $('article-count').textContent=e.articles.length;
  $('headline-count').textContent=e.headlines.length;
  $('headlines').replaceChildren();
  const cols=el('div',undefined,'headline-columns');
  for(const region of ['Österreich','International']){
    const sec=el('section');sec.append(el('h2',region));const list=el('ul');
    for(const a of e.headlines.filter(a=>a.region===region)){
      const item=el('li');
      item.append(link(a.title,a.url),el('small',a.source));
      if(config.mode==='github')item.append(githubRating(a));
      list.append(item);
    }
    if(!list.children.length)list.append(el('li','Keine eigenständigen Meldungen in dieser Ausgabe.','small'));
    sec.append(list);cols.append(sec);
  }
  $('headlines').append(cols);
  sectionSave($('headlines'),'„Vertiefungen“');
  $('feedback').value=feedbackDrafts[e.date]||'';
  $('edition-meta').textContent=new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'}).format(new Date(e.available_at))+' · '+(e.preview?'Vorschau':('bereitgestellt '+fmt(e.available_at)));
  $('window').textContent='Recherche: '+fmt(e.window_start)+' bis '+fmt(e.window_end)+' · Stand: '+fmt(e.researched_at)+' · alle Zeiten Wien';
  $('feedback-section').hidden=false;
  status((e.preview?'Vorschau mit echten Artikeln · noch kein täglicher Betrieb. ':'')+(e.limitations||[]).join(' ')+(e.duplicateHeadlinesRemoved?' '+e.duplicateHeadlinesRemoved+' doppelte Nachrichten entfernt.':''));
  if(!e.preview){
    const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Vienna',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    if(e.date!==today)status((e.date!==latestDate?'Archiv · Ausgabe vom ':'Letzte verfügbare Ausgabe vom ')+e.date+'. '+(e.limitations||[]).join(' '));
  }
}
async function load(){try{const [list,r]=await Promise.all([api('/api/editions'),api('/api/ratings')]);ratings=r;latestDate=list.dates[0];$('date').replaceChildren();for(const d of list.dates){const o=el('option',d);o.value=d;$('date').append(o);}if(!list.dates.length){status('Noch keine erfolgreiche Ausgabe verfügbar.');return; }edition=await api('/api/edition');render();$('login').hidden=true;$('logout').hidden=config.preview;$('operating-state').textContent=list.scheduler_enabled?'Automatik konfiguriert · tatsächlicher Stand siehe Ausgabe.':'Täglicher Betrieb noch nicht aktiviert.';}catch(e){status(e.message);$('login').hidden=false;}}
$('date').onchange=async()=>{try{edition=config.mode==='github'?await GitHubPaper.edition($('date').value):await api('/api/edition?date='+encodeURIComponent($('date').value));render();}catch(e){status(e.message);}};
for(const tab of ['headlines','articles'])$('tab-'+tab).onclick=()=>{for(const name of ['headlines','articles']){$(name).hidden=name!==tab;$('tab-'+name).setAttribute('aria-pressed',String(name===tab));}};
$('login-form').onsubmit=async e=>{e.preventDefault();secret=$('token').value;$('token').value='';await load();};
$('logout').onclick=()=>{secret='';location.reload();};
$('profile-toggle').onclick=async()=>{if(config.mode==='github'){status('Profiländerungen bitte über das GitHub-Feedback unten mitteilen. Deine ausdrücklichen Wünsche haben Vorrang.');$('feedback-section').scrollIntoView({behavior:'smooth'});return;}if(config?.api===null){status('Interessenprofil wird nach Verbindung des privaten Dienstes verfügbar.');return;}try{const data=await api('/api/profile');currentProfile=data.profile;$('topics').replaceChildren();for(const [topic,value] of Object.entries(currentProfile.topics)){const label=el('label',topic);const select=el('select');select.dataset.topic=topic;for(const [v,t] of [[5,'Sehr hoch'],[4,'Hoch'],[3,'Mittel'],[2,'Ergänzend'],[1,'Gering'],[0,'Ausblenden']]){const o=el('option',t);o.value=v;select.append(o);}select.value=value;label.append(select);$('topics').append(label);}$('rules').value=currentProfile.rules;$('profile-history').replaceChildren(el('p','Lernsignale (maximal ±0,5; explizite Prioritäten bleiben maßgeblich): '+JSON.stringify(data.learning)));for(const h of data.history)$('profile-history').append(el('p',fmt(h.at)+' · '+h.reason));$('profile').hidden=!$('profile').hidden;}catch(e){status(e.message);}};
$('profile-form').onsubmit=async e=>{e.preventDefault();const topics=Object.fromEntries([...$('topics').querySelectorAll('select')].map(s=>[s.dataset.topic,Number(s.value)]));try{currentProfile=await api('/api/profile',{topics,rules:$('rules').value,version:currentProfile.version});$('profile-status').textContent='Gespeichert · gilt für den nächsten Recherchelauf';}catch(e){$('profile-status').textContent=e.message;}};
$('feedback-form').onsubmit=async e=>{e.preventDefault();if(config.mode==='github'){
  const b=e.submitter;
  try{
    const selected=[...edition.headlines,...edition.articles].map(a=>ratingDrafts[edition.date+':'+a.id])
      .filter(r=>r&&(r.value||r.reason.trim()));
    const comment=$('feedback').value.trim();
    if(!selected.length&&!comment)throw Error('Bitte mindestens einen Artikel bewerten oder Feedback eingeben.');
    const token=DirectFeedback.readToken();
    if(!token){
      refreshGitHubConnection();
      $('github-setup').scrollIntoView({behavior:'smooth'});
      throw Error('Bitte zuerst einmalig den GitHub-Zugang oben einrichten.');
    }
    b.disabled=true;
    $('feedback-status').textContent='Wird direkt auf GitHub gespeichert …';
    $('feedback-confirmation').hidden=true;
    const result=await DirectFeedback.submit(edition.date,selected,comment,token);
    $('feedback-status').textContent=result.existing
      ? 'Bereits auf GitHub gespeichert.'
      : (result.updated?'Auf GitHub erfolgreich aktualisiert.':'Erfolgreich auf GitHub gespeichert.');
    $('feedback-issue-link').href=result.html_url;
    $('feedback-confirmation').hidden=false;
  }catch(err){
    $('feedback-status').textContent=err.message+' Nicht bestätigte Änderungen bleiben im Tab erhalten.';
    if(/ungültig oder abgelaufen/.test(err.message)){
      $('github-setup').hidden=false;
      $('github-connected').hidden=true;
    }
  }finally{b.disabled=false;}
  return;}const b=e.submitter;b.disabled=true;try{await api('/api/feedback',{text:$('feedback').value});$('feedback-status').textContent='Gespeichert · wird beim nächsten Recherchelauf berücksichtigt';$('feedback').value='';}catch(e){$('feedback-status').textContent=e.message+' – bitte erneut versuchen';}finally{b.disabled=false;}};
(async()=>{try{config=await(await fetch('./config.json',{cache:'no-store'})).json();if(config.mode==='github') {
$('login').hidden=true;$('logout').hidden=true;$('feedback').maxLength=4000;
$('feedback-form').querySelector('button').textContent='Feedback speichern';
refreshGitHubConnection();$('feedback').required=false;
const index=await GitHubPaper.json('./data/index.json');latestDate=index.dates[0];$('date').replaceChildren();
for(const d of index.dates){const o=el('option',d);o.value=d;$('date').append(o);}
$('operating-state').textContent='Ausgaben aus GitHub · Feedback wird nach einmaliger Verbindung direkt auf GitHub gespeichert.';
if(!latestDate){status('Noch keine veröffentlichte Ausgabe verfügbar.');return;}
edition=await GitHubPaper.edition(latestDate);render();return;
}if(config.api===null){status('Die Morgenzeitung wird vorbereitet. Der private Zeitungsdienst ist noch nicht verbunden.');return;}if(config.api&&!config.api.startsWith('https://'))throw Error('Unsichere Dienstadresse');if(config.preview)await load();else{$('login').hidden=false;status('Bitte öffne deine persönliche Morgenzeitung.');}}catch(e){status('Zeitungsdienst nicht erreichbar. '+e.message);}})();

$('feedback').addEventListener('input',()=>{if(edition){feedbackDrafts[edition.date]=$('feedback').value;persistComments();}$('feedback-status').textContent='Änderung noch nicht gesendet.';});


function refreshGitHubConnection(){
  const connected=!!DirectFeedback.readToken();
  $('github-setup').hidden=connected;
  $('github-connected').hidden=!connected;
}
$('github-setup-form').onsubmit=async e=>{
  e.preventDefault();
  const button=e.submitter;
  const token=$('github-token').value.trim();
  if(!$('remember-token').checked){
    $('github-setup-status').textContent='Bitte die lokale Speicherung ausdrücklich bestätigen.';
    return;
  }
  button.disabled=true;
  $('github-setup-status').textContent='Prüfe den GitHub-Zugang …';
  try{
    await DirectFeedback.verify(token);
    DirectFeedback.saveToken(token);
    $('github-token').value='';
    $('remember-token').checked=false;
    $('github-setup-status').textContent='';
    refreshGitHubConnection();
    $('feedback-status').textContent='GitHub verbunden. Dein nächstes Feedback lässt sich mit einem Klick speichern.';
  }catch(err){
    $('github-setup-status').textContent=err.message+' Kein Token gespeichert.';
  }finally{button.disabled=false;}
};
$('github-disconnect').onclick=()=>{
  DirectFeedback.clearToken();
  refreshGitHubConnection();
  $('feedback-status').textContent='GitHub-Verbindung auf diesem Gerät entfernt. Bereits gespeicherte GitHub-Rückmeldungen bleiben erhalten.';
};
