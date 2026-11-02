'use strict';
const $=id=>document.getElementById(id);
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const safeLink=url=>{try{const u=new URL(url);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null;}catch(_){return null;}};
let edition,loading=0,saving=false,interestsGeneration=0;
const drafts=new Map(),comments=new Map();
const pendingKey='pressespiegel:pending:v1';
const dateLabel=d=>/^\d{4}-\d{2}-\d{2}$/.test(d)?new Intl.DateTimeFormat('de-AT',{dateStyle:'long',timeZone:'UTC'}).format(new Date(d+'T12:00:00Z')):d;
async function json(path){const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error('Ausgabe konnte nicht geladen werden.');return r.json();}
function rating(item,section){
 const key=edition.date+':'+item.id;
 const draft=drafts.get(key)||{rating:'',reason:''};drafts.set(key,draft);
 const details=node('details',undefined,'rating');details.append(node('summary','Passt dieser Artikel zu dir?'));
 const group=node('fieldset');group.append(node('legend','Bewertung: '+item.title));
 for(const value of ['Sehr relevant','Teilweise relevant','Nicht relevant']){
  const label=node('label'),input=node('input');input.type='radio';input.name='rating-'+item.id;input.value=value;input.checked=draft.rating===value;
  input.onchange=()=>{draft.rating=value;draft.dirty=true;};label.append(input,document.createTextNode(value));group.append(label);
 }
 const reason=node('textarea');reason.rows=2;reason.maxLength=600;reason.placeholder='Warum? Was wäre hilfreicher? (freiwillig)';reason.setAttribute('aria-label','Begründung zu '+item.title);reason.value=draft.reason;
 reason.oninput=()=>{draft.reason=reason.value;draft.dirty=true;};
 details.append(group,reason);details.open=!!draft.rating||!!draft.reason;return details;
}
function render(){
 $('edition-meta').textContent=edition.kind==='imported'?'Übernommene Ausgabe · keine neue Recherche':'Recherchiert für '+dateLabel(edition.date);
 $('edition-note').textContent=edition.note||'';
 for(const section of ['articles','headlines']){
  const target=$(section);target.replaceChildren();
  for(const item of edition[section]){
   const story=node('article',undefined,'story');story.dataset.articleId=item.id;
   const body=node('div'),heading=node('h3'),link=node('a',item.title);const href=safeLink(item.url);if(href){link.href=href;link.target='_blank';link.rel='noopener noreferrer';}heading.append(link);
   const basis={headline:'Lesehinweis · Überschrift',teaser:'Grundlage: Vorspann',read:'Grundlage: gelesener Originaltext oder Originalauszug'}[item.basis]||'Grundlage nicht dokumentiert';
   body.append(node('div',item.source+' · '+dateLabel(item.published_at),'source'),heading,node('div',basis,'small'));
   const text=node('div');if(item.source_context)text.append(node('p',item.source_context,'small'));text.append(node('p',item.summary,'summary'));if(item.why)text.append(node('p',item.why,'why'));
   story.append(body,text,rating(item,section));target.append(story);
  }
  if(!edition[section].length)target.append(node('p','Für diese Ausgabe keine weiteren Beiträge.','small'));
 }
 $('comment').value=comments.get(edition.date)||'';
}
async function loadEdition(date){
 const sequence=++loading;$('load-status').textContent='Ausgabe wird geladen …';$('save-feedback').disabled=true;
 try{const next=await json('./data/'+date+'.json');if(sequence!==loading)return;edition=next;render();$('load-status').textContent='';}
 catch(e){if(sequence!==loading)return;$('load-status').textContent=e.message;if(edition)$('date').value=edition.date;}
 finally{if(sequence===loading)$('save-feedback').disabled=saving||!edition;}
}
$('date').onchange=()=>loadEdition($('date').value);
$('comment').oninput=()=>{if(edition)comments.set(edition.date,$('comment').value);};
async function loadInterests(){
 const generation=++interestsGeneration;$('interest-text').hidden=true;$('copy-interests').hidden=true;
 if(!PressFeedback.token()){$('interest-status').textContent='Verbinde deinen Zugang, um deine aktuelle Beschreibung zu lesen.';return;}
 $('interest-status').textContent='Beschreibung wird geladen …';
 try{const text=await PressFeedback.interests();if(generation!==interestsGeneration)return;$('interest-text').textContent=text;$('interest-text').hidden=false;$('copy-interests').hidden=false;$('interest-status').textContent='Die aktuelle Fassung aus deinem Redaktionsgedächtnis.';}
 catch(e){if(generation===interestsGeneration)$('interest-status').textContent=e.message;}
}
$('connect').onclick=async()=>{const b=$('connect');b.disabled=true;try{await PressFeedback.connect($('token').value.trim());$('token').value='';$('connection-status').textContent='Verbunden.';await loadInterests();}catch(e){$('connection-status').textContent=e.message;}finally{b.disabled=false;}};
$('disconnect').onclick=()=>{localStorage.removeItem(PressFeedback.tokenKey);$('interest-text').textContent='';$('connection-status').textContent='Verbindung auf diesem Gerät entfernt.';loadInterests();};
$('copy-interests').onclick=async()=>{try{await navigator.clipboard.writeText($('interest-text').textContent);$('interest-status').textContent='Beschreibung kopiert. Du kannst sie direkt zu deinem Suchprompt hinzufügen.';}catch(_){$('interest-status').textContent='Bitte den Beschreibungstext markieren und kopieren.';}};
$('save-feedback').onclick=async()=>{
 if(saving||!edition)return;
 const status=$('feedback-status');let payload;
 try{payload=JSON.parse(sessionStorage.getItem(pendingKey)||'null');}catch(_){status.textContent='Der gespeicherte Sendeentwurf ist beschädigt. Bitte diese Registerkarte neu öffnen.';return;}
 if(!payload){
  const ratings=[];
  for(const section of ['articles','headlines'])for(const item of edition[section]){
   const d=drafts.get(edition.date+':'+item.id);if(d?.dirty&&(d.rating||d.reason.trim()))ratings.push({id:item.id,title:item.title,url:item.url,section,rating:d.rating,reason:d.reason.trim()});
  }
  const comment=$('comment').value.trim();if(!ratings.length&&!comment){status.textContent='Bitte zuerst einen Artikel bewerten oder eine Rückmeldung schreiben.';return;}
  payload={version:1,submission_id:crypto.randomUUID(),date:edition.date,origin:'website-explicit',ratings,comment};
 }
 if(!PressFeedback.token()){status.textContent='Bitte zuerst deinen GitHub-Zugang verbinden. Deine Eingaben bleiben erhalten.';$('connection').open=true;return;}
 sessionStorage.setItem(pendingKey,JSON.stringify(payload));saving=true;$('save-feedback').disabled=true;$('date').disabled=true;status.textContent='Rückmeldung wird gespeichert …';
 try{
  await PressFeedback.submit(payload);sessionStorage.removeItem(pendingKey);
  for(const row of payload.ratings){const d=drafts.get(payload.date+':'+row.id);if(d&&d.rating===row.rating&&d.reason.trim()===row.reason)d.dirty=false;}
  if(edition.date===payload.date&&$('comment').value.trim()===payload.comment){$('comment').value='';comments.set(payload.date,'');}
  status.textContent='Rückmeldung für '+dateLabel(payload.date)+' gespeichert. Sie wird beim nächsten Morgenlauf gelesen. Weitere Änderungen kannst du anschließend speichern.';
 }catch(e){status.textContent=e.message+' Erneutes Speichern prüft zuerst, ob diese Rückmeldung schon angekommen ist.';}
 finally{saving=false;$('save-feedback').disabled=false;$('date').disabled=false;}
};
(async()=>{try{const index=await json('./data/index.json');for(const date of index.dates){const o=node('option',dateLabel(date));o.value=date;$('date').append(o);}if(index.dates.length)await loadEdition(index.dates[0]);else{$('load-status').textContent='Die erste recherchierte Ausgabe folgt beim nächsten Morgenlauf.';$('save-feedback').disabled=true;}await loadInterests();}catch(e){$('load-status').textContent=e.message;}})();
