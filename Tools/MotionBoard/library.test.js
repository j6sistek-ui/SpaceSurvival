import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const app = readFileSync(new URL('./app.js', import.meta.url), 'utf8');
const functions = app.slice(app.indexOf('function catalogClips('), app.indexOf('async function importFiles('));
const flush = () => new Promise(resolve => setImmediate(resolve));
const meta = id => ({ id, name: id, url: `/libraries/${id}.glb`, clips: [{ name: `${id}-clip`, duration: 5 }] });
const gltf = id => ({ animations: [{ name: `${id}-clip`, duration: 5, tracks: ['private key data'] }], scene: { traverse(visit) { visit({ isMesh: true, material: { dispose() {} } }); } } });

function setup() {
  const elements = new Map(), requests = [], messages = [];
  const element = () => ({ value: 'all', disabled: false, children: [], append(child) { this.children.push(child); }, replaceChildren(...children) { this.children = children; this.firstChild = children[0]; } });
  const context = {
    performance: { now: () => Date.now() }, neutral: {},
    $: id => { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); },
    text: (tag, value) => ({ tag, textContent: value }), renderCards() {}, libraryStatus() {},
    toast: message => messages.push(message),
    loader: { loadAsync(url) { return new Promise((resolve, reject) => requests.push({ url, resolve, reject })); } },
  };
  vm.createContext(context);
  vm.runInContext('const libraries = new Map(), loadQueue = [], visibleLibraryIds = new Set(); let activeLoads = 0, nextLibraryId = null, cards = [], active = null;', context);
  vm.runInContext(functions, context);
  return { context, requests, messages, get: code => vm.runInContext(code, context) };
}

test('catalogs do not download GLBs and active downloads are bounded to two', async () => {
  const { context, requests, get } = setup();
  for (let i = 0; i < 100; i++) context.registerLibrary(meta(`p${i}`));
  assert.equal(requests.length, 0);
  assert.equal(get('libraries.size'), 100);
  const a = context.ensureLibrary(get("libraries.get('p0')"));
  const b = context.ensureLibrary(get("libraries.get('p1')"));
  const c = context.ensureLibrary(get("libraries.get('p2')"));
  context.ensureLibrary(get("libraries.get('p2')"), true);
  assert.equal(requests.length, 2);
  assert.equal(get('activeLoads'), 2);
  assert.equal(get('loadQueue.length'), 1);
  requests[0].resolve(gltf('p0')); await flush();
  assert.equal(requests.length, 3);
  assert.equal(requests[2].url, '/libraries/p2.glb');
  assert.equal(get('activeLoads'), 2);
  requests[1].resolve(gltf('p1')); requests[2].resolve(gltf('p2')); await Promise.all([a, b, c]); await flush();
  assert.equal(get('activeLoads'), 0);
  assert.equal(get("libraries.get('p0').clips[0].tracks"), undefined, 'catalog must not retain heavyweight animation tracks');
});

test('reload adds metadata and discovers legacy entries without touching edits or saved state', async () => {
  const { context, requests, get } = setup();
  context.registerLibrary(meta('old'));
  vm.runInContext("active = { library: 'old', clip: 'old-clip', start: 1, end: 4, duration: 8, reverse: true }; const board = { title: 'Keep my proposal', items: [active] }; let elapsed = 2.4, selectedId = 'owner-slot';", context);
  const before = get('JSON.stringify({active, board, elapsed, selectedId})');
  const urls = [];
  context.fetch = async url => { urls.push(url); return { ok: true, json: async () => ({ libraries: [meta('old'), meta('new'), { id: 'legacy', name: 'Legacy', url: '/legacy.glb' }] }) }; };
  const reload = context.reloadLibraries(); await flush();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, '/legacy.glb');
  requests[0].resolve(gltf('legacy')); await reload; await flush();
  assert.deepEqual(urls, ['/api/info']);
  assert.equal(get('libraries.size'), 3);
  assert.equal(get('JSON.stringify({active, board, elapsed, selectedId})'), before);
  assert.equal(get("libraries.get('new').gltf"), null);
  assert.equal(context.$('reloadLibraries').disabled, false);
});

test('a failed preview waits for explicit reload before retrying', async () => {
  const { context, requests, get } = setup();
  const library = context.registerLibrary(meta('retry'));
  const first = context.ensureLibrary(library); requests[0].reject(new Error('Download unavailable')); await first; await flush();
  await context.ensureLibrary(library);
  assert.equal(requests.length, 1);
  context.fetch = async () => ({ ok: true, json: async () => ({ libraries: [meta('retry')] }) });
  await context.reloadLibraries();
  const retry = context.ensureLibrary(library);
  assert.equal(requests.length, 2);
  requests[1].resolve(gltf('retry')); await retry; await flush();
  assert.equal(get("libraries.get('retry').status"), 'ready');
});

test('unused remote packs release geometry while visible, active and local sources survive', () => {
  const { context, get } = setup();
  const disposed = [];
  for (let i = 0; i < 5; i++) {
    const id = `p${i}`, loaded = gltf(id);
    loaded.scene.traverse = visit => visit({ isMesh: true, material: { dispose() {} }, geometry: { dispose: () => disposed.push(id) } });
    context.addLibrary(loaded, meta(id));
  }
  context.addLibrary(gltf('local'), { id: 'local', name: 'Local source' });
  vm.runInContext("visibleLibraryIds.add('p0'); active = {library:'p1'}; nextLibraryId = 'p2'; cards = [{library: libraries.get('p3'),view:{}}];", context);
  context.evictLibraries();
  assert.deepEqual(disposed, ['p4']);
  assert.equal(get("libraries.get('p4').gltf"), null);
  assert.equal(get("libraries.get('p4').clips.length"), 1);
  assert.ok(get("libraries.get('local').gltf"));
});
