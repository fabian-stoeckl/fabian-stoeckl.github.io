'use strict';
// One explicit browser-owned state object; edition/config remain stable V3 hooks.
let config, edition, latestDate;
const readerState={visibleArticles:[],visibleHeadlines:[],ratingDrafts:{},loadSequence:0,saving:false};
const draftKey=a=>edition.date+':'+(a.id||a.url);
function feedbackStatus(msg){$('feedback-status').textContent=msg;for(const id of ['news-feedback-status','features-feedback-status'])if($(id))$(id).textContent=msg;}
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const fmt=v=>new Intl.DateTimeFormat('de-AT',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Vienna'}).format(new Date(v));
function safeURL(value){const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password)throw Error('Ungültiger Link');return u.href;}
function link(text,url){const n=el('a',text);n.href=safeURL(url);n.target='_blank';n.rel='noopener noreferrer';return n;}
function status(text){
  const notice=$('notice');
  notice.textContent=text||'';
  notice.hidden=!text;
}
function githubRating(a,section='Vertiefungen') {
  const box=el('fieldset',undefined,'ratings rating-dots');
  box.append(el('legend','Wie relevant ist dieser Artikel?'));
  const key=draftKey(a);
  box.dataset.ratingKey=key;
  for(const value of ['Sehr relevant','Teilweise relevant','Nicht relevant']) {
    const label=el('label');const input=el('input');input.type='radio';input.name='rating-'+key;
    input.value=value;input.checked=readerState.ratingDrafts[key]?.value===value;
    input.onchange=()=>{readerState.ratingDrafts[key]={value,reason:readerState.ratingDrafts[key]?.reason||'',section};feedbackStatus('Auswahl vorgemerkt · beide Rubriken werden gemeinsam gespeichert.');};
    label.append(input,el('span',value));box.append(label);
  }
  const details=el('details',undefined,'rating-reason');
  details.append(el('summary','Optional begründen'));
  const label=el('label','Deine Begründung','reason');const reason=el('textarea');
  reason.rows=2;reason.maxLength=600;reason.placeholder='Was war hilfreich oder hat dir gefehlt?';
  reason.value=readerState.ratingDrafts[key]?.reason||'';details.open=!!reason.value;
  reason.oninput=()=>{readerState.ratingDrafts[key]={value:readerState.ratingDrafts[key]?.value||'',reason:reason.value,section};feedbackStatus('Änderung vorgemerkt · beide Rubriken werden gemeinsam gespeichert.');};
  label.append(reason);details.append(label);box.append(details);
  return box;
}
function article(a,index,section='Vertiefungen'){
  const isHeadline=section==='Heute wichtig';
  const node=el('article',undefined,isHeadline?'news-item':(a.treat?'treat':''));
  // Stable identity for editorial enrichment, regardless of lead/rest ordering.
  node.dataset.articleId=String(a.id||'');
  node.dataset.section=section;
  const intro=el('div');
  intro.append(el('span',isHeadline?'NACHRICHT':(a.treat?'DAS ZUCKERL':a.topic),'eyebrow'));
  const details=[a.source];
  if(!isHeadline&&a.kind)details.push(a.kind);
  details.push(fmt(a.published_at));
  if(a.paywall)details.push('Paywall');
  intro.append(el('p',details.join(' · '),'meta'));
  const body=el('div',undefined,'body');
  const title=el('h2');title.append(link(a.title,a.url));
  body.append(title,el('p',a.summary,isHeadline?'news-summary':undefined));
  if(a.access==='teaser')body.append(el('p','Zusammenfassung beruht ausschließlich auf dem zugänglichen Vorspann.','small'));
  if(!isHeadline&&typeof a.novelty_explanation==='string'&&a.novelty_explanation.trim())
    body.append(el('p','Neu gegenüber der bisherigen Berichterstattung: '+a.novelty_explanation,'novelty'));
  body.append(githubRating(a,section));node.append(intro,body);return node;
}
function addSaveAction(section,statusId){
  const bar=el('div',undefined,'section-save');
  const button=el('button','Alle Bewertungen speichern');button.type='button';
  button.onclick=()=>$('feedback-form').requestSubmit();
  const hint=el('p','Speichert die Bewertungen aus beiden Rubriken gemeinsam.','small');
  const state=el('p','','section-save-status');state.id=statusId;state.setAttribute('role','status');
  bar.append(button,hint,state);section.append(bar);
}
function render(){
  const e=edition,selection=GitHubPaper.partition(e);
  readerState.visibleArticles=selection.articles;
  readerState.visibleHeadlines=selection.headlines;
  $('articles').replaceChildren();
  const lead=el('div',undefined,'lead-grid'),rest=el('div',undefined,'article-list');
  readerState.visibleArticles.forEach((a,i)=>(i<3&&!a.treat?lead:rest).append(article(a,i)));
  $('articles').append(lead,rest);
  $('article-count').textContent=readerState.visibleArticles.length;
  $('headline-count').textContent=readerState.visibleHeadlines.length;
  $('headlines').replaceChildren();
  const cols=el('div',undefined,'headline-columns');
  for(const region of ['Österreich','International']){
    const sec=el('section',undefined,'headline-region');
    sec.append(el('h2',region,'region-title'));
    const list=el('div',undefined,'article-list');
    const regional=readerState.visibleHeadlines.filter(a=>a.region===region);
    if(!regional.length){
      list.append(el('p',e.preview?'Keine zusätzlichen eigenständigen Nachrichten in dieser reduzierten Vorschau.':'Keine weiteren aktuellen Meldungen in dieser Ausgabe.','small empty-region'));
    }
    for(const a of regional)list.append(article(a,undefined,'Heute wichtig'));
    sec.append(list);cols.append(sec);
  }
  $('headlines').append(cols);
  const discovery=$('new-sources');
  if(discovery){
    discovery.replaceChildren();
    const trials=Array.isArray(e.new_sources)?e.new_sources.filter(s=>s&&typeof s.name==='string'&&typeof s.why==='string'&&typeof s.example_url==='string'):[];
    discovery.hidden=trials.length===0;
    if(trials.length){
      discovery.append(el('h2','Neue Quellen entdeckt'));
      discovery.append(el('p','Testquellen mit konkreten Artikeln. Eine dauerhafte Aufnahme erfolgt erst nach wiederholt guter Relevanz und deinem Feedback.','small'));
      const items=el('ul',undefined,'source-trials');
      for(const source of trials){
        const item=el('li');
        try{item.append(link(source.name,source.example_url));}catch{continue;}
        item.append(document.createTextNode(' – '+source.why));
        items.append(item);
      }
      discovery.append(items);
    }
  }
  addSaveAction($('headlines'),'news-feedback-status');
  addSaveAction($('articles'),'features-feedback-status');
  // The date and the research timestamp are shown exactly once in the masthead.
  // Use noon UTC for the calendar date, to avoid browser timezone rollover.
  const issueDay=new Intl.DateTimeFormat('de-AT',{dateStyle:'full',timeZone:'Europe/Vienna'}).format(new Date(e.date+'T12:00:00Z'));
  const issueTime=new Intl.DateTimeFormat('de-AT',{hour:'2-digit',minute:'2-digit',timeZone:'Europe/Vienna'}).format(new Date(e.researched_at));
  $('edition-meta').textContent=issueDay+' · Stand '+issueTime+' Uhr (Wien)'+(e.preview?' · Vorschau':'');
  $('feedback-section').hidden=false;
  updatePublicationStatus(e);
  // The edition's free-form limitations are editorial notes, not errors. Display
  // only explicitly flagged operational issues or genuinely filtered duplicates.
  const errors=[...(Array.isArray(e.errors)?e.errors:[]),...(Array.isArray(e.warnings)?e.warnings:[])];
  if(selection.duplicatesRemoved)errors.unshift('Doppelte Nachrichtenmeldungen ausgeblendet: '+selection.duplicatesRemoved+'.');
  status(errors.filter(x=>typeof x==='string'&&x.trim()).join(' '));
  // Deterministic one-shot enhancement after each render, no MutationObservers.
  RatingReasons.enhance();
  EditorialExtras.render(e);
}
async function restoreSavedRatings(){
  if(config?.mode!=='github'||!edition)return;
  const date=edition.date,token=DirectFeedback.readToken();
  if(!token)return;
  try{
    const saved=await DirectFeedback.savedFeedback(date,token);
    if(!saved||edition.date!==date)return;
    const byId=new Map(saved.ratings.map(r=>[r.id,r]));
    for(const item of [...readerState.visibleHeadlines,...readerState.visibleArticles]){
      const id=await GitHubPaper.ratingId(item);
      if(edition.date!==date)return;
      const savedRow=byId.get(id),key=draftKey(item);
      if(!savedRow||readerState.ratingDrafts[key])continue;
      readerState.ratingDrafts[key]={value:savedRow.value,reason:savedRow.reason,section:savedRow.section};
      const field=[...document.querySelectorAll('.rating-dots')].find(x=>x.dataset.ratingKey===key);
      if(!field)continue;
      for(const input of field.querySelectorAll('input[type=radio]'))input.checked=input.value===savedRow.value;
      const note=field.querySelector('textarea');
      if(note)note.value=savedRow.reason;
      const disclosure=field.querySelector('.rating-reason');if(disclosure)disclosure.open=!!savedRow.reason;
    }
    if(!$('feedback').value&&saved.feedback)$('feedback').value=saved.feedback;
  }catch(err){feedbackStatus('Gespeicherte Bewertungen konnten nicht geladen werden: '+err.message);}
}

