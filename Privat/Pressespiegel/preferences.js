'use strict';
const byId=id=>document.getElementById(id);
const root='https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback';
async function privateFile(path){
 const token=DirectFeedback.readToken();
 if(!token)throw Error('Bitte zuerst deinen GitHub-Zugang auf der Zeitungsseite verbinden.');
 const r=await fetch(root+'/contents/'+path,{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+token}});
 if(!r.ok){
  const err=Error('Privater Zugriff fehlgeschlagen (HTTP '+r.status+'). Bitte die Berechtigung Contents: Read prüfen.');
  err.status=r.status;
  throw err;
 }
 const file=await r.json();
 return new TextDecoder().decode(Uint8Array.from(atob(String(file.content||'').replace(/\s/g,'')),c=>c.charCodeAt(0)));
}
function show(id,text){byId(id).textContent=text;}
async function refresh(){
 const token=DirectFeedback.readToken();
 if(!token){
  show('profile-status','Verbinde deinen GitHub-Zugang auf der Zeitungsseite, um deine persönliche Beschreibung zu lesen.');
  show('feedback-summary','Ohne Verbindung sind keine persönlichen Bewertungen sichtbar.');
  show('profile-changes','Die Änderungen werden nach der Verbindung angezeigt.');
  show('learning-monitor','Verbinde deinen GitHub-Zugang, um deine private Lernbilanz zu lesen.');
  return;
 }
 const tasks=[
  privateFile('morgenzeitung-neu/interessen.md').then(t=>{byId('profile-text').textContent=t;byId('profile-text').hidden=false;show('profile-status','Aktuelle Fassung aus dem privaten Redaktionsgedächtnis.');}).catch(e=>show('profile-status',e.message)),
  privateFile('morgenzeitung-neu/aenderungen.md').then(t=>show('profile-changes',t)).catch(e=>show('profile-changes',e.message)),
  privateFile('morgenzeitung-neu/lernmonitoring.md')
    .then(t=>show('learning-monitor',t.trim()||'Noch keine belastbare Lernbilanz vorhanden.'))
    .catch(e=>show('learning-monitor',e.status===404
      ?'Noch keine Lernbilanz vorhanden. Sie beginnt nach den ersten echten Ausgaben und Rückmeldungen.'
      :'Lernbilanz konnte nicht privat gelesen werden: '+e.message)),
  DirectFeedback.feedbackHistory(token).then(history=>{
    const ratings=new Map();
    // Latest explicitly saved article state wins; earlier issue versions are not extra votes.
    for(const x of [...history].sort((a,b)=>a.updated_at.localeCompare(b.updated_at)))
      for(const y of x.ratings||[])ratings.set(x.date+':'+y.id,{date:x.date,...y});
    const all=[...ratings.values()];
    const count=all.filter(x=>x.value);
    const notesOnly=all.filter(x=>!x.value&&(x.reason?.trim()||
      x.reason_codes?.length||x.suggested_reasons?.length));
    const intro=document.createElement('p');
    intro.textContent=history.length+' Ausgabe-Rückmeldungen, '+count.length+' aktuell bewertete Artikel, '+
      notesOnly.length+' qualitative Artikelhinweise ohne Relevanzstufe, '+
      history.filter(x=>x.feedback.trim()).length+
      ' allgemeine Kommentare. Historische Urteile der früheren Zeitungen wurden nicht als neue Bewertungen gezählt.';
    const list=document.createElement('ul');list.className='preference-list';
    const labels={topic_dislike:'Thema unpassend',too_shallow:'Zu oberflächlich',already_known:'Schon bekannt',too_niche:'Zu speziell',one_sided:'Einseitige Perspektive',more_of_this:'Mehr davon'};
    for(const x of all.filter(y=>y.value||y.reason?.trim()||y.reason_codes?.length||y.suggested_reasons?.length).slice(-10).reverse()){
      const li=document.createElement('li');
      const reasons=(x.reason_codes||[]).map(s=>labels[s]||s);
      li.textContent=x.date+' · '+(x.value||'Artikelhinweis ohne Relevanzstufe')+
        (reasons.length?' · '+reasons.join(', '):'')+(x.reason?' · '+x.reason:'');
      list.append(li);
    }
    byId('feedback-summary').replaceChildren(intro,list);
  }).catch(e=>show('feedback-summary','Bewertungen konnten nicht gelesen werden: '+e.message))
 ];await Promise.all(tasks);
}
// The index is intentionally fetched only at submission. Page-load dates become
// stale for readers who leave the preferences page open across publication.
void refresh();
byId('preference-comment-form').onsubmit=async e=>{
 e.preventDefault();const field=byId('preference-comment'),comment=field.value.trim(),status=byId('preference-comment-status'),button=e.submitter||byId('preference-comment-form').querySelector('button[type=submit]');
 if(!comment){status.textContent='Bitte zuerst eine konkrete Rückmeldung eingeben.';return;}
 const token=DirectFeedback.readToken();if(!token){status.textContent='Bitte auf der Zeitungsseite deinen GitHub-Zugang verbinden.';return;}
 button.disabled=true;status.textContent='Prüfe die neueste Ausgabe und speichere deine Rückmeldung privat …';
 try{
  // This page may remain open overnight. A date captured at page-load would
  // silently attach today's feedback to yesterday's publication.
  const index=await GitHubPaper.json('./data/index.json');
  const currentDate=index?.dates?.[0];
  if(typeof currentDate!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(currentDate))
    throw Error('Die aktuelle Ausgabe konnte nicht sicher bestimmt werden.');
  await DirectFeedback.appendComment(currentDate,comment,token,localStorage,fetch,
    {commentSuggestions:FeedbackSuggestions.getSelected(field)});
  field.value='';FeedbackSuggestions.setSelected(field,[]);
  status.textContent='Gespeichert zur Ausgabe '+currentDate+'. Der nächste Lauf prüft deine Rückmeldung.';
  await refresh();
 }
 catch(e){status.textContent=e.message+' Deine Eingabe bleibt erhalten.';}
 finally{button.disabled=false;}
};
