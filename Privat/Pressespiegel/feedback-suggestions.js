'use strict';
/* UI suggestions are prompted opinions, never independently authored evidence. */
const FeedbackSuggestions=(()=>{
  const selected=new WeakMap();
  const suggestions=[
    'Das Thema interessiert mich, aber ich kannte die Inhalte schon.',
    'Mehr analytische Tiefe: Bitte Mechanismen und Folgen erklären.',
    'Zu einseitig: Ich hätte gern auch fundierte Gegenpositionen.',
    'Mehr neue Erkenntnisse statt kurzer Ankündigungen.',
    'Mehr konkrete Daten und Auswirkungen für Österreich.',
    'Mehr davon: Diese Analyse hat mir eine neue Sichtweise eröffnet.'
  ];
  const containsLine=(value,phrase)=>String(value).split('\n').some(line=>line.trim()===phrase);
  function getSelected(field){
    return (selected.get(field)||[]).filter(s=>containsLine(field.value,s));
  }
  function setSelected(field,items){
    selected.set(field,[...new Set((Array.isArray(items)?items:[])
      .filter(s=>typeof s==='string'&&containsLine(field.value,s)))]);
  }
  function enhance(field){
    const bar=document.createElement('div');bar.className='feedback-suggestions';
    bar.setAttribute('role','group');bar.setAttribute('aria-label','Freiwillige Vorschläge für genaueres Feedback');
    const hint=document.createElement('p');hint.className='small';
    hint.textContent='Genaueres Feedback hilft beim Lernen. Ergänze beispielsweise (freiwillig):';
    bar.append(hint);
    for(const phrase of suggestions){
      const button=document.createElement('button');
      button.type='button';button.textContent=phrase;
      button.onclick=()=>{
        if(containsLine(field.value,phrase)||field.value.length+phrase.length+1>field.maxLength)return;
        field.value+=(field.value.trim()?'\n':'')+phrase;
        setSelected(field,[...getSelected(field),phrase]);
        field.dispatchEvent(new Event('input',{bubbles:true}));field.focus();
      };
      bar.append(button);
    }
    field.addEventListener('input',()=>setSelected(field,getSelected(field)));
    field.before(bar);
  }
  for(const id of ['feedback','preference-comment']){
    const field=document.getElementById(id);
    if(field)enhance(field);
  }
  return {getSelected,setSelected};
})();
