// Optional private-source CPU regression; no renderer, Unreal or owner state.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import vm from 'node:vm';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const vendor = path.join(root, 'SourceAssets/MotionBoard/vendor');
const fixtures = [
  ['animation-only FBX', 'SourceAssets/ZeroGChoreography_20261025/FBX/A_F3_ZeroG_01_Drift.fbx', true],
  ['mesh and animation FBX', 'SourceAssets/DanceRefinement_20261025/Vexa_Shoulder_Proof.fbx', false],
];
const available = existsSync(path.join(vendor, 'examples/jsm/loaders/FBXLoader.js')) && fixtures.every(([, file]) => existsSync(path.join(root, file)));
const hash = data => createHash('sha256').update(data).digest('hex');
const curveHash = clips => hash(JSON.stringify(clips.map(c => [c.name, c.duration, c.tracks.map(t => [t.name, Array.from(t.times), Array.from(t.values)])])));

test('browser-local FBX parses source motion and frames mesh or skeleton previews', { skip: available ? false : 'Private FBX fixtures/vendor are not available' }, async t => {
  const scratch = mkdtempSync(path.join(tmpdir(), 'motionboard-fbx-'));
  try {
    const threeUrl = pathToFileURL(path.join(vendor, 'build/three.module.js')).href;
    const imports = [['libs/fflate.module.js', 'fflate.mjs'], ['curves/NURBSUtils.js', 'NURBSUtils.mjs'], ['curves/NURBSCurve.js', 'NURBSCurve.mjs'], ['loaders/FBXLoader.js', 'FBXLoader.mjs'], ['utils/SkeletonUtils.js', 'SkeletonUtils.mjs']];
    for (const [source, target] of imports) {
      let code = readFileSync(path.join(vendor, 'examples/jsm', source), 'utf8').replaceAll("from 'three'", `from '${threeUrl}'`);
      for (const [from, to] of imports) code = code.replaceAll(`from '../${from}'`, `from './${to}'`);
      writeFileSync(path.join(scratch, target), code);
    }
    const THREE = await import(threeUrl);
    const { FBXLoader } = await import(pathToFileURL(path.join(scratch, 'FBXLoader.mjs')).href);
    const { clone } = await import(pathToFileURL(path.join(scratch, 'SkeletonUtils.mjs')).href);
    const app = readFileSync(new URL('./app.js', import.meta.url), 'utf8');
    const context = { THREE, FBXLoader, clone, URL, performance, neutral: new THREE.MeshStandardMaterial(), controlsCamera: new THREE.PerspectiveCamera(38, 1, 0.01, 1000),
      controls: { target: new THREE.Vector3(), update() {} }, $: () => ({ getBoundingClientRect: () => ({ width: 400, height: 400 }) }), renderCards() {}, libraryStatus() {} };
    vm.createContext(context);
    vm.runInContext('const libraries = new Map(), loadQueue = [], visibleLibraryIds = new Set(); let activeLoads = 0, nextLibraryId = null, cards = [], active = null;', context);
    vm.runInContext(app.slice(app.indexOf('const fbxManager ='), app.indexOf('const loadQueue =')), context);
    vm.runInContext(app.slice(app.indexOf('function catalogClips('), app.indexOf('async function importFiles(')), context);
    vm.runInContext(app.slice(app.indexOf('function disposeView('), app.indexOf('function draw(')), context);
    context.refreshPackages = () => {};

    for (const [label, relative, skeletonOnly] of fixtures) await t.test(label, async () => {
      const file = path.join(root, relative), bytes = readFileSync(file), before = hash(bytes);
      const data = await context.parseLocalFile(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), path.basename(file));
      assert.ok(data.animations.length > 0);
      const curves = curveHash(data.animations);
      const library = context.addLibrary(data, { id: skeletonOnly ? 'bones' : 'mesh', name: label, fileName: path.basename(file), sourceHash: before });
      assert.equal(library.skeletonOnly, skeletonOnly);
      assert.equal(library.fbxPreview, true);
      const clip = data.animations[0], view = context.makeView(library, clip);
      assert.ok(Number.isFinite(view.wrapper.scale.x) && view.wrapper.scale.x > 0);
      assert.ok(view.radius >= 0.5 && view.radius < 5, `normalized radius ${view.radius}`);
      assert.equal(!!view.helper, skeletonOnly);
      const positions = [];
      for (const fraction of [0, 0.25, 0.5, 0.75]) {
        view.action.time = clip.duration * fraction; view.mixer.update(0); view.scene.updateMatrixWorld(true);
        const pose = []; view.actor.traverse(o => { if (o.isBone) pose.push(o.matrixWorld.toArray()); }); positions.push(hash(JSON.stringify(pose)));
        if (view.helper) { view.helper.updateMatrixWorld(true); assert.ok(view.helper.geometry.attributes.position.count > 0); }
      }
      assert.ok(new Set(positions).size > 1, 'preview must actually move');
      assert.equal(curveHash(data.animations), curves);
      assert.equal(hash(readFileSync(file)), before);
      context.disposeView(view);
    });
    await t.test('static and unrenderable exports receive actionable errors', () => {
      assert.throws(() => context.addLibrary({ animations: [], scene: new THREE.Group() }, { id: 'static', name: 'Static model' }), /no animation clips/);
      assert.throws(() => context.addLibrary({ animations: [new THREE.AnimationClip('Take', 1, [])], scene: new THREE.Group() }, { id: 'empty', name: 'Empty hierarchy' }), /no previewable mesh or skeleton/);
      assert.equal(vm.runInContext("libraries.has('empty') || libraries.has('static')", context), false);
    });
  } finally {
    const resolved = path.resolve(scratch);
    assert.equal(path.dirname(resolved), path.resolve(tmpdir()));
    assert.ok(path.basename(resolved).startsWith('motionboard-fbx-'));
    rmSync(resolved, { recursive: true });
  }
});
