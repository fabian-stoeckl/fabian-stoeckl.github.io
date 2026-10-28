/* Optional short rating reasons in the only Persönliche Zeitung reader.
 * Nothing leaves the browser before the reader explicitly saves feedback.
 */
'use strict';
const RatingReasons=(()=>{
  const CHOICES=[
    ['Thema unpassend','Thema interessiert mich nicht'],
    ['Zu oberflächlich','Zu oberflächlich'],
    ['Schon bekannt','Schon bekannt'],
    ['Zu speziell','Zu speziell'],
    ['Einseitige Perspektive','Einseitig, andere Perspektive gewünscht'],
    ['Mehr davon','Mehr davon']
  ];
  function enhance(){
    for(const box of document.querySelectorAll('.rating-reason:not([data-v3-enhanced])')){
      const input=box.querySelector('textarea');
      if(!input)continue;
      box.dataset.v3Enhanced='true';
      const toolbar=document.createElement('div');
      toolbar.className='v3-quick-reasons';
      toolbar.setAttribute('role','group');
      toolbar.setAttribute('aria-label','Optionale kurze Bewertungsgründe');
      const hint=document.createElement('p');hint.className='small';
      hint.textContent='Optionaler Grund – unterscheide Themenfit, Tiefe und Neuigkeitswert:';
      toolbar.append(hint);
      for(const [label,value] of CHOICES){
        const button=document.createElement('button');
        button.type='button';button.className='v3-reason-choice';
        button.textContent=label;
        button.addEventListener('click',()=>{
          const existing=input.value.trim();
          const pieces=existing.split(/[,;]\s*/).map(s=>s.trim()).filter(Boolean);
          if(!pieces.some(x=>x.toLowerCase()===value.toLowerCase())){
            input.value=[existing,value].filter(Boolean).join(existing?', ':'');
            input.dispatchEvent(new Event('input',{bubbles:true}));
          }
          box.open=true;
          input.focus();
        });
        toolbar.append(button);
      }
      input.parentNode.insertBefore(toolbar,input);
    }
  }
  return {enhance};
})();