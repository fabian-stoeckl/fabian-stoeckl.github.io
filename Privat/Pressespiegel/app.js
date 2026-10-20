'use strict';
let config, secret='', currentProfile, ratings={}, edition, latestDate, visibleArticles=[], visibleHeadlines=[];
const ratingDrafts={};
const draftKey=a=>edition.date+':'+(a.id||a.url);
function feedbackStatus(msg){$('feedback-status').textContent=msg;for(const id of ['news-feedback-status','features-feedback-status'])if($(id))$(id).textContent=msg;}
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const fmt=v=>new Intl.DateTimeFormat('de-AT',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Vienna'}).format(new Date(v));
function safeURL(value){const u=new URL(value);if(u.protocol!=='https:'||u.username||u.password)throw Error('Ungültiger Link');return u.href;}
function link(text,url){const n=el('a',text);n.href=safeURL(url);n.target='_blank';n.rel='noopener noreferrer';return n;}
async function api(path, data){const response=await fetch(config.api+path,{method:data?'POST':'GET',cache:'no-store',headers:{'Authorization':'Bearer '+secret,...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{})});const result=await response.json();if(!response.ok)throw Error(result.error||'Verbindung fehlgeschlagen');return result;}
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
    input.value=value;input.checked=ratingDrafts[key]?.value===value;
    input.onchange=()=>{ratingDrafts[key]={value,reason:ratingDrafts[key]?.reason||'',section};feedbackStatus('Auswahl vorgemerkt · beide Rubriken werden gemeinsam gespeichert.');};
    label.append(input,el('span',value));box.append(label);
  }
  const details=el('details',undefined,'rating-reason');
  details.append(el('summary','Optional begründen'));
  const label=el('label','Deine Begründung','reason');const reason=el('textarea');
  reason.rows=2;reason.maxLength=600;reason.placeholder='Was war hilfreich oder hat dir gefehlt?';
  reason.value=ratingDrafts[key]?.reason||'';details.open=!!reason.value;
  reason.oninput=()=>{ratingDrafts[key]={value:ratingDrafts[key]?.value||'',reason:reason.value,section};feedbackStatus('Änderung vorgemerkt · beide Rubriken werden gemeinsam gespeichert.');};
  label.append(reason);details.append(label);box.append(details);
  return box;
}
function article(a,index){const node=el('article',undefined,a.treat?'treat':'');const intro=el('div');intro.append(el('span',a.treat?'DAS ZUCKERL':a.topic,'eyebrow'));const meta=el('p',a.source+' · '+a.kind+'\n'+fmt(a.published_at)+(a.paywall?' · Paywall':''),'meta');intro.append(meta);const body=el('div',undefined,'body');const title=el('h2');title.append(link(a.title,a.url));body.append(title,el('p',a.summary));if(a.access==='teaser')body.append(el('p','Zusammenfassung beruht ausschließlich auf dem zugänglichen Vorspann.','small'));if(a.novelty)body.append(el('p','Neu gegenüber der bisherigen Berichterstattung: '+a.novelty,'novelty'));if(config.mode==='github'){body.append(githubRating(a));node.append(intro,body);return node;}const controls=el('div',undefined,'ratings');controls.setAttribute('aria-label','Relevanz bewerten');const state=el('p','','rating-state');state.setAttribute('role','status');const reasonLabel=el('label','Optionaler Grund ','reason');const reason=el('select');reason.setAttribute('aria-label','Grund für die Bewertung');for(const t of ['','Mehr davon','Schon bekannt','Zu oberflächlich','Thema interessiert mich nicht']){const o=el('option',t||'–');o.value=t;reason.append(o);}reasonLabel.append(reason);let saved=ratings[a.id];reason.value=saved?.reason||'';const buttons=[];function refresh(){for(const [b,v] of buttons)b.setAttribute('aria-pressed',String(saved?.value===v));state.textContent=saved?'Gespeichert · jederzeit änderbar':'';reason.disabled=!saved;}
async function save(value){buttons.forEach(([b])=>b.disabled=true);reason.disabled=true;state.textContent='Wird gespeichert …';try{await api('/api/rating',{id:a.id,value,reason:reason.value});saved={value,reason:reason.value};ratings[a.id]=saved;refresh();}catch(e){state.textContent=e.message+' – nicht gespeichert';reason.value=saved?.reason||'';}finally{buttons.forEach(([b])=>b.disabled=false);reason.disabled=!saved;}}
for(const [text,value] of [['Sehr relevant',1],['Teilweise relevant',0],['Nicht relevant',-1]]){const b=el('button',text);b.type='button';b.onclick=()=>save(value);controls.append(b);buttons.push([b,value]);}reason.onchange=()=>save(saved.value);refresh();body.append(controls,state,reasonLabel);node.append(intro,body);return node;}
function addSaveAction(section,statusId){
  if(config.mode!=='github')return;
  const bar=el('div',undefined,'section-save');
  const button=el('button','Alle Bewertungen speichern');button.type='button';
  button.onclick=()=>$('feedback-form').requestSubmit();
  const hint=el('p','Speichert die Bewertungen aus beiden Rubriken gemeinsam.','small');
  const state=el('p','','section-save-status');state.id=statusId;state.setAttribute('role','status');
  bar.append(button,hint,state);section.append(bar);
}
function render(){
  const e=edition,selection=GitHubPaper.partition(e);
  visibleArticles=selection.articles;
  visibleHeadlines=selection.headlines;
  $('articles').replaceChildren();
  const lead=el('div',undefined,'lead-grid'),rest=el('div',undefined,'article-list');
  visibleArticles.forEach((a,i)=>(i<3&&!a.treat?lead:rest).append(article(a,i)));
  $('articles').append(lead,rest);
  $('article-count').textContent=visibleArticles.length;
  $('headline-count').textContent=visibleHeadlines.length;
  $('headlines').replaceChildren();
  const cols=el('div',undefined,'headline-columns');
  for(const region of ['Österreich','International']){
    const sec=el('section');sec.append(el('h2',region));
    const list=el('ul');
    const regional=visibleHeadlines.filter(a=>a.region===region);
    if(!regional.length){const note=el('li',e.preview?'Keine zusätzlichen eigenständigen Nachrichten in dieser reduzierten Vorschau.':'Keine weiteren aktuellen Meldungen in dieser Ausgabe.','small empty-region');list.append(note);}
    for(const a of regional){
      const row=el('li',undefined,'news-item');
      row.append(link(a.title,a.url));
      if(typeof a.summary==='string'&&a.summary.trim())row.append(el('p',a.summary.trim(),'news-summary'));
      row.append(el('small',a.source));
      if(config.mode==='github')row.append(githubRating(a,'Heute wichtig'));
      list.append(row);
    }
    sec.append(list);cols.append(sec);
  }
  $('headlines').append(cols);
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
}
async function restoreSavedRatings(){
  if(config?.mode!=='github'||!edition)return;
  const date=edition.date,token=DirectFeedback.readToken();
  if(!token)return;
  try{
    const saved=await DirectFeedback.savedFeedback(date,token);
    if(!saved||edition.date!==date)return;
    const byId=new Map(saved.ratings.map(r=>[r.id,r]));
    for(const item of [...visibleHeadlines,...visibleArticles]){
      const id=await GitHubPaper.ratingId(item);
      if(edition.date!==date)return;
      const savedRow=byId.get(id),key=draftKey(item);
      if(!savedRow||ratingDrafts[key])continue;
      ratingDrafts[key]={value:savedRow.value,reason:savedRow.reason,section:savedRow.section};
      const field=[...document.querySelectorAll('.rating-dots')].find(x=>x.dataset.ratingKey===key);
      if(!field)continue;
      for(const input of field.querySelectorAll('input[type=radio]'))input.checked=input.value===savedRow.value;
      const note=field.querySelector('textarea');
      if(note)note.value=savedRow.reason;
      const disclosure=field.querySelector('.rating-reason');if(disclosure)disclosure.open=!!savedRow.reason;
    }
    if(!$('feedback').value&&saved.feedback)$('feedback').value=saved.feedback;
  }catch(err){feedbackStatus('Alte Bewertungen konnten nicht geladen werden: '+err.message);}
}

