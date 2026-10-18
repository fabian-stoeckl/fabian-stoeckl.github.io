'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {run} = require('../scripts/website-context.cjs');
const root = path.resolve(__dirname,'..');
const current=run(root);
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'website-context-'));
try {
 fs.mkdirSync(path.join(tmp,'docs/website-context'),{recursive:true});
 fs.writeFileSync(path.join(tmp,'_config.yml'),'exclude:\n  - docs\n');
 fs.writeFileSync(path.join(tmp,'AGENTS.md'),'docs/website-context/README.md');
 fs.writeFileSync(path.join(tmp,'index.md'),'# Home');
 const protocol=(name,paths)=>`<!-- website-area: ${JSON.stringify({name,paths})} -->\n# ${name}\n\n**Stand:** 01.01.2027\n\n## Offen\nKeine.\n`;
 fs.writeFileSync(path.join(tmp,'docs/website-context/Home.md'),protocol('Home',['index.md']));
 run(tmp,true);run(tmp);
 // Arbitrary additional area: no changes to validator required.
 fs.mkdirSync(path.join(tmp,'Privat/NewArea'),{recursive:true});
 fs.writeFileSync(path.join(tmp,'Privat/NewArea/index.html'),'<h1>New</h1>');
 assert.throws(()=>run(tmp),/Unregistered website page/);
 fs.writeFileSync(path.join(tmp,'docs/website-context/NewArea.md'),protocol('New area',['Privat/NewArea/']));
 assert.throws(()=>run(tmp),/Registry outdated/);
 run(tmp,true);assert.equal(run(tmp).length,2);
 fs.writeFileSync(path.join(tmp,'docs/website-context/Planned.md'),protocol('Planned',[]));run(tmp,true);assert.equal(run(tmp).length,3);
 fs.writeFileSync(path.join(tmp,'docs/website-context/Fourth.md'),protocol('Fourth',[]));run(tmp,true);assert.equal(run(tmp).length,4);
 fs.writeFileSync(path.join(tmp,'docs/website-context/Bad.md'),protocol('Bad',['../outside']));assert.throws(()=>run(tmp),/unsafe source path/);fs.unlinkSync(path.join(tmp,'docs/website-context/Bad.md'));
 fs.writeFileSync(path.join(tmp,'docs/website-context/Duplicate.md'),protocol('Home',[]));assert.throws(()=>run(tmp),/Duplicate area/);fs.unlinkSync(path.join(tmp,'docs/website-context/Duplicate.md'));
 fs.unlinkSync(path.join(tmp,'docs/website-context/Fourth.md'));assert.throws(()=>run(tmp),/Registry outdated/);run(tmp,true);
 fs.writeFileSync(path.join(tmp,'_config.yml'),'exclude: []\n');assert.throws(()=>run(tmp),/docs must be excluded/);
} finally {fs.rmSync(tmp,{recursive:true,force:true});}
console.log(`PASS: ${current.length} real areas and dynamic registration/failure fixtures`);
