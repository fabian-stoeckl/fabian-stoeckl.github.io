/* The standalone preference page intentionally contains NO newspaper stories or tabs.
   All private feedback remains in the owner's browser and private GitHub Issues. */
'use strict';
const $=id=>document.getElementById(id);
const el=(tag,value,cls)=>{
  const n=document.createElement(tag);
  if(value!==undefined)n.textContent=value;
  if(cls)n.className=cls;
  return n;
};
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

let currentDate='';
$('preference-comment-form').onsubmit=async event=>{
  event.preventDefault();
  const form=$('preference-comment-form'),button=event.submitter||form.querySelector('button[type=submit]');
  const field=$('preference-comment'),fresh=field.value.trim(),out=$('preference-comment-status');
  if(!fresh){out.textContent='Bitte zuerst einen Kommentar eingeben.';return;}
  if(!currentDate){out.textContent='Keine aktuelle Ausgabe geladen. Bitte später erneut versuchen.';return;}
  const token=DirectFeedback.readToken();
  if(!token){out.replaceChildren(el('span','Verbinde deinen GitHub-Zugang am Ende der Morgenzeitung, um Kommentare privat zu speichern.'));return;}
  const date=currentDate;
  button.disabled=true;
  out.textContent='Dein Kommentar wird privat zusammen mit bisherigen Bewertungen gespeichert …';
  try {
    // submit() reloads the original private issue before PATCH and preserves all article ratings.
    const saved=await DirectFeedback.savedFeedback(date,token);
    const combined=[(saved?.feedback||'').trim(),fresh].filter(Boolean).join('\n\n');
    if(combined.length>4000)throw Error('Die gesammelten Kommentare überschreiten 4000 Zeichen. Bitte kürze deinen neuen Kommentar.');
    const result=await DirectFeedback.submit(date,[],combined,token);
    field.value='';
    out.replaceChildren(
      el('span',result.existing?'Dein Kommentar ist bereits gespeichert.':'Kommentar erfolgreich privat auf GitHub gespeichert.'),
      document.createTextNode(' '));
    const view=el('a','Feedback auf GitHub ansehen ↗');
    view.href=result.html_url;view.target='_blank';view.rel='noopener noreferrer';
    out.append(view);
    await showPreferenceSummary();
  }catch(err){
    out.textContent=err.message+' Dein Kommentar bleibt im Eingabefeld erhalten.';
  }finally{button.disabled=false;}
};
(async()=>{
  try{
    DirectFeedback.resetOldTokenOnce();
    const index=await GitHubPaper.json('./data/index.json');
    currentDate=index.dates?.[0]||'';
    await showPreferenceSummary();
  }catch(err){
    $('preference-feedback').textContent='Präferenzen konnten nicht vollständig geladen werden: '+err.message;
  }
})();
