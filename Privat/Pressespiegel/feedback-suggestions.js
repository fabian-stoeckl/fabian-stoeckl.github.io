'use strict';
/* Suggested text is an explicit user action, not independently authored evidence.
 * Optional personalized suggestions are read ONLY from the private repository,
 * never from the public newspaper JSON or anonymous browser analytics.
 */
const FeedbackSuggestions=(()=>{
  const selected=new WeakMap();
  const defaults=[
    'Das Thema interessiert mich, aber ich kannte die Inhalte schon.',
    'Mehr analytische Tiefe: Bitte Mechanismen und Folgen erklären.',
    'Zu einseitig: Ich hätte gern auch fundierte Gegenpositionen.',
    'Mehr neue Erkenntnisse statt kurzer Ankündigungen.',
    'Mehr konkrete Daten und Auswirkungen für Österreich.',
    'Mehr davon: Diese Analyse hat mir eine neue Sichtweise eröffnet.'
  ];
  let personalized=[],currentRequest=0;
  const fields=['feedback','preference-comment'].map(id=>document.getElementById(id)).filter(Boolean);
  const containsLine=(value,phrase)=>String(value).split('\n').some(line=>line.trim()===phrase);
  function getSelected(field){
    return (selected.get(field)||[]).filter(s=>containsLine(field.value,s));
  }
  function setSelected(field,items){
    selected.set(field,[...new Set((Array.isArray(items)?items:[])
      .filter(s=>typeof s==='string'&&containsLine(field.value,s)))]);
  }
  function choice(field,phrase){
    const button=document.createElement('button');
    button.type='button';button.textContent=phrase;
    button.onclick=()=>{
      if(containsLine(field.value,phrase)||field.value.length+phrase.length+1>field.maxLength)return;
      field.value+=(field.value.trim()?'\n':'')+phrase;
      // Record the click *before* notifying the draft handler, so it stays a
      // prompted selection even when followed by a separately authored line.
      setSelected(field,[...getSelected(field),phrase]);
      field.dispatchEvent(new Event('input',{bubbles:true}));field.focus();
    };
    return button;
  }
  function renderPrivate(){
    for(const field of fields){
      const privateGroup=field.parentElement.querySelector('.feedback-suggestions-private');
      if(!privateGroup)continue;
      privateGroup.replaceChildren();
      privateGroup.hidden=personalized.length===0;
      if(!personalized.length)continue;
      const label=document.createElement('p');label.className='small';
      label.textContent='Weitere Vorschläge aus wiederkehrenden eigenen Rückmeldungen (freiwillig):';
      privateGroup.append(label);
      for(const phrase of personalized)privateGroup.append(choice(field,phrase));
    }
  }
  function enhance(field){
    const bar=document.createElement('div');bar.className='feedback-suggestions';
    bar.setAttribute('role','group');bar.setAttribute('aria-label','Freiwillige Vorschläge für genaueres Feedback');
    const hint=document.createElement('p');hint.className='small';
    hint.textContent='Genaueres Feedback hilft beim Lernen. Ergänze beispielsweise (freiwillig):';
    bar.append(hint);
    for(const phrase of defaults)bar.append(choice(field,phrase));
    const privateGroup=document.createElement('div');privateGroup.className='feedback-suggestions-private';
    privateGroup.hidden=true;privateGroup.setAttribute('role','group');
    privateGroup.setAttribute('aria-label','Zusätzliche Vorschläge aus deinen eigenen Rückmeldungen');
    bar.append(privateGroup);
    field.addEventListener('input',()=>setSelected(field,getSelected(field)));
    field.before(bar);
  }
  for(const field of fields)enhance(field);
  async function loadPrivateSuggestions(token){
    const request=++currentRequest;
    personalized=[];renderPrivate();
    if(!token)return;
    try{
      const url='https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback/contents/morgenzeitung-neu/begruendungsvorschlaege.json';
      const response=await fetch(url,{cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',
        headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+token}});
      if(!response.ok)return;
      const file=await response.json();
      const data=JSON.parse(new TextDecoder().decode(Uint8Array.from(
        atob(String(file.content||'').replace(/\s/g,'')),c=>c.charCodeAt(0))));
      // Version 1 remains backwards compatible: general_suggestions is optional.
      if(data.version!==1||!Array.isArray(data.general_suggestions))return;
      const excluded=new Set(defaults.map(s=>s.toLocaleLowerCase('de')));
      const next=[];
      for(const item of data.general_suggestions){
        if(typeof item!=='string')continue;
        const phrase=item.trim(),key=phrase.toLocaleLowerCase('de');
        if(phrase.length<12||phrase.length>160||/[\r\n\u0000-\u001f]/.test(phrase)
            ||excluded.has(key))continue;
        excluded.add(key);next.push(phrase);
        if(next.length===5)break;
      }
      if(request!==currentRequest||DirectFeedback.readToken()!==token)return;
      personalized=next;renderPrivate();
    }catch(_){/* Private suggestions are optional; never block free feedback. */}
  }
  return {getSelected,setSelected,loadPrivateSuggestions};
})();