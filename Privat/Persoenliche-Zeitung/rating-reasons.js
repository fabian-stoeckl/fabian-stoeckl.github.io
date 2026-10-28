/* Explicit reason codes are separate from free text; no automatic sentiment guesses. */
'use strict';
const RatingReasons=(()=>{
  const CHOICES=[['Thema unpassend','topic_dislike'],['Zu oberflächlich','too_shallow'],
    ['Schon bekannt','already_known'],['Zu speziell','too_niche'],
    ['Einseitige Perspektive','one_sided'],['Mehr davon','more_of_this']];
  function sync(field){
    const codes=JSON.parse(field.dataset.reasonCodes||'[]');
    field.querySelectorAll('[data-reason-code]').forEach(b=>b.setAttribute('aria-pressed',String(codes.includes(b.dataset.reasonCode))));
  }
  function enhance(){
    for(const box of document.querySelectorAll('.rating-reason:not([data-v3-enhanced])')){
      const input=box.querySelector('textarea'),field=box.closest('.ratings');
      if(!input||!field)continue;
      box.dataset.v3Enhanced='true';
      const toolbar=document.createElement('div');toolbar.className='v3-quick-reasons';
      toolbar.setAttribute('role','group');toolbar.setAttribute('aria-label','Optionale kurze Bewertungsgründe');
      const hint=document.createElement('p');hint.className='small';
      hint.textContent='Optionale Gründe auswählen; eigener Text bleibt separat:';toolbar.append(hint);
      for(const [label,code] of CHOICES){
        const b=document.createElement('button');b.type='button';b.className='v3-reason-choice';
        b.textContent=label;b.dataset.reasonCode=code;
        b.onclick=()=>{
          const codes=new Set(JSON.parse(field.dataset.reasonCodes||'[]'));
          codes.has(code)?codes.delete(code):codes.add(code);
          const selected=[...codes].sort();field.dataset.reasonCodes=JSON.stringify(selected);
          sync(field);field.dispatchEvent(new CustomEvent('reasoncodes',{detail:selected}));box.open=true;
        };toolbar.append(b);
      }
      input.parentNode.insertBefore(toolbar,input);sync(field);
    }
  }
  return {enhance,sync};
})();
