// Optional CPU-only rendering-math regression against the private local libraries.
// Run: node --test Tools/MotionBoard/framing.test.js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import vm from 'node:vm';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const assets = path.resolve(process.env.MOTION_BOARD_ASSETS || path.join(root, 'SourceAssets/MotionBoard'));
const vendor = path.join(assets, 'vendor');
const hash = data => createHash('sha256').update(data).digest('hex');
const fixtures = [
  ['Meshy', 'Meshy_Reference.glb', 19],
  ['Flips', 'libraries/flips.glb', 40],
];
const available = existsSync(path.join(vendor, 'build/three.module.js')) && fixtures.every(([, file]) => existsSync(path.join(assets, file)));

// Images need a browser. Ignore materials in a memory-only GLB copy so the CPU
// test still exercises the real mesh, skin, transforms and every source curve.
function geometryOnly(buffer) {
  assert.equal(buffer.readUInt32LE(0), 0x46546c67);
  const length = buffer.readUInt32LE(12);
  const json = JSON.parse(buffer.subarray(20, 20 + length).toString());
  for (const mesh of json.meshes || []) for (const primitive of mesh.primitives) delete primitive.material;
  const text = Buffer.from(JSON.stringify(json));
  const padded = Buffer.alloc(Math.ceil(text.length / 4) * 4, 0x20); text.copy(padded);
  const tail = buffer.subarray(20 + length);
  const result = Buffer.alloc(20 + padded.length + tail.length);
  buffer.copy(result, 0, 0, 20); result.writeUInt32LE(result.length, 8); result.writeUInt32LE(padded.length, 12);
  padded.copy(result, 20); tail.copy(result, 20 + padded.length);
  return result.buffer.slice(result.byteOffset, result.byteOffset + result.byteLength);
}

function curveHash(clips) {
  const digest = createHash('sha256');
  for (const clip of clips) {
    digest.update(JSON.stringify([clip.name, clip.duration]));
    for (const track of clip.tracks) {
      digest.update(track.name);
      for (const data of [track.times, track.values]) digest.update(Buffer.from(data.buffer, data.byteOffset, data.byteLength));
    }
  }
  return digest.digest('hex');
}

test('private Meshy and Flips previews normalize skins, follow roots and preserve source curves', { skip: available ? false : 'Private local libraries/vendor are not available' }, async t => {
  // Local vendor files use browser import maps. Rewrite only their import URLs
  // into an isolated temporary test directory; no downloads or host installs.
  const scratch = mkdtempSync(path.join(tmpdir(), 'motionboard-framing-'));
  try {
    const threeUrl = pathToFileURL(path.join(vendor, 'build/three.module.js')).href;
    for (const [input, output] of [['utils/BufferGeometryUtils.js', 'geometry.mjs'], ['utils/SkeletonUtils.js', 'skeleton.mjs'], ['loaders/GLTFLoader.js', 'loader.mjs']]) {
      const source = readFileSync(path.join(vendor, 'examples/jsm', input), 'utf8')
        .replaceAll("from 'three'", `from '${threeUrl}'`)
        .replaceAll("from '../utils/BufferGeometryUtils.js'", "from './geometry.mjs'");
      writeFileSync(path.join(scratch, output), source);
    }
    const THREE = await import(threeUrl);
    const { GLTFLoader } = await import(pathToFileURL(path.join(scratch, 'loader.mjs')).href);
    const { clone } = await import(pathToFileURL(path.join(scratch, 'skeleton.mjs')).href);
    const app = readFileSync(path.join(root, 'Tools/MotionBoard/app.js'), 'utf8');
    const context = { THREE, clone, neutral: new THREE.MeshStandardMaterial(), controlsCamera: new THREE.PerspectiveCamera(38, 1, 0.01, 1000),
      controls: { target: new THREE.Vector3(), update() {} }, $: () => ({ getBoundingClientRect: () => ({ width: 400, height: 400 }) }) };
    vm.createContext(context);
    vm.runInContext(app.slice(app.indexOf('function makeView('), app.indexOf('function draw(')), context);
    vm.runInContext(app.slice(app.indexOf('function followMotion('), app.indexOf('function setMain(')), context);

    for (const [name, relative, count] of fixtures) await t.test(name, async () => {
      const file = path.join(assets, relative), bytes = readFileSync(file), originalHash = hash(bytes);
      const gltf = await new GLTFLoader().parseAsync(geometryOnly(bytes), '');
      assert.equal(gltf.animations.length, count);
      const curves = curveHash(gltf.animations);
      let restScale;
      for (const clip of gltf.animations) {
        const view = context.makeView({ gltf }, clip, false);
        restScale ??= view.wrapper.scale.x;
        assert.equal(view.wrapper.scale.x, restScale, `${name}/${clip.name}: per-clip size changed`);
        assert.ok(view.radius >= 0.5 && view.radius < 5, `${name}/${clip.name}: normalized radius ${view.radius}`);
        assert.ok(view.camera.position.distanceTo(view.center) < 30, `${name}/${clip.name}: camera still uses unnormalized units`);
        assert.ok(view.anchor, `${name}/${clip.name}: missing root-follow anchor`);
        const cameraOffset = view.camera.position.clone().sub(view.anchor.getWorldPosition(new THREE.Vector3()));
        // Denser than the fitting samples, plus a jump back to zero at the end.
        for (const fraction of [...Array.from({ length: 25 }, (_, i) => i / 25), 0]) {
          view.action.time = clip.duration * fraction; view.mixer.update(0); context.followMotion(view);
          const offset = view.camera.position.clone().sub(view.anchor.getWorldPosition(new THREE.Vector3()));
          assert.ok(offset.distanceTo(cameraOffset) < 1e-7, `${name}/${clip.name}: root motion escaped camera`);
        }
        view.mixer.stopAllAction(); view.mixer.uncacheRoot(view.actor);
        view.actor.traverse(o => { if (o.isSkinnedMesh) o.skeleton.dispose(); });
      }
      assert.equal(curveHash(gltf.animations), curves, `${name}: source animation curves changed`);
      assert.equal(hash(readFileSync(file)), originalHash, `${name}: source file changed`);
    });
  } finally {
    const resolved = path.resolve(scratch), parent = path.resolve(tmpdir());
    assert.equal(path.dirname(resolved), parent);
    assert.ok(path.basename(resolved).startsWith('motionboard-framing-'));
    rmSync(resolved, { recursive: true });
  }
});
