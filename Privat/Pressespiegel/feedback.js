'use strict';
const PaperFeedback={
  async send(endpoint,data){
    if(!endpoint)throw Error('Direkter Versand ist noch nicht verbunden. Deine Eingaben bleiben in diesem Tab erhalten.');
    const url=new URL(endpoint);
    if(url.protocol!=='https:'||url.username||url.password||url.pathname!=='/feedback')throw Error('Ungültige Feedback-Verbindung.');
    let response;
    try{response=await fetch(url.href,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),credentials:'omit',redirect:'error',referrerPolicy:'no-referrer',signal:AbortSignal.timeout(90000)});}
    catch(e){throw Error('Keine Bestätigung erhalten. Eingaben bleiben erhalten; erneutes Senden prüft auf Dubletten.');}
    const result=await response.json();
    if(!response.ok||result.ok!==true)throw Error(result.error||'Speicherung nicht bestätigt.');
    return result;
  }
};
if(typeof module!=='undefined')module.exports=PaperFeedback;