async function load(){try{const [list,r]=await Promise.all([api('/api/editions'),api('/api/ratings')]);ratings=r;latestDate=list.dates[0];$('date').replaceChildren();for(const d of list.dates){const o=el('option',d);o.value=d;$('date').append(o);}if(!list.dates.length){status('Noch keine erfolgreiche Ausgabe verfügbar.');return; }edition=await api('/api/edition');render();$('login').hidden=true;$('logout').hidden=config.preview;$('operating-state').textContent=list.scheduler_enabled?'Automatik konfiguriert · tatsächlicher Stand siehe Ausgabe.':'Täglicher Betrieb noch nicht aktiviert.';}catch(e){status(e.message);$('login').hidden=false;}}
$('date').onchange=async()=>{try{edition=config.mode==='github'?await GitHubPaper.edition($('date').value):await api('/api/edition?date='+encodeURIComponent($('date').value));render();await restoreSavedRatings();}catch(e){status(e.message);}};
for(const tab of ['headlines','articles'])$('tab-'+tab).onclick=()=>{for(const name of ['headlines','articles']){$(name).hidden=name!==tab;$('tab-'+name).setAttribute('aria-pressed',String(name===tab));}};
$('login-form').onsubmit=async e=>{e.preventDefault();secret=$('token').value;$('token').value='';await load();};
$('logout').onclick=()=>{secret='';location.reload();};

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
  else if(late)node.textContent='Hinweis: Die heutige Morgenzeitung fehlt noch. Letzte Ausgabe: '+e.date+'.';
  else node.textContent='Neue Ausgabe wird um 07:45 Uhr Wiener Zeit erwartet. Zuletzt: '+e.date+'.';
}
async function renderSelectionHistory() {
  const node=$('preference-edition-changes');
  if(!node)return;
  const index=await GitHubPaper.json('./data/index.json');
  if(!Array.isArray(index.dates)||index.dates.length<2){
    node.replaceChildren(el('p','Noch keine zwei veröffentlichten Ausgaben für einen überprüfbaren Vergleich. Die bisherige Demofassung ist kein Beleg für redaktionelles Lernen.','small'));
    return;
  }
  const available=index.dates.slice(0,6);
  const editions=await Promise.all(available.map(day=>GitHubPaper.edition(day)));
  const entries=[];
  for(let i=0;i<editions.length-1;i++){
    const newer=editions[i],older=editions[i+1];
    const counts=ed=>ed.articles.reduce((acc,a)=>(acc[a.topic]=(acc[a.topic]||0)+1,acc),{});
    const newCounts=counts(newer),oldCounts=counts(older);
    const topics=[...new Set([...Object.keys(newCounts),...Object.keys(oldCounts)])];
    const changed=topics.filter(t=>(newCounts[t]||0)!==(oldCounts[t]||0))
      .map(t=>t+': '+(oldCounts[t]||0)+' → '+(newCounts[t]||0)).slice(0,7);
    const audit=newer.selection_audit;
    const note=audit&&typeof audit.summary==='string'&&audit.summary.length<=600?audit.summary:null;
    entries.push({date:newer.date,reference:older.date,change:changed.join(' · ')||'Themenschwerpunkte in den Vertiefungen unverändert',note,hasProof:!!(audit&&audit.feedback_applied===true&&note)});
  }
  node.replaceChildren();
  const list=el('ul',undefined,'preference-list');
  for(const item of entries){
    const li=el('li');
    li.append(el('strong',item.date+' gegenüber '+item.reference+': '),
      el('span',item.change+'. '));
    li.append(el('span',item.hasProof?'Redaktionell dokumentierte Feedback-Anpassung: '+item.note:
      'Keine nachgewiesene Ursache durch Feedback.','small'));
    list.append(li);
  }
  node.append(list);
}

