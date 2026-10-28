/* Optional editorial context for the only Persönliche Zeitung reader.
 * No publisher-access ranking signals. All DOM enrichment is explicitly
 * scheduled by app.js and mapped by stable article ID, never card order.
 */
'use strict';
const EditorialExtras=(()=>{
  const safeLink=(label,url)=>{
    try{
      const u=new URL(url);
      if(u.protocol!=='https:'||u.username||u.password)return null;
      const a=document.createElement('a');a.textContent=label;a.href=u.href;
      a.target='_blank';a.rel='noopener noreferrer';return a;
    }catch(_){return null}
  };
  function articleContext(edition){
    if(!edition||!Array.isArray(edition.articles))return;
    const byId=new Map([...document.querySelectorAll('#articles article[data-article-id]')]
      .map(node=>[node.dataset.articleId,node]));
    edition.articles.forEach((story,i)=>{
      const node=byId.get(String(story.id));
      if(!node||node.dataset.v3Context===story.id)return;
      node.dataset.v3Context=story.id;
      const body=node.querySelector('.body');
      if(!body)return;
      node.querySelectorAll('.v3-extra-context').forEach(x=>x.remove());
      const meta=document.createElement('p');meta.className='v3-extra-context small';
      const genre=String(story.article_type||story.kind||'').trim();
      // A technically accessible full text is not evidence that it was read.
      const evidence=String(story.evidence_level||story.level||'unknown').toLowerCase();
      const evidenceText={
        'headline':'Quelle: Überschrift/Metadaten',
        'teaser':'Quelle: Vorspann',
        'read':'Quelle: gelesener Originaltext',
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
  function comparisons(edition){
    if(!edition)return;
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
  function render(edition){
    articleContext(edition);
    comparisons(edition);
  }

  function enrichFeedback(edition,rawText){
    const previous=String(rawText||'').replace(/(?:^|\n)\[V3-Vergleich [^\n]*\]/g,'').trim();
    if(!edition)return previous;
    const notes=[];
    for(const field of document.querySelectorAll('#v3-comparisons fieldset')){
      const checked=field.querySelector('input[type=radio]:checked');
      if(!checked)continue;
      notes.push('[V3-Vergleich '+edition.date+' '+field.dataset.comparisonId+': '+checked.value+']');
    }
    const next=[previous,...notes].filter(Boolean).join('\n');
    if(next.length>4000)throw Error('Die Rückmeldung ist zu lang. Bitte etwas kürzen.');
    return next;
  }

  return {render,enrichFeedback};
})();
