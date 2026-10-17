'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const files = ['README.md', 'Allgemeine-Website.md', 'ETF.md', 'Pressespiegel.md'];
const index = read('docs/website-context/README.md');
for (const name of files) {
  const file = path.join('docs/website-context', name);
  const body = read(file);
  assert.ok(body.startsWith('# '), file + ' needs a heading');
  assert.ok(body.includes('18.10.2026'), file + ' needs a reviewed baseline date');
  if (name !== 'README.md') {
    assert.ok(index.includes('](' + name + ')'), file + ' must be indexed');
    assert.match(body, /Offen|offen/, file + ' must track open items');
  }
}
assert.match(read('_config.yml'), /^\s+- docs\s*$/m, 'Working protocols must not be published by Jekyll');
assert.match(read('AGENTS.md'), /docs\/website-context\/README\.md/, 'Repository guide must direct agents to protocols');
console.log('PASS: all three website-area protocols indexed and excluded from production site');
