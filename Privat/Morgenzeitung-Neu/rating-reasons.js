/* Explicit reason codes are separate from free text; no automatic sentiment guesses. */
'use strict';
const RatingReasons=(()=>{
  let personalized=[],currentRequest=0;
  const CHOICES=[['Thema unpassend','topic_dislike'],['Zu oberflächlich','too_shallow'],
    ['Schon bekannt','already_known'],['Zu speziell','too_niche'],
    ['Einseitige Perspektive','one_sided'],['Mehr davon','more_of_this']];
  function sync(field){
    const codes=JSON.parse(field.dataset.reasonCodes||'[]');
    field.querySelectorAll('[data-reason-code]').forEach(b=>b.setAttribute('aria-pressed',String(codes.includes(b.dataset.reasonCode))));
  }
  function decorate(){
    for(const field of document.querySelectorAll('.ratings')){
      const bar=field.querySelector('.v3-quick-reasons');
      const input=field.querySelector('.rating-reason textarea');
      if(!bar||!input)continue;
      bar.querySelectorAll('.personal-reason-choice').forEach(b=>b.remove());
      for(const phrase of personalized){
        const button=document.createElement('button');
        button.type='button';button.className='v3-reason-choice personal-reason-choice';
        button.textContent=phrase;
        button.onclick=()=>{
          const old=input.value.trim();
          const next=old?(old+'\n'+phrase):phrase;
          if(old.split('\n').some(line=>line.trim()===phrase)||next.length>input.maxLength)return;
          field.dispatchEvent(new CustomEvent('suggestionclick',{detail:phrase}));
          input.value=next;input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();
        };
        bar.append(button);
      }
    }
  }
  async function loadPrivateSuggestions(token){
    const current=++currentRequest;
    personalized=[];decorate();
    if(!token)return;
    try{
      const url='https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback/contents/morgenzeitung-neu/begruendungsvorschlaege.json';
      const response=await fetch(url,{cache:'no-store',credentials:'omit',
        headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+token}});
      if(!response.ok)return;
      const file=await response.json();
      const data=JSON.parse(new TextDecoder().decode(
        Uint8Array.from(atob(file.content.replace(/\\s/g,'')),c=>c.charCodeAt(0))));
      if(data.version!==1||!Array.isArray(data.suggestions))return;
      if(current!==currentRequest||DirectFeedback.readToken()!==token)return;
      personalized=[...new Set(data.suggestions.filter(x=>typeof x==='string').map(x=>x.trim())
        .filter(x=>x.length>=8&&x.length<=120))].slice(0,5);
      decorate();
    }catch(_){/* Non-essential private suggestions: keep generic reasons. */}
  }
  function enhance(){
    for(const box of document.querySelectorAll('.rating-reason:not([data-v3-enhanced])')){
      const input=box.querySelector('textarea'),field=box.closest('.ratings');
      if(!input||!field)continue;
      box.dataset.v3Enhanced='true';
      const toolbar=document.createElement('div');toolbar.className='v3-quick-reasons';
      toolbar.setAttribute('role','group');toolbar.setAttribute('aria-label','Optionale kurze Bewertungsgründe');
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
      input.parentNode.insertBefore(toolbar,input);box.open=true;sync(field);
    }
    decorate();
  }
  return {enhance,sync,loadPrivateSuggestions};
})();
