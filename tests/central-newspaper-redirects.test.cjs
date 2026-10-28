'use strict';
// No separate old folder; validate the central 404 client-side redirect
// against real and unrelated paths without fetching the public website.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('404.html', 'utf8');
const matched = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(matched,'A central 404 redirect script is required');
assert.equal(fs.existsSync('Privat/Morgenzeitung-3'),false,'Old directory must not exist');
const js=matched[1];
const cases=[
 ['/Privat/Morgenzeitung-3/','/Privat/Persoenliche-Zeitung/'],
 ['/Privat/Morgenzeitung-3/index.html','/Privat/Persoenliche-Zeitung/'],
 ['/Privat/Morgenzeitung-3/praeferenzen.html','/Privat/Persoenliche-Zeitung/praeferenzen.html'],
 ['/Privat/Morgenzeitung-3/lern-ausgabe-2026-10-28/','/Privat/Persoenliche-Zeitung/lern-ausgabe-2026-10-28/'],
 ['/Privat/Morgenzeitung-3/lern-ausgabe-2026-10-28/index.html','/Privat/Persoenliche-Zeitung/lern-ausgabe-2026-10-28/'],
 ['/privat/pressespiegel','/Privat/Persoenliche-Zeitung/'],
 ['/privat/morgenzeitung-neu','/Privat/Persoenliche-Zeitung/'],
 ['/privat/persoenliche-zeitung','/Privat/Persoenliche-Zeitung/'],
 ['/privat/etfs','/Privat/ETFs/'],
 ['/unknown/path',null],
 ['/Privat/Persoenliche-Zeitung/',null]
];
for (const [pathname,destination] of cases) {
 const calls=[];
 const location={pathname,search:'?from=old',hash:'#article',
   replace(url){calls.push(url)}};
 vm.runInNewContext(js,{window:{location}},{timeout:1000});
 if(destination)assert.deepEqual(calls,[destination+'?from=old#article'],pathname);
 else assert.equal(calls.length,0,'Unrelated pages must keep 404 status: '+pathname);
}
console.log('PASS: old folder absent, explicit 404 redirects preserve query/hash, unrelated errors untouched');