$('date').onchange=async()=>{
  const sequence=++readerState.loadSequence;
  const requested=$('date').value;
  try{
    const next=await GitHubPaper.edition(requested);
    if(sequence!==readerState.loadSequence)return;
    edition=next;
    render();
    await restoreSavedRatings();
  }catch(e){if(sequence===readerState.loadSequence)status(e.message);}
};
for(const tab of ['headlines','articles'])$('tab-'+tab).onclick=()=>{
  // Preserve unsent feedback; switching only changes visibility.
  if($('tab-'+tab).getAttribute('aria-pressed')==='true')return;
  for(const name of ['headlines','articles']){
    $(name).hidden=name!==tab;
    $('tab-'+name).setAttribute('aria-pressed',String(name===tab));
  }
  // Sticky tabs may have been clicked far down the page: show the masthead again.
  window.scrollTo(0,0);
};

function updatePublicationStatus(e) {
  const node=$('publication-status');
  if(!node||!e)return;
  const now=new Date();
  const d=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Vienna',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
  const hhmm=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Vienna',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(now);
  const late=hhmm>='07:45';
  node.dataset.state=e.preview||e.date!==d&&late?'stale':e.date===d?'fresh':'pending';
  // No third repeated date/time block when today's regular edition is up.
  if(!e.preview&&e.date===d){node.hidden=true;node.textContent='';return;}
  node.hidden=false;
  if(e.preview)node.textContent='Beispielausgabe: Der tägliche Betrieb ist für diese Ausgabe noch nicht bestätigt.';
  else if(late)node.textContent='Hinweis: Die heutige Persönliche Zeitung fehlt noch. Letzte Ausgabe: '+e.date+'.';
  else node.textContent='Neue Ausgabe wird um 07:45 Uhr Wiener Zeit erwartet. Zuletzt: '+e.date+'.';
}
async function collectDraftRatings(date,groups){
  const selected=[];
  for(const [items,section] of groups){
    for(const item of items){
      const draft=readerState.ratingDrafts[date+':'+(item.id||item.url)];
      if(draft&&(draft.value||draft.reason.trim()))
        selected.push({id:await GitHubPaper.ratingId(item),value:draft.value||'',reason:draft.reason||'',section});
    }
  }
  return selected;
}

$('feedback-form').onsubmit=async e=>{e.preventDefault();
  // Section buttons and the main form may all request submission. One tab
  // must never start competing writes to the same private GitHub Issue.
  if(readerState.saving)return;
  readerState.saving=true;
  const submittedEdition=edition;
  const submittedText=$('feedback').value;
  const groups=[[readerState.visibleHeadlines.slice(),'Heute wichtig'],
                [readerState.visibleArticles.slice(),'Vertiefungen']];
  const b=e.submitter||$('feedback-form').querySelector('button[type=submit]');
  try{
    const selected=await collectDraftRatings(submittedEdition.date,groups);
    const comment=EditorialExtras.enrichFeedback(submittedEdition,submittedText).trim();
    if(!selected.length&&!comment)throw Error('Bitte mindestens einen Artikel bewerten oder Feedback eingeben.');
    const token=DirectFeedback.readToken();
    if(!token){
      refreshGitHubConnection();
      $('github-setup').scrollIntoView({behavior:'smooth'});
      throw Error('Bitte zuerst einmalig den GitHub-Zugang oben einrichten.');
    }
    b.disabled=true;
    feedbackStatus('Wird gemeinsam auf GitHub gespeichert …');
    $('feedback-confirmation').hidden=true;
    const result=await DirectFeedback.submit(submittedEdition.date,selected,comment,token);
    feedbackStatus(result.existing
      ? 'Beide Rubriken sind bereits auf GitHub gespeichert.'
      : (result.updated?'Bewertungen beider Rubriken auf GitHub aktualisiert.':'Bewertungen beider Rubriken erfolgreich auf GitHub gespeichert.'));
    $('feedback-issue-link').href=result.html_url;
    $('feedback-confirmation').hidden=false;
  }catch(err){
    feedbackStatus(err.message+' Nicht bestätigte Änderungen bleiben im Tab erhalten.');
    if(/ungültig oder abgelaufen/.test(err.message)){
      $('github-setup').hidden=false;
      $('github-connected').hidden=true;
    }
  }finally{b.disabled=false;readerState.saving=false;}
};
(async()=>{try{config=await(await fetch('./config.json',{cache:'no-store'})).json();if(config.mode!=='github')throw Error('Ungültiger V3-Modus');
$('feedback').maxLength=4000;
$('feedback-form').querySelector('button').textContent='Feedback speichern';
refreshGitHubConnection();$('feedback').required=false;
const index=await GitHubPaper.json('./data/index.json');latestDate=index.dates[0];$('date').replaceChildren();
for(const d of index.dates){const o=el('option',d);o.value=d;$('date').append(o);}
$('operating-state').textContent='Ausgaben aus GitHub · Feedback wird nach einmaliger Verbindung direkt auf GitHub gespeichert.';
if(!latestDate){status('Noch keine veröffentlichte Ausgabe verfügbar.');return;}
edition=await GitHubPaper.edition(latestDate);render();await restoreSavedRatings();return;
}catch(e){status('Persönliche Zeitung nicht erreichbar. '+e.message);}})();

$('feedback').addEventListener('input',()=>{feedbackStatus('Änderung noch nicht gesendet.');});


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
    feedbackStatus('GitHub verbunden. Dein nächstes Feedback lässt sich mit einem Klick speichern.');
    await restoreSavedRatings();
  }catch(err){
    $('github-setup-status').textContent=err.message+' Kein Token gespeichert.';
  }finally{button.disabled=false;}
};
const disconnect=$('github-disconnect');
if(disconnect)disconnect.onclick=()=>{
  DirectFeedback.clearToken();
  refreshGitHubConnection();
  feedbackStatus('GitHub-Verbindung auf diesem Gerät entfernt. Bereits gespeicherte GitHub-Rückmeldungen bleiben erhalten.');
};
