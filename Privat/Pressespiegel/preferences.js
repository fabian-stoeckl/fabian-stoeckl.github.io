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
    const count=[...ratings.values()].filter(x=>x.value);
    const intro=document.createElement('p');
    intro.textContent=history.length+' Ausgabe-Rückmeldungen, '+count.length+' aktuell bewertete Artikel, '+history.filter(x=>x.feedback.trim()).length+' allgemeine Kommentare. Historische Urteile der früheren Zeitungen wurden nicht als neue Bewertungen gezählt.';
    const list=document.createElement('ul');list.className='preference-list';
    const labels={topic_dislike:'Thema unpassend',too_shallow:'Zu oberflächlich',already_known:'Schon bekannt',too_niche:'Zu speziell',one_sided:'Einseitige Perspektive',more_of_this:'Mehr davon'};
    for(const x of count.slice(-10).reverse()){
      const li=document.createElement('li');
      const reasons=(x.reason_codes||[]).map(s=>labels[s]||s);
      li.textContent=x.date+' · '+x.value+(reasons.length?' · '+reasons.join(', '):'')+(x.reason?' · '+x.reason:'');
      list.append(li);
    }
    byId('feedback-summary').replaceChildren(intro,list);
  }).catch(e=>show('feedback-summary','Bewertungen konnten nicht gelesen werden: '+e.message))
 ];await Promise.all(tasks);
}
let latestDate='';
(async()=>{
 try{const index=await GitHubPaper.json('./data/index.json');latestDate=index.dates?.[0]||'';}
 catch(e){show('preference-comment-status','Ausgabenindex nicht erreichbar: '+e.message);}
 await refresh();
})();
byId('preference-comment-form').onsubmit=async e=>{
 e.preventDefault();const field=byId('preference-comment'),comment=field.value.trim(),status=byId('preference-comment-status'),button=e.submitter;
 if(!comment){status.textContent='Bitte zuerst eine konkrete Rückmeldung eingeben.';return;}
 if(!latestDate){status.textContent='Es ist noch keine Ausgabe vorhanden.';return;}
 const token=DirectFeedback.readToken();if(!token){status.textContent='Bitte auf der Zeitungsseite deinen GitHub-Zugang verbinden.';return;}
 button.disabled=true;status.textContent='Speichere deine Rückmeldung privat …';
 try{
  await DirectFeedback.appendComment(latestDate,comment,token,localStorage,fetch,
    {commentSuggestions:FeedbackSuggestions.getSelected(field)});
  field.value='';FeedbackSuggestions.setSelected(field,[]);
  status.textContent='Gespeichert. Der nächste Lauf prüft, ob die Interessenbeschreibung dadurch besser wird.';
  await refresh();
 }
 catch(e){status.textContent=e.message+' Deine Eingabe bleibt erhalten.';}
 finally{button.disabled=false;}
};
