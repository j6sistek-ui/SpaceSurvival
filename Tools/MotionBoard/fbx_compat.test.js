// Synthetic CPU-only compatibility tests; no licensed FBX or renderer required.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const vendor = path.join(root, 'SourceAssets/MotionBoard/vendor');
const recipe = JSON.parse(readFileSync(new URL('./fbx_r180_patch.json', import.meta.url), 'utf8'));
const loaderFile = path.join(vendor, 'examples/jsm/loaders/FBXLoader.js');
const sha = data => createHash('sha256').update(data).digest('hex');
const freeze = value => { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; };

test('pinned FBX compatibility preserves scalar timing, canonical rest and Euler motion', {
  skip: existsSync(loaderFile) ? false : 'Prepare the pinned MIT vendor; no licensed fixture is required',
}, async t => {
  const scratch = mkdtempSync(path.join(tmpdir(), 'motionboard-fbx-compat-'));
  const original = readFileSync(loaderFile), originalHash = sha(original);
  try {
    let patched = original.toString('utf8');
    if (originalHash === recipe.upstreamSha256) for (const edit of recipe.patches) {
      assert.equal(patched.split(edit.old).length - 1, 1, edit.name);
      patched = patched.replace(edit.old, edit.new);
    }
    else assert.equal(originalHash, recipe.patchedSha256, 'Unknown vendor is never used for a compatibility test');
    assert.equal(sha(patched), recipe.patchedSha256);
    const threeUrl = pathToFileURL(path.join(vendor, 'build/three.module.js')).href;
    const imports = [['libs/fflate.module.js', 'fflate.mjs'], ['curves/NURBSUtils.js', 'NURBSUtils.mjs'], ['curves/NURBSCurve.js', 'NURBSCurve.mjs'], ['loaders/FBXLoader.js', 'FBXLoader.mjs']];
    for (const [from, to] of imports) {
      let code = (to === 'FBXLoader.mjs' ? patched : readFileSync(path.join(vendor, 'examples/jsm', from), 'utf8')).replaceAll("from 'three'", `from '${threeUrl}'`);
      for (const [source, target] of imports) code = code.replaceAll(`from '../${source}'`, `from './${target}'`);
      if (to === 'FBXLoader.mjs') code += '\nexport { AnimationParser };\nexport function setSyntheticTree(tree, graph, links) { fbxTree=tree; sceneGraph=graph; connections=links; }\n';
      writeFileSync(path.join(scratch, to), code);
    }
    const THREE = await import(threeUrl);
    const { AnimationParser, setSyntheticTree } = await import(pathToFileURL(path.join(scratch, 'FBXLoader.mjs')).href);
    const parser = new AnimationParser();
    const near = (actual, expected, epsilon = 1e-5) => assert.ok(Math.abs(actual-expected) <= epsilon, `${actual} != ${expected}`);
    const quaternionNear = (track, time, degrees, order, pre, post) => {
      const values = track.createInterpolant().evaluate(time);
      const actual = new THREE.Quaternion().fromArray(values);
      const expected = new THREE.Quaternion().setFromEuler(new THREE.Euler(...degrees.map(THREE.MathUtils.degToRad), order));
      if (pre) expected.premultiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(...pre.map(THREE.MathUtils.degToRad), 'ZYX')));
      if (post) expected.multiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(...post.map(THREE.MathUtils.degToRad), 'ZYX')).invert());
      near(Math.abs(actual.dot(expected)), 1, 1e-6);
    };

    await t.test('delayed one-key translation is constant; absent axes use rest without mutation', () => {
      const curves = freeze({ x: { times: [2], values: [7] }, z: { times: [0, 1, 2], values: [0, 10, 20] } });
      const rest = freeze([99, 20, 30]);
      const before = JSON.stringify({ curves, rest });
      const times = parser.getTimesForAllAxes(curves);
      assert.deepEqual(times, [0, 1, 2]);
      assert.deepEqual(parser.getKeyframeTrackValues(times, curves, rest), [7, 20, 0, 7, 20, 10, 7, 20, 20]);
      assert.equal(parser.sampleAnimationCurve(curves.x, -1, 99), 7);
      assert.equal(parser.sampleAnimationCurve(curves.x, 3, 99), 7);
      assert.equal(parser.sampleAnimationCurve(undefined, 0, 20), 20);
      assert.equal(parser.sampleAnimationCurve({ times: [], values: [] }, 0, 20), 20);
      assert.equal(JSON.stringify({ curves, rest }), before);
    });

    await t.test('canonical rest model wins over duplicate skin-cluster ID in either traversal order', () => {
      const canonical = new THREE.Object3D(); canonical.ID = 42;
      canonical.userData.transformData = { eulerOrder: 'ZYX' };
      canonical.matrix.makeTranslation(1, 20, 30);
      const cluster = new THREE.Object3D(); cluster.ID = 42; cluster.matrix.makeTranslation(999, 999, 999);
      const tree = { Objects: { AnimationLayer: { 100: {} }, Model: { 42: { id: 42, attrName: 'Joint' } } } };
      const links = new Map([[100, { children: [{ ID: 1 }] }], [1, { parents: [{ ID: 42, relationship: 'Lcl Translation' }] }]]);
      const curves = new Map([[1, { attr: 'T', curves: { x: { times: [2], values: [7] }, z: { times: [0, 2], values: [3, 4] } } }]]);
      for (const children of [[canonical, cluster], [cluster, canonical]]) {
        const graph = new THREE.Group(); children.forEach(child => graph.add(child));
        setSyntheticTree(tree, graph, links);
        const layer = parser.parseAnimationLayers(curves).get(100);
        assert.equal(layer[0].transform, canonical.matrix);
        const track = parser.generateTracks(layer[0])[0];
        assert.deepEqual(Array.from(track.values), [7, 20, 3, 7, 20, 4]);
      }
      const other = canonical.clone(); other.ID = 42;
      const ambiguous = new THREE.Group(); ambiguous.add(canonical, other);
      setSyntheticTree(tree, ambiguous, links);
      assert.throws(() => parser.parseAnimationLayers(curves), /Ambiguous canonical FBX model/);
    });

    await t.test('asynchronous rotation axes retain every source knot and actual-time scalar values', () => {
      const curves = freeze({ x: { times: [0, 2], values: [0, 90] }, y: { times: [0, 1, 2], values: [0, 30, 0] }, z: { times: [0.5, 1.5], values: [10, 30] } });
      const before = JSON.stringify(curves);
      const times = parser.getTimesForAllAxes(curves);
      assert.deepEqual(times, [0, 0.5, 1, 1.5, 2]);
      const expected = [[0, 0, 10], [22.5, 15, 10], [45, 30, 20], [67.5, 15, 30], [90, 0, 30]];
      const track = parser.generateRotationTrack('Joint', curves, undefined, undefined, 'XYZ');
      for (let i = 0; i < times.length; i++) quaternionNear(track, times[i], expected[i], 'XYZ');
      assert.equal(JSON.stringify(curves), before);
      assert.deepEqual(Array.from(parser.generateRotationTrack('Joint', curves, undefined, undefined, 'XYZ').values), Array.from(track.values));
    });

    await t.test('pre/post rotations apply once with the model Euler order', () => {
      const curves = { x: { times: [0, 1], values: [10, 20] }, y: { times: [0, 1], values: [30, 40] }, z: { times: [0, 1], values: [50, 60] } };
      const pre = [15, -5, 20], post = [-7, 10, 3];
      const track = parser.generateRotationTrack('Joint', curves, pre, post, 'YZX');
      quaternionNear(track, 0, [10, 30, 50], 'YZX', pre, post);
      quaternionNear(track, 1, [20, 40, 60], 'YZX', pre, post);
    });

    await t.test('a full raw Euler turn survives asynchronous union keys', () => {
      const curves = freeze({ x: { times: [0, 1], values: [0, 360] }, y: { times: [0, 0.25, 0.5, 0.75, 1], values: [0, 0, 0, 0, 0] }, z: { times: [0, 1], values: [0, 0] } });
      const track = parser.generateRotationTrack('Joint', curves, undefined, undefined, 'XYZ');
      for (let i = 0; i <= 8; i++) quaternionNear(track, i/8, [i*45, 0, 0], 'XYZ');
    });

    await t.test('a single 0–360 degree span retains its quarter-turn orientation', {
      todo: 'Known r180 large-angle limitation outside this three-edit patch; full-turn support is not universal',
    }, () => {
      const curves = { x: { times: [0, 1], values: [0, 360] }, y: { times: [0, 1], values: [0, 0] }, z: { times: [0, 1], values: [0, 0] } };
      const track = parser.generateRotationTrack('Joint', curves, undefined, undefined, 'XYZ');
      quaternionNear(track, 0.25, [90, 0, 0], 'XYZ');
    });

    await t.test('uniform scalar keys retain their authored values', () => {
      const curves = freeze(Object.fromEntries(['x', 'y', 'z'].map((axis, index) => [axis, { times: [0, 1, 2], values: [index, index+2, index+4] }])));
      assert.deepEqual(parser.getKeyframeTrackValues([0, 1, 2], curves, [100, 100, 100]), [0, 1, 2, 2, 3, 4, 4, 5, 6]);
    });
    assert.equal(sha(readFileSync(loaderFile)), originalHash, 'Live vendor bytes were never changed');
  } finally {
    assert.equal(path.dirname(path.resolve(scratch)), path.resolve(tmpdir()));
    assert.ok(path.basename(scratch).startsWith('motionboard-fbx-compat-'));
    rmSync(scratch, { recursive: true });
  }
});
