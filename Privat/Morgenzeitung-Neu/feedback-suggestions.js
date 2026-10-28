'use strict';
/* Suggestions never send feedback or create a preference automatically. */
(()=>{
const suggestions=[
'Das Thema interessiert mich, aber ich kannte die Inhalte schon.',
'Mehr analytische Tiefe: Bitte Mechanismen und Folgen erklären.',
'Zu einseitig: Ich hätte gern auch fundierte Gegenpositionen.',
'Mehr neue Erkenntnisse statt kurzer Ankündigungen.',
'Mehr konkrete Daten und Auswirkungen für Österreich.',
'Mehr davon: Diese Analyse hat mir eine neue Sichtweise eröffnet.'
];
for(const id of ['feedback','preference-comment']){
const field=document.getElementById(id);if(!field)continue;
const bar=document.createElement('div');bar.className='feedback-suggestions';bar.setAttribute('role','group');bar.setAttribute('aria-label','Freiwillige Vorschläge für genaueres Feedback');
const hint=document.createElement('p');hint.className='small';
hint.textContent='Genaueres Feedback hilft beim Lernen. Ergänze beispielsweise (freiwillig):';
bar.append(hint);
for(const s of suggestions){
 const b=document.createElement('button');b.type='button';b.textContent=s;
 b.onclick=()=>{if(field.value.includes(s))return;field.value+=(field.value.trim()?'\n':'')+s;field.dispatchEvent(new Event('input',{bubbles:true}));field.focus();};
 bar.append(b);
}
field.before(bar);
}
})();