async function showPreferenceSummary() {
  const summary=$('preference-feedback'),token=DirectFeedback.readToken();
  summary.replaceChildren(el('p','Lese deine bisherigen Bewertungen aus deinem privaten GitHub-Repository …','small'));
  if(!token){
    summary.replaceChildren(el('p','Auf diesem Gerät ist noch kein GitHub-Zugang verbunden. Die Auswahlregeln oben kannst du trotzdem lesen; nach dem Verbinden ganz unten werden hier deine gespeicherten Bewertungen angezeigt.'));
    await renderSelectionHistory();
    return;
  }
  try{
    await renderSelectionHistory();
    const history=await DirectFeedback.feedbackHistory(token);
    if($('profile').hidden)return;
    if(!history.length){
      summary.replaceChildren(el('p','Bisher keine auswertbaren echten Bewertungen gefunden. Test-Feedback wird bewusst ignoriert.'));
      return;
    }
    const items=history.flatMap(entry=>entry.ratings.map(r=>({...r,date:entry.date})));
    const tally=label=>items.filter(r=>r.value===label).length;
    const feedbackCount=history.filter(h=>h.feedback.trim()).length;
    const top=el('p',history.length+' bewertete Ausgabe(n) · '+items.length+' Artikelbewertungen · '+feedbackCount+' allgemeine Rückmeldung(en).');
    const count=el('p','Sehr relevant: '+tally('Sehr relevant')+' · Teilweise relevant: '+tally('Teilweise relevant')+' · Nicht relevant: '+tally('Nicht relevant'),'small');
    const dateMap=new Map(),days=[...new Set(history.map(h=>h.date))].slice(0,20);
    for(const day of days){
      try{
        const ed=await GitHubPaper.edition(day);
        for(const item of [...(ed.articles||[]),...(ed.headlines||[])]){
          const id=await GitHubPaper.ratingId(item);
          dateMap.set(day+':'+id,{title:item.title,topic:item.topic||item.region||'Nachrichten'});
        }
      }catch(_){/* Not all older editions remain in the current public index. */}
    }
    if($('profile').hidden)return;
    const list=el('ul',undefined,'preference-list');
    for(const item of items.filter(r=>r.value).slice(-7).reverse()){
      const meta=dateMap.get(item.date+':'+item.id);
      const title=meta?.title||'Artikel '+item.id.slice(0,8);
      const text=item.value+': '+title+(item.reason?' – '+item.reason:'')+' ('+item.date+')';
      list.append(el('li',text));
    }
    summary.replaceChildren(top,count);
    if(list.childElementCount){
      summary.append(el('p','Zuletzt bewertete Artikel:','small'),list);
    }
    const recentNegative=items.filter(r=>r.value==='Nicht relevant');
    const recentPositive=items.filter(r=>r.value==='Sehr relevant');
    const signals=[];
    if(recentPositive.length)signals.push('Mehr Gewicht für Inhalte, die du ausdrücklich als sehr relevant markiert hast.');
    if(recentNegative.length)signals.push('Weniger Gewicht für ähnliche Beiträge, die du als nicht relevant markiert hast.');
    if(!signals.length)signals.push('Deine Rückmeldungen sind noch kein eindeutiges positives oder negatives Themen-Signal.');
    $('preference-learning-status').textContent='Bisheriges Feedback als Auswahlhinweis: '+signals.join(' ')+' Die tatsächliche Umsetzung in späteren, neu zusammengestellten Ausgaben ist noch nicht verlässlich nachgewiesen; daher wird hier keine bereits erfolgte Änderung behauptet.';
  }catch(error){
    summary.replaceChildren(el('p','Deine privaten Bewertungen konnten nicht geladen werden: '+error.message+'. Die Auswahlregeln bleiben sichtbar.','small'));
  }
}
let preferencesVisible=false;
const preferencesRoute=()=>location.hash==='#praeferenzen';
async function syncPreferencesView(){
  if(config?.mode!=='github')return;
  const open=preferencesRoute(),changed=preferencesVisible!==open;
  preferencesVisible=open;
  document.body.classList.toggle('preferences-view',open);
  $('profile').hidden=!open;
  const toggle=$('profile-toggle');
  toggle.setAttribute('aria-expanded',String(open));
  toggle.textContent=open?'← Zur Morgenzeitung':'Meine Präferenzen';
  toggle.setAttribute('aria-label',open?'Zur Morgenzeitung zurückkehren':'Meine Präferenzen öffnen');
  document.title=(open?'Meine Präferenzen':'Morgenzeitung')+' · Pressespiegel';
  if(changed){
    window.scrollTo(0,0);
    if(open)await showPreferenceSummary();
  }
}
function navigatePreferences(open){
  const next=new URL(window.location.href);
  next.hash=open?'praeferenzen':'';
  history.pushState(null,'',next);
  void syncPreferencesView();
}
window.addEventListener('popstate',()=>{void syncPreferencesView();});
window.addEventListener('hashchange',()=>{void syncPreferencesView();});
$('profile-close').onclick=()=>{if(config?.mode==='github')navigatePreferences(false);else $('profile').hidden=true;};
$('profile-toggle').onclick=async()=>{if(config?.mode==='github'){
  navigatePreferences(!preferencesRoute());
  return;}if(config?.api===null){status('Interessenprofil wird nach Verbindung des privaten Dienstes verfügbar.');return;}try{const data=await api('/api/profile');currentProfile=data.profile;$('topics').replaceChildren();for(const [topic,value] of Object.entries(currentProfile.topics)){const label=el('label',topic);const select=el('select');select.dataset.topic=topic;for(const [v,t] of [[5,'Sehr hoch'],[4,'Hoch'],[3,'Mittel'],[2,'Ergänzend'],[1,'Gering'],[0,'Ausblenden']]){const o=el('option',t);o.value=v;select.append(o);}select.value=value;label.append(select);$('topics').append(label);}$('rules').value=currentProfile.rules;$('profile-history').replaceChildren(el('p','Lernsignale (maximal ±0,5; explizite Prioritäten bleiben maßgeblich): '+JSON.stringify(data.learning)));for(const h of data.history)$('profile-history').append(el('p',fmt(h.at)+' · '+h.reason));$('profile').hidden=!$('profile').hidden;}catch(e){status(e.message);}};
if($('profile-form')) $('profile-form').onsubmit=async e=>{e.preventDefault();const topics=Object.fromEntries([...$('topics').querySelectorAll('select')].map(s=>[s.dataset.topic,Number(s.value)]));try{currentProfile=await api('/api/profile',{topics,rules:$('rules').value,version:currentProfile.version});$('profile-status').textContent='Gespeichert · gilt für den nächsten Recherchelauf';}catch(e){$('profile-status').textContent=e.message;}};
async function collectDraftRatings(){
  const selected=[];
  for(const [items,section] of [[visibleHeadlines,'Heute wichtig'],[visibleArticles,'Vertiefungen']]){
    for(const item of items){
      const draft=ratingDrafts[draftKey(item)];
      if(draft&&(draft.value||draft.reason.trim()))
        selected.push({id:await GitHubPaper.ratingId(item),value:draft.value||'',reason:draft.reason||'',section});
    }
  }
  return selected;
}

$('feedback-form').onsubmit=async e=>{e.preventDefault();if(config.mode==='github'){
  const b=e.submitter||$('feedback-form').querySelector('button[type=submit]');
  try{
    const selected=await collectDraftRatings();
    const comment=$('feedback').value.trim();
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
    const result=await DirectFeedback.submit(edition.date,selected,comment,token);
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
  }finally{b.disabled=false;}
  return;}const b=e.submitter;b.disabled=true;try{await api('/api/feedback',{text:$('feedback').value});$('feedback-status').textContent='Gespeichert · wird beim nächsten Recherchelauf berücksichtigt';$('feedback').value='';}catch(e){$('feedback-status').textContent=e.message+' – bitte erneut versuchen';}finally{b.disabled=false;}};
