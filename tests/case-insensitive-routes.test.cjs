'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const template = fs.readFileSync('404.html', 'utf8');
assert.match(template, /^---\nlayout: null\n---\n/, 'Jekyll must render the route manifest');

const paths = [
  '/index.html',
  '/Privat/index.html',
  '/Privat/ETFs/index.html',
  '/Privat/ETFs/data/etf_data.json',
  '/Privat/Pressespiegel/index.html',
  '/Privat/Pressespiegel/praeferenzen.html',
  '/Privat/Pressespiegel/data/2099-12-31.json',
  '/Privat/Pressespiegel/direct-feedback.js',
  '/Hochzeit/index.html',
  '/Hochzeit/danke.html',
  '/Hochzeit/einladung.svg',
  // Existing compatibility redirects must lose to canonical URLs.
  '/privat/index.html',
  '/Privat/etfs/index.html',
  '/privat/ETFs/index.html',
  '/hochzeit/index.html'
];

const source = template.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(source, '404 redirect script must be present');
const rendered = source
  .replace(/\{% for file in site\.static_files %\}[\s\S]*?\{% endfor %\}/,
    paths.map(p => JSON.stringify(p) + ',').join('\n'))
  .replace(/\{% for page in site\.pages %\}[\s\S]*?\{% endfor %\}/, '');
assert.doesNotMatch(rendered, /\{%|\{\{/, 'Liquid replacements must be complete');

function resolve(pathname, search = '', hash = '') {
  let redirected = null;
  const window = {location: {pathname, search, hash, replace: target => {redirected = target;}}};
  vm.runInNewContext(rendered, {window}, {timeout: 200});
  return redirected;
}

const examples = {
  '/pRiVaT': '/Privat/',
  '/PRIVAT/': '/Privat/',
  '/pRiVaT/EtFs/': '/Privat/ETFs/',
  '/PRIVAT/etFS': '/Privat/ETFs/',
  '/privat/pReSsEsPiEgEl/': '/Privat/Pressespiegel/',
  '/PRIVAT/PRESSESPIEGEL': '/Privat/Pressespiegel/',
  '/PrIvAt/PrEsSeSpIeGeL/PrAeFeReNzEn.HtMl': '/Privat/Pressespiegel/praeferenzen.html',
  '/privAT/pressesPIEGEL/data/2099-12-31.JSON': '/Privat/Pressespiegel/data/2099-12-31.json',
  '/PRIVAT/eTfS/data/ETF_DATA.JSON': '/Privat/ETFs/data/etf_data.json',
  '/hOcHzEiT': '/Hochzeit/',
  '/HOCHZEIT/DaNkE.HtMl': '/Hochzeit/danke.html',
  '/HoChZeIt/Einladung.SVG': '/Hochzeit/einladung.svg'
};
for (const [source, target] of Object.entries(examples)) {
  assert.equal(resolve(source, '?ref=AbC', '#RSVP'), target + '?ref=AbC#RSVP', source);
}

// All combinations of ASCII-letter casing should resolve to the same target.
for (const [source, expected] of Object.entries(examples)) {
  for (let seed = 1; seed <= 64; seed++) {
    let i = seed * 43;
    const variant = source.replace(/[a-z]/gi, c => {
      i = (i * 1664525 + 1013904223) >>> 0;
      return i % 2 ? c.toUpperCase() : c.toLowerCase();
    });
    assert.equal(resolve(variant), expected, variant);
  }
}
assert.equal(resolve('/Privat/Pressespiegel/'), null, 'Canonical page should not redirect');
assert.equal(resolve('/Hochzeit/'), null, 'Canonical wedding page should not redirect');
assert.equal(resolve('/Privat/Pressespiegel/removed-old-reader'), null, 'Retired pages stay missing');
assert.equal(resolve('/unknown/ETF/'), null, 'Unrelated unknown URLs stay missing');
assert.equal(resolve('/Privat/Pressespiegel/not-a-file.json'), null, 'Typos must not redirect');
console.log('Case-insensitive route tests passed.');
