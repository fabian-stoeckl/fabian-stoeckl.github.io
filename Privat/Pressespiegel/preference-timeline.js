/* Private browser-only preference history. No user data is published. */
'use strict';
const PreferenceTimeline = {
  reconcile(history) {
    const latest=new Map();
    for(const entry of history){
      for(const rating of entry.ratings||[]){
        if(!['Sehr relevant','Teilweise relevant','Nicht relevant'].includes(rating.value))continue;
        const key=entry.date+':'+rating.id;
        const previous=latest.get(key);
        if(!previous || (entry.updated_at||'')>(previous.updated_at||'')){
          latest.set(key,{...rating,date:entry.date,updated_at:entry.updated_at||''});
        }
      }
    }
    return [...latest.values()].sort((a,b)=>a.date.localeCompare(b.date)||a.updated_at.localeCompare(b.updated_at));
  },
  calculate(history, metadata) {
    const byDay=new Map();
    for(const rating of this.reconcile(history)){
      const info=metadata.get(rating.date+':'+rating.id);
      // Only explicitly tagged in-depth articles; never infer topic from geography.
      if(!info?.topic)continue;
      const points={'Sehr relevant':1,'Teilweise relevant':0,'Nicht relevant':-1}[rating.value];
      if(!byDay.has(rating.date))byDay.set(rating.date,[]);
      byDay.get(rating.date).push({topic:info.topic,points,title:info.title||'',rating:rating.value});
    }
    const totals=new Map(),events=[];
    for(const date of [...byDay.keys()].sort()){
      const changes=new Map();
      for(const item of byDay.get(date)){
        if(!changes.has(item.topic))changes.set(item.topic,{delta:0,ratings:0});
        const change=changes.get(item.topic);
        change.delta+=item.points;
        change.ratings++;
      }
      const entries=[];
      for(const [topic,change] of [...changes].sort(([a],[b])=>a.localeCompare(b,'de'))){
        const before=totals.get(topic)||0,after=before+change.delta;
        totals.set(topic,after);
        entries.push({topic,before,after,delta:change.delta,ratings:change.ratings});
      }
      events.push({date,entries});
    }
    return events.reverse();
  }
};
if(typeof module!=='undefined')module.exports=PreferenceTimeline;
