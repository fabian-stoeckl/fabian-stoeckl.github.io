'use strict';
/* UI suggestions are prompted opinions, never independently authored evidence. */
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
  let personalized=[];
  let request=0;
  const bars=[];
  const containsLine=(value,phrase)=>String(value).split('\n').some(line=>line.trim()===phrase);
  function getSelected(field){
    return (selected.get(field)||[]).filter(s=>containsLine(field.value,s));
  }
  function setSelected(field,items){
    selected.set(field,[...new Set((Array.isArray(items)?items:[])
      .filter(s=>typeof s==='string'&&containsLine(field.value,s)))]);
  }
  function renderButtons(choices,field){
    choices.replaceChildren();
    for(const phrase of [...new Set([...personalized,...defaults])].slice(0,9)){
      const button=document.createElement('button');
      button.type='button';button.textContent=phrase;
      button.onclick=()=>{
        if(containsLine(field.value,phrase)||field.value.length+phrase.length+1>field.maxLength)return;
        field.value+=(field.value.trim()?'\n':'')+phrase;
        setSelected(field,[...getSelected(field),phrase]);
        field.dispatchEvent(new Event('input',{bubbles:true}));field.focus();
      };
      choices.append(button);
    }
  }
  function enhance(field){
    const bar=document.createElement('div');bar.className='feedback-suggestions';
    bar.setAttribute('role','group');bar.setAttribute('aria-label','Freiwillige Vorschläge für genaueres Feedback');
    const hint=document.createElement('p');hint.className='small';
    hint.textContent='Genaueres Feedback hilft beim Lernen. Ergänze beispielsweise (freiwillig):';
    bar.append(hint);
    const choices=document.createElement('div');
    choices.className='feedback-suggestion-buttons';
    bar.append(choices);
    bars.push({choices,field});
    renderButtons(choices,field);
    field.addEventListener('input',()=>setSelected(field,getSelected(field)));
    field.before(bar);
  }
  for(const id of ['feedback','preference-comment']){
    const field=document.getElementById(id);
    if(field)enhance(field);
  }
  async function loadPrivateSuggestions(token){
    const version=++request;
    personalized=[];
    for(const {choices,field} of bars)renderButtons(choices,field);
    if(!token)return;
    try{
      const url='https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback/contents/morgenzeitung-neu/begruendungsvorschlaege.json';
      const response=await fetch(url,{cache:'no-store',credentials:'omit',
        headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+token}});
      if(!response.ok)return;
      const file=await response.json();
      const data=JSON.parse(new TextDecoder().decode(
        Uint8Array.from(atob(file.content.replace(/\s/g,'')),x=>x.charCodeAt(0))));
      if(version!==request||DirectFeedback.readToken()!==token)return;
      if(data.version!==1||!Array.isArray(data.general_suggestions))return;
      personalized=[...new Set(data.general_suggestions.filter(x=>typeof x==='string')
        .map(x=>x.trim()).filter(x=>x.length>=8&&x.length<=160))].slice(0,5);
      for(const {choices,field} of bars)renderButtons(choices,field);
    }catch(_){/* Static buttons remain available without private data. */}
  }
  return {getSelected,setSelected,loadPrivateSuggestions};
})();