(async()=>{try{const oldTokenCleared=DirectFeedback.resetOldTokenOnce();config=await(await fetch('./config.json',{cache:'no-store'})).json();if(config.mode==='github') {
$('login').hidden=true;$('logout').hidden=true;$('feedback').maxLength=4000;
$('feedback-form').querySelector('button').textContent='Feedback speichern';
refreshGitHubConnection();if(oldTokenCleared)$('github-setup-status').textContent='Alter lokal gespeicherter Token gelöscht. Bitte neuen Token verbinden und den alten auf GitHub widerrufen.';$('feedback').required=false;
const index=await GitHubPaper.json('./data/index.json');latestDate=index.dates[0];$('date').replaceChildren();
for(const d of index.dates){const o=el('option',d);o.value=d;$('date').append(o);}
$('operating-state').textContent='Ausgaben aus GitHub · Feedback wird nach einmaliger Verbindung direkt auf GitHub gespeichert.';
if(!latestDate){status('Noch keine veröffentlichte Ausgabe verfügbar.');return;}
edition=await GitHubPaper.edition(latestDate);render();await restoreSavedRatings();await syncPreferencesView();return;
}if(config.api===null){status('Die Morgenzeitung wird vorbereitet. Der private Zeitungsdienst ist noch nicht verbunden.');return;}if(config.api&&!config.api.startsWith('https://'))throw Error('Unsichere Dienstadresse');if(config.preview)await load();else{$('login').hidden=false;status('Bitte öffne deine persönliche Morgenzeitung.');}}catch(e){status('Zeitungsdienst nicht erreichbar. '+e.message);}})();

