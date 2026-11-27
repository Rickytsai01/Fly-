'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const exists = p => fs.existsSync(path.join(root, p));
const html = read('index.html');
assert.ok(exists('index.html'), 'root index.html is missing');
assert.ok(exists('.nojekyll'), '.nojekyll is missing');
assert.ok(exists('flight-physics.js'), 'flight physics module is missing');
assert.ok(exists('gamepad-controls.js'), 'gamepad controls module is missing');
assert.match(html, /<meta[^>]+name=["']viewport["']/i, 'mobile viewport metadata is missing');
assert.match(html, /<script\s+src=["']\.\/flight-physics\.js["']/i, 'flight physics script must use a relative path');
assert.match(html, /<script\s+src=["']\.\/gamepad-controls\.js["']/i, 'gamepad module must use a relative path');
assert.ok(html.includes('id="btnCameraView"'), 'camera view control is missing');
assert.ok(html.includes('id="btnOpenGamepadSettings"'), 'controller settings button is missing');
assert.ok(html.includes('data-gp-axis="roll"') && html.includes('data-gp-axis="throttle"'), 'configurable axis selectors are missing');
assert.ok(html.includes("fetch('./data/taiwan-map.json'"), 'map JSON request must be relative to the project path');
assert.ok(html.includes("fetch('./data/terrain20m/index.json'"), 'terrain index request must be relative to the project path');
assert.ok(html.includes('`./data/terrain20m/${record.file}`'), 'terrain tile request must be relative to the project path');
assert.ok(!/\b(?:src|href)\s*=\s*["']\/(?!\/)/i.test(html), 'root-absolute asset path breaks GitHub Pages /Fly-/ deployment');

// Validate local HTML asset references without trying to fetch external CDNs.
const refs = [...html.matchAll(/\b(?:src|href)\s*=\s*["']([^"']+)["']/gi)].map(m => m[1]);
const localRefs = refs.filter(ref => !/^(?:[a-z]+:|\/\/|#|javascript:)/i.test(ref));
for (const ref of localRefs) {
  const pathname = decodeURIComponent(ref.split(/[?#]/, 1)[0]);
  if (!pathname) continue;
  assert.ok(exists(pathname), `missing local HTML resource: ${ref}`);
}

// Check every inline JavaScript block for syntax errors.
let inlineScripts = 0;
for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
  const attrs = match[1];
  const body = match[2].trim();
  if (!body || /\bsrc\s*=/.test(attrs) || /application\/json/i.test(attrs)) continue;
  new vm.Script(body, { filename: `index-inline-${++inlineScripts}.js` });
}
assert.ok(inlineScripts > 0, 'no inline application scripts were checked');

const map = JSON.parse(read('data/taiwan-map.json'));
assert.equal(map.schema, 'tw-flightsim-map-v1', 'unsupported map JSON schema');
assert.ok(Number.isInteger(map.width) && Number.isInteger(map.height), 'map dimensions are invalid');
assert.equal(map.elevation.length, map.width * map.height, 'map elevation count does not match its dimensions');
for (const code of ['TPE', 'RMQ', 'HUN', 'MZG', 'TTT', 'KHH']) {
  const airport = map.airports?.find(a => a.code === code);
  assert.ok(airport && Number.isFinite(airport.x) && Number.isFinite(airport.z), `missing mapped airport coordinate ${code}`);
}

const terrainDir = path.join(root, 'data', 'terrain20m');
const terrain = JSON.parse(read('data/terrain20m/index.json'));
assert.equal(terrain.schema, 'tw-flightsim-terrain-tiles-v1', 'unsupported terrain index schema');
assert.equal(terrain.sampleSpacingM, 20, 'expected 20 m source spacing');
assert.equal(terrain.tileSize, 256, 'unexpected terrain tile size');
assert.equal(terrain.tiles.length, terrain.tileCount, 'terrain tile count mismatch');
for (const tile of terrain.tiles) {
  assert.match(tile.file, /^\d{3}_\d{3}\.bin$/, `invalid terrain tile name ${tile.file}`);
  const fullPath = path.resolve(terrainDir, tile.file);
  assert.equal(path.dirname(fullPath), terrainDir, `tile escapes terrain directory: ${tile.file}`);
  assert.ok(fs.existsSync(fullPath), `missing terrain tile ${tile.file}`);
  assert.equal(fs.statSync(fullPath).size, terrain.tileSize * terrain.tileSize * 2, `invalid binary size for ${tile.file}`);
}
assert.ok(exists('data/airport-runway-sources.md'), 'runway data provenance document is missing');
assert.match(html, /rwyLen:\s*3660\s*\*\s*M_TO_WORLD/);
assert.match(html, /rwyWidth:\s*60\s*\*\s*M_TO_WORLD/);
for (const [code, heading, length, width] of [['RMQ','176.69','3659','61'],['HUN','26.32','2751','45'],['MZG','18.22','3000','45'],['TTT','38.64','2438','45'],['KHH','91.90','3150','60']]) {
  assert.match(html, new RegExp(`code: '${code}'.*rwyHeading: ${heading}, rwyLen: ${length} \\* M_TO_WORLD, rwyWidth: ${width} \\* M_TO_WORLD`), `runway values for ${code} changed unexpectedly`);
}
assert.ok(html.includes('id="btnTaxiStart"'), 'optional ground taxi practice button is missing');
assert.match(html, /function startTaxiwayPractice\(\)/, 'taxi practice action is not wired');
assert.ok(html.includes('沿黃色中心線前進'), 'taxi practice instructions are missing');
console.log(`PASS deployment assets: ${localRefs.length} local HTML references; map ${map.width}x${map.height}; ${terrain.tileCount} complete 20 m DEM tiles; ${inlineScripts} inline JS blocks parsed.`);