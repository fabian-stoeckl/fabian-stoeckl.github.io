/* Additional editorial context ONLY for Morgenzeitung 3.
 * Never uses a publisher's technical access or full-text status as a
 * ranking signal. Does not alter the shared V1/V2 reader application.
 */
'use strict';
(function(){
  const safeLink=(label,url)=>{
    try{
      const u=new URL(url);
      if(u.protocol!=='https:'||u.username||u.password)return null;
      const a=document.createElement('a');a.textContent=label;a.href=u.href;
      a.target='_blank';a.rel='noopener noreferrer';return a;
    }catch(_){return null}
  };
  function articleContext(){
    if(typeof edition==='undefined'||!edition||!Array.isArray(edition.articles))return;
    const cards=document.querySelectorAll('#articles article');
    edition.articles.forEach((story,i)=>{
      const node=cards[i];
      if(!node||node.dataset.v3Context===story.id)return;
      node.dataset.v3Context=story.id;
      const body=node.querySelector('.body');
      if(!body)return;
      node.querySelectorAll('.v3-extra-context').forEach(x=>x.remove());
      const meta=document.createElement('p');meta.className='v3-extra-context small';
      const genre=String(story.article_type||story.kind||'').trim();
      const evidence=String(story.evidence_level||story.level||story.access||'unknown').toLowerCase();
      const evidenceText={
        'headline':'Quelle: Überschrift/Metadaten',
        'teaser':'Quelle: Vorspann',
        'read':'Quelle: gelesener Originaltext',
        'full':'Quelle: gelesener Originaltext',
        'unknown':'Quellentiefe noch nicht dokumentiert'
      }[evidence]||'Quellentiefe noch nicht dokumentiert';
      meta.textContent=[genre,evidenceText].filter(Boolean).join(' · ');
      body.append(meta);
      if(i>=3)return;
      const why=String(story.why_selected||'').trim();
      if(why){
        const reason=document.createElement('p');reason.className='v3-extra-context v3-why';
        const strong=document.createElement('strong');strong.textContent='Warum ausgewählt: ';
        reason.append(strong,document.createTextNode(why));
        body.append(reason);
      }
    });
  }
  function comparisons(){
    if(typeof edition==='undefined'||!edition)return;
    const root=document.getElementById('feedback-section');
    if(!root)return;
    const rows=Array.isArray(edition.editorial_comparisons)?
      edition.editorial_comparisons.slice(0,2):[];
    const key=edition.date+':'+rows.map(x=>x.id||'').join(':');
    const old=document.getElementById('v3-comparisons');
    if(old&&old.dataset.current===key)return;
    if(old)old.remove();
    if(!rows.length)return;
    const section=document.createElement('section');section.id='v3-comparisons';
    section.dataset.current=key;section.className='v3-optional-comparisons';
    const title=document.createElement('h3');
    title.textContent='Optional: Welcher Artikel wäre nützlicher gewesen?';
    const intro=document.createElement('p');intro.className='small';
    intro.textContent='Vergleiche höchstens zwei echte Alternativen. Die Entscheidung ist freiwillig und wird nur beim normalen Feedback-Speichern übertragen.';
    section.append(title,intro);
    rows.forEach((x,i)=>{
      if(!x||!x.id||!x.selected_title||!x.alternative_title)return;
      const selected=safeLink(x.selected_title,x.selected_url);
      const alternative=safeLink(x.alternative_title,x.alternative_url);
      if(!selected||!alternative)return;
      const field=document.createElement('fieldset');field.className='v3-comparison';
      field.dataset.comparisonId=String(x.id).slice(0,90);
      const legend=document.createElement('legend');legend.textContent='Vergleich '+(i+1);
      field.append(legend);
      for(const [caption,node] of [['In der Zeitung: ',selected],['Alternative: ',alternative]]){
        const p=document.createElement('p');p.className='small';
        p.append(document.createTextNode(caption),node);field.append(p);
      }
      const id='v3-compare-'+edition.date+'-'+i;
      for(const [label,value] of [
        ['Ausgewählter Artikel besser','published'],
        ['Alternative besser','alternative'],
        ['Beide ähnlich hilfreich','equal']
      ]){
        const wrap=document.createElement('label');wrap.className='v3-comparison-option';
        const radio=document.createElement('input');radio.type='radio';radio.name=id;radio.value=value;
        wrap.append(radio,document.createTextNode(' '+label));field.append(wrap);
      }
      section.append(field);
    });
    const form=root.querySelector('form');
    root.insertBefore(section,form);
  }
  function enhance(){articleContext();comparisons();}
  document.addEventListener('DOMContentLoaded',()=>{
    const container=document.getElementById('newspaper-view');
    if(container){
      const mo=new MutationObserver(enhance);
      mo.observe(container,{childList:true,subtree:true});
    }
    enhance();
    // Use existing V3 issue/comment persistence and preserve all older ratings.
    const form=document.getElementById('feedback-form');
    if(form)form.addEventListener('submit',()=>{
      if(typeof edition==='undefined'||!edition)return;
      const textarea=document.getElementById('feedback');
      if(!textarea)return;
      const notes=[];
      for(const field of document.querySelectorAll('#v3-comparisons fieldset')){
        const checked=field.querySelector('input[type=radio]:checked');
        if(!checked)continue;
        notes.push('[V3-Vergleich '+edition.date+' '+field.dataset.comparisonId+': '+checked.value+']');
      }
      if(!notes.length)return;
      const previous=textarea.value.replace(/(?:^|\n)\[V3-Vergleich [^\n]*\]/g,'').trim();
      const next=[previous,...notes].filter(Boolean).join('\n');
      if(next.length<=4000)textarea.value=next;
    },true);
  });
})();