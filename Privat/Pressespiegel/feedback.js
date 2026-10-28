'use strict';
const PressFeedback={
 root:'https://api.github.com/repos/fabian-stoeckl/morgenzeitung-feedback',
 tokenKey:'morgenzeitung:github-token:v1',marker:'PRESSESPIEGEL_FEEDBACK_V1\n',
 token(){return localStorage.getItem(this.tokenKey)||'';},
 async api(path,options={},token=this.token()){
  if(!token)throw Error('Bitte zuerst deinen GitHub-Zugang verbinden.');
  const response=await fetch(this.root+path,{...options,cache:'no-store',headers:{Accept:'application/vnd.github+json',Authorization:'Bearer '+token,'Content-Type':'application/json',...options.headers}});
  if(!response.ok)throw Error(response.status===401?'Der GitHub-Zugang ist ungültig oder abgelaufen.':`GitHub meldet ${response.status}. Deine Rückmeldung bleibt erhalten.`);
  return response.json();
 },
 async connect(token){const repo=await this.api('',{},token);if(repo.full_name!=='fabian-stoeckl/morgenzeitung-feedback'||!repo.private)throw Error('Das Feedback-Repository konnte nicht bestätigt werden.');localStorage.setItem(this.tokenKey,token);},
 async interests(){const file=await this.api('/contents/pressespiegel/interessen.md');return new TextDecoder().decode(Uint8Array.from(atob(file.content.replace(/\s/g,'')),c=>c.charCodeAt(0)));},
 async findSubmission(id){
  for(let page=1;;page++){
   const issues=await this.api('/issues?state=all&per_page=100&page='+page);
   for(const issue of issues){
    if(issue.pull_request||!issue.body?.startsWith(this.marker))continue;
    try{const data=JSON.parse(issue.body.slice(this.marker.length));if(data.submission_id===id&&data.origin==='website-explicit'&&data.test!==true)return issue;}catch(_){}
   }
   if(issues.length<100)return null;
  }
 },
 async submit(payload){
  const found=await this.findSubmission(payload.submission_id);if(found)return found;
  const issue=await this.api('/issues',{method:'POST',body:JSON.stringify({title:'[Pressespiegel] Feedback '+payload.date,body:this.marker+JSON.stringify(payload,null,2)})});
  const confirmed=await this.api('/issues/'+issue.number);
  const data=JSON.parse(confirmed.body.slice(this.marker.length));
  if(data.submission_id!==payload.submission_id)throw Error('Speicherung noch nicht bestätigt. Bitte erneut versuchen.');
  return confirmed;
 }
};
if(typeof module!=='undefined')module.exports=PressFeedback;