$('feedback').addEventListener('input',()=>{feedbackStatus('Änderung noch nicht gesendet.');});


$('preference-comment-form').onsubmit=async event=>{
  event.preventDefault();
  const button=event.submitter||$('preference-comment-form').querySelector('button[type=submit]');
  const field=$('preference-comment');
  const fresh=field.value.trim();
  const out=$('preference-comment-status');
  if(!fresh){out.textContent='Bitte zuerst einen Kommentar eingeben.';return;}
  if(!edition){out.textContent='Noch keine Ausgabe geladen.';return;}
  const token=DirectFeedback.readToken();
  if(!token){
    out.textContent='Bitte verbinde deinen GitHub-Zugang am Ende der Seite, bevor du Feedback sendest.';
    return;
  }
  const day=edition.date;
  button.disabled=true;
  out.textContent='Dein Kommentar wird gemeinsam mit allen Bewertungen gespeichert …';
  try {
    // Preserve both previously submitted comments and any draft in the general form.
    const existing=await DirectFeedback.savedFeedback(day,token);
    if(edition.date!==day)throw Error('Ausgabe wurde während des Speicherns gewechselt.');
    const previous=(existing?.feedback||'').trim();
    const general=$('feedback').value.trim();
    const base=general?(!previous||general.includes(previous)?general:previous+'\n\n'+general):previous;
    const combined=[base,fresh].filter(Boolean).join('\n\n');
    const selected=await collectDraftRatings();
    if(edition.date!==day)throw Error('Ausgabe wurde während des Speicherns gewechselt.');
    const result=await DirectFeedback.submit(day,selected,combined,token);
    $('feedback').value=combined;
    field.value='';
    out.textContent=result.existing?'Dieser Kommentar war bereits gespeichert.':'Kommentar und sämtliche bisherigen Bewertungen erfolgreich privat auf GitHub gespeichert.';
    feedbackStatus('Rückmeldung aus „Meine Präferenzen“ gespeichert.');
    $('feedback-issue-link').href=result.html_url;
    $('feedback-confirmation').hidden=false;
    await showPreferenceSummary();
  } catch(error){
    out.textContent=error.message+' Dein Kommentar bleibt im Eingabefeld erhalten.';
  } finally{button.disabled=false;}
};

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
if($('github-disconnect')) $('github-disconnect').onclick=()=>{
  DirectFeedback.clearToken();
  refreshGitHubConnection();
  feedbackStatus('GitHub-Verbindung auf diesem Gerät entfernt. Bereits gespeicherte GitHub-Rückmeldungen bleiben erhalten.');
};
