import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { SLOT_COUNT, makeItem, placeItem, sourceTime, timeline, playbackTiming, editItem, playbackPlan, advancePlayback } from './model.js';

const $ = id => document.getElementById(id);
const libraries = new Map();
const loader = new GLTFLoader();
// Motion previews use a neutral material. Do not fetch texture paths embedded
// in a browser-local FBX (or require its external image sidecars).
const fbxManager = new THREE.LoadingManager();
fbxManager.addHandler(/.*/, { path: '', setPath(value) { this.path = value; return this; }, load(url) {
  if (String(url).startsWith('blob:')) URL.revokeObjectURL(url);
  return new THREE.Texture();
} });
const fbxLoader = new FBXLoader(fbxManager);
const loadQueue = [];
const visibleLibraryIds = new Set();
let activeLoads = 0;
let nextLibraryId = null;
const history = [];
let board = { version: 1, title: 'My motion proposal', items: [], libraries: [] };
let revision = 0, dirty = false, saving = false, conflict = false, saveTimer;
let draft = null, selectedId = null, active = null, elapsed = 0, playing = false, sequence = false;
let cardsPlaying = true, cards = [], mainView = null, activeKey = '', lastFrame = 0, lastCards = 0;
let cardTime = 0, cardSpeed = 1;
try {
  const savedSpeed = Number(localStorage.getItem('motionBoard.cardSpeed'));
  if ([0.25, 0.5, 1, 2].includes(savedSpeed)) cardSpeed = savedSpeed;
} catch { /* Preview preferences are optional when browser storage is unavailable. */ }
const pretty = name => name.replace(/_/g, ' ').replace(/^AS /, '');
const seconds = n => Number(n).toFixed(2);
const total = () => board.items.reduce((n, item) => n + item.duration, 0);
const clipFor = item => libraries.get(item?.library)?.clips.find(c => c.name === item.clip);
const loadedClipFor = item => libraries.get(item?.library)?.gltf?.animations.find(c => c.name === item.clip);
function toast(message) { $('toast').textContent = message; $('toast').style.display = 'block'; clearTimeout(toast.timer); toast.timer = setTimeout(() => $('toast').style.display = 'none', 5000); }
function text(tag, value, className) { const e = document.createElement(tag); e.textContent = value; if (className) e.className = className; return e; }
function checkpoint() { history.push(structuredClone(board)); if (history.length > 40) history.shift(); $('undo').disabled = false; }
function metadata() { return [...libraries.values()].map(({ id, name, fileName, sourceHash }) => ({ id, name, fileName: fileName || '', sourceHash: sourceHash || '' })); }
function changed() {
  board.libraries = [...new Map([...(board.libraries || []), ...metadata()].map(l => [l.id, l])).values()];
  dirty = true; $('saveStatus').textContent = 'Saving…';
  clearTimeout(saveTimer); saveTimer = setTimeout(save, 400); renderSlots();
}
async function save() {
  if (saving || !dirty || conflict) return;
  saving = true; dirty = false;
  try {
    const response = await fetch('/api/project', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision, project: board }) });
    const data = await response.json();
    if (response.status === 409) { conflict = true; throw new Error('Another tab saved this board. Export your proposal before reloading.'); }
    if (!response.ok) throw new Error(data.error || 'Save failed. Export a copy before closing.');
    revision = data.revision; $('saveStatus').textContent = 'Saved on this PC';
  } catch (error) { dirty = true; $('saveStatus').textContent = 'Not saved — export a copy'; toast(error.message); }
  finally { saving = false; if (dirty && !conflict) clearTimeout(saveTimer); }
  // Edits made during a successful request must not be lost.
  if (dirty && !conflict && $('saveStatus').textContent === 'Saved on this PC') saveTimer = setTimeout(save, 100);
}
window.addEventListener('beforeunload', event => { if (dirty || saving) { event.preventDefault(); event.returnValue = ''; } });

// One renderer for all cards: shared geometry, independent skeletons, visible cards only.
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.domElement.className = 'motion-canvas'; document.body.append(renderer.domElement);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.35));
renderer.setSize(innerWidth, innerHeight); renderer.setClearColor(0x000000, 0);
renderer.outputColorSpace = THREE.SRGBColorSpace;
const neutral = new THREE.MeshStandardMaterial({ color: 0xa2c8cd, roughness: 0.76, metalness: 0.03, side: THREE.DoubleSide });
const controlsCamera = new THREE.PerspectiveCamera(38, 1, 0.01, 1000);
const controls = new OrbitControls(controlsCamera, $('stage'));
controls.enableDamping = true; controls.enablePan = true; controls.minDistance = 0.3; controls.maxDistance = 30;

function disposeView(view) {
  if (!view) return;
  view.mixer.stopAllAction(); view.mixer.uncacheRoot(view.actor);
  view.actor.traverse(o => { if (o.isSkinnedMesh) o.skeleton.dispose(); });
  if (view.helper) { view.helper.geometry.dispose(); view.helper.material.dispose(); }
}
function makeView(library, clip, isMain = false) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(isMain ? 0x182430 : 0x1c2a39);
  scene.add(new THREE.HemisphereLight(0xdcefff, 0x4a5362, 2.4));
  const key = new THREE.DirectionalLight(0xffffff, 3); key.position.set(3, 5, 4); scene.add(key);
  const rim = new THREE.DirectionalLight(0x74e0d0, 1.3); rim.position.set(-4, 2, -3); scene.add(rim);
  const actor = clone(library.gltf.scene); actor.traverse(o => { if (o.isMesh) { o.material = neutral; o.frustumCulled = false; } });
  // A static display wrapper normalizes units; the original animated hierarchy is untouched.
  const wrapper = new THREE.Group(); wrapper.add(actor); scene.add(wrapper);
  // Refresh cloned skin bindings before measuring the rest pose. Without this,
  // an imported .01 armature scale can be applied twice to the initial bounds.
  scene.updateMatrixWorld(true);
  actor.traverse(o => { if (o.isSkinnedMesh) o.computeBoundingBox(); });
  const bones = []; actor.traverse(o => { if (o.isBone) bones.push(o); });
  const poseBounds = () => {
    if (!library.skeletonOnly) return new THREE.Box3().setFromObject(wrapper);
    const bounds = new THREE.Box3();
    for (const bone of bones) bounds.expandByPoint(bone.getWorldPosition(new THREE.Vector3()));
    return bounds;
  };
  const box = poseBounds(); const size = box.getSize(new THREE.Vector3());
  const scale = 1.85 / Math.max(size.y, size.x * 0.7, 0.01);
  wrapper.scale.setScalar(scale);
  const center = box.getCenter(new THREE.Vector3()); wrapper.position.set(-center.x * scale, -box.min.y * scale, -center.z * scale);
  const mixer = new THREE.AnimationMixer(actor); const action = mixer.clipAction(clip);
  action.play(); action.paused = true;
  const camera = isMain ? controlsCamera : new THREE.PerspectiveCamera(38, 1, 0.01, 1000);
  let helper = null;
  if (library.skeletonOnly) {
    helper = new THREE.SkeletonHelper(actor); helper.material.vertexColors = false;
    helper.material.color.set(0x74e0d0); helper.material.depthTest = false; scene.add(helper);
  }
  let anchor = null;
  actor.traverse(o => { if (o.isBone && /^(pelvis|hips|mixamorig:?hips)$/i.test(o.name)) anchor = o; });
  if (!anchor) actor.traverse(o => { if (!anchor && o.isSkinnedMesh) anchor = o.skeleton.bones.find(b => /hips|pelvis/i.test(b.name)) || o.skeleton.bones[0]; });
  if (!anchor && bones.length) anchor = bones.find(b => /hips|pelvis/i.test(b.name)) || bones[0];
  const view = { scene, actor, wrapper, mixer, action, camera, clip, anchor, helper, center: new THREE.Vector3(0, 0.95, 0), radius: 1.1, lastAnchor: new THREE.Vector3() };
  // Sample the whole clip for framing, including root travel/flips, without editing it.
  const bounds = new THREE.Box3();
  for (let i = 0; i <= 12; i++) {
    action.time = Math.min(clip.duration - 0.00001, clip.duration * i / 12); mixer.update(0); scene.updateMatrixWorld(true);
    actor.traverse(o => { if (o.isSkinnedMesh) o.computeBoundingBox(); });
    const sample = poseBounds();
    // Follow translation with the camera, retaining the body's flips/turns.
    // Including the whole root path would make a travelling character tiny.
    if (anchor) sample.translate(anchor.getWorldPosition(new THREE.Vector3()).negate());
    bounds.union(sample);
  }
  if (!bounds.isEmpty()) { view.center.copy(bounds.getCenter(new THREE.Vector3())); view.radius = Math.max(1.1, bounds.getSize(new THREE.Vector3()).length() / 2); }
  action.time = 0; mixer.update(0); scene.updateMatrixWorld(true);
  if (anchor) { anchor.getWorldPosition(view.lastAnchor); view.center.add(view.lastAnchor); }
  if (!isMain) frameCamera(view); return view;
}
function frameCamera(view) {
  const element = view.camera === controlsCamera ? $('stage') : null;
  if (element) { const rect = element.getBoundingClientRect(); view.camera.aspect = rect.width / Math.max(rect.height, 1); }
  const vertical = THREE.MathUtils.degToRad(view.camera.fov / 2);
  const horizontal = Math.atan(Math.tan(vertical) * view.camera.aspect);
  const d = view.radius / Math.sin(Math.min(vertical, horizontal)) * 1.06;
  view.camera.near = Math.max(0.001, view.radius / 1000);
  view.camera.far = Math.max(1000, d * 30);
  view.camera.updateProjectionMatrix();
  view.camera.position.copy(view.center).add(new THREE.Vector3(d * 0.28, d * 0.08, d));
  view.camera.lookAt(view.center);
  if (view.camera === controlsCamera) {
    // Imported unit scales vary. A fixed distance limit could force an otherwise
    // correctly framed camera inside the character on the next controls update.
    controls.minDistance = view.radius * 0.15; controls.maxDistance = d * 6;
    controls.target.copy(view.center); controls.update();
  }
}
function draw(view, element, clipRect) {
  const rect = element.getBoundingClientRect();
  const left = Math.max(0, rect.left, clipRect?.left ?? 0), right = Math.min(innerWidth, rect.right, clipRect?.right ?? innerWidth);
  const top = Math.max(0, rect.top, clipRect?.top ?? 0), bottom = Math.min(innerHeight, rect.bottom, clipRect?.bottom ?? innerHeight);
  if (right <= left || bottom <= top) return false;
  view.camera.aspect = rect.width / rect.height; view.camera.updateProjectionMatrix();
  renderer.setViewport(rect.left, innerHeight - rect.bottom, rect.width, rect.height);
  renderer.setScissor(left, innerHeight - bottom, right - left, bottom - top);
  renderer.render(view.scene, view.camera); return true;
}
function followMotion(view) {
  if (!view?.anchor) return;
  view.scene.updateMatrixWorld(true);
  const point = view.anchor.getWorldPosition(new THREE.Vector3());
  const shift = point.clone().sub(view.lastAnchor);
  view.camera.position.add(shift); view.center.add(shift);
  if (view.camera === controlsCamera) controls.target.add(shift);
  else view.camera.lookAt(view.center);
  view.lastAnchor.copy(point);
}
function setMain(item, reset = false) {
  const library = libraries.get(item?.library), clip = loadedClipFor(item);
  const key = clip ? `${library.id}/${clip.name}` : '';
  if (!clip) {
    disposeView(mainView); mainView = null; activeKey = '';
    if (item?.clip && (library?.url || library?.sourceFile) && !library.gltf) ensureLibrary(library, true);
    $('stageMessage').textContent = item?.clip ? library?.error ? `${library.name}: preview unavailable. Try Reload libraries.` : (library?.url || library?.sourceFile) && !library.gltf ? `Loading ${library.name} preview…` : 'Reselect this GLB or FBX file to restore its preview.' : (item?.note || 'Choose a move from the library.');
    $('stageMessage').style.display = 'grid'; return;
  }
  if (key !== activeKey) { disposeView(mainView); mainView = makeView(library, clip, true); activeKey = key; reset = true; }
  if (reset) frameCamera(mainView);
  $('stageHint').textContent = `${library.skeletonOnly ? 'Skeleton preview · no mesh · ' : library.fbxPreview ? 'FBX motion preview · skin deformation may differ · ' : ''}Drag to rotate · scroll to zoom`;
  $('stageMessage').style.display = 'none';
}
function renderCards() {
  cards.forEach(c => disposeView(c.view)); cards = []; $('cards').replaceChildren();
  const query = $('search').value.toLowerCase(), pack = $('package').value;
  let count = 0;
  for (const library of libraries.values()) {
    if (pack !== 'all' && pack !== library.id) continue;
    for (const clip of library.clips) {
      if (!pretty(clip.name).toLowerCase().includes(query)) continue;
      if (!$('showBasics').checked && /^(walking|running|idle|walk|run|t[-_ ]?pose|a[-_ ]?pose)([_ .]|$)/i.test(clip.name)) continue;
      count++;
      const element = document.createElement('article'); element.className = 'card'; element.draggable = true; element.tabIndex = 0;
      element.setAttribute('aria-label', `${pretty(clip.name)}, ${seconds(clip.duration)} seconds, ${library.name}`);
      element.dataset.library = library.id; element.dataset.clip = clip.name;
      const viewport = text('div', '', 'card-viewport'), info = text('div', '', 'card-info');
      viewport.style.cssText = 'display:grid;place-items:center;text-align:center;font-size:11px;color:#9caec4;padding:12px';
      info.append(text('strong', pretty(clip.name)), text('span', `${seconds(clip.duration)}s · ${library.name}${library.skeletonOnly ? ' · skeleton' : ''}`));
      element.append(viewport, text('span', String(count).padStart(2, '0'), 'card-number'), info);
      element.onclick = () => selectClip(library, clip);
      element.onkeydown = event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); selectClip(library, clip); } };
      element.ondragstart = event => { event.dataTransfer.setData('application/x-motion', JSON.stringify({ library: library.id, clip: clip.name })); event.dataTransfer.effectAllowed = 'copy'; };
      $('cards').append(element); cards.push({ element, viewport, library, clip, view: null });
    }
  }
  $('count').textContent = `${count} clips`;
  if (!count) $('cards').append(text('p', 'No matching moves. Try another package or search.'));
  markSelected();
}
function markSelected() { cards.forEach(c => c.element.classList.toggle('selected', c.library.id === active?.library && c.clip.name === active?.clip)); }
function selectClip(library, clip) {
  draft = makeItem(library.id, clip, 0); selectedId = null; active = draft; elapsed = 0; sequence = false; playing = true;
  setMain(active); renderEditor(); renderSlots(); markSelected();
}
function selectSlot(item) {
  selectedId = item.id; active = item; sequence = false; elapsed = 0; playing = !!item.clip;
  setMain(item); renderEditor(); renderSlots(); markSelected();
}
function renderEditor() {
  const clip = clipFor(active); const max = clip?.duration || Math.max(active?.end || 0, 1);
  $('previewTitle').textContent = active?.clip ? pretty(active.clip) : active ? 'Transition direction' : 'Choose a move';
  $('previewMode').textContent = sequence ? 'SEQUENCE PREVIEW' : selectedId ? `SLOT ${active.slot + 1}` : 'CLIP PREVIEW';
  $('editTitle').textContent = selectedId ? `Slot ${active.slot + 1} · trim & timing` : 'Trim before adding';
  $('start').value = seconds(active?.start || 0); $('end').value = seconds(active?.end || 0); $('duration').value = seconds(active?.duration || 1);
  $('reverse').checked = active?.reverse || false; $('note').value = active?.note || '';
  for (const id of ['trimIn', 'trimOut']) { $(id).max = max; $(id).disabled = !clip; }
  $('trimIn').value = active?.start || 0; $('trimOut').value = active?.end || 0;
  $('trimFill').style.left = `${100 * (active?.start || 0) / max}%`; $('trimFill').style.right = `${100 * (1 - (active?.end || 0) / max)}%`;
  for (const id of ['start', 'end', 'reverse']) $(id).disabled = !clip;
  $('duration').disabled = !active; $('note').disabled = !active;
  const timing = active?.clip ? playbackTiming(active) : null;
  const repeating = timing && timing.mode !== 'stretch';
  $('playbackMode').value = timing?.mode || 'stretch'; $('playbackMode').disabled = !clip;
  $('playbackSpeed').value = active?.playbackSpeed ?? 1; $('playbackSpeed').disabled = !clip || !repeating;
  $('repeatCount').value = active?.repeatCount ?? 1; $('repeatCount').disabled = !clip || timing?.mode !== 'repeat-count';
  $('repeatSpeedField').hidden = !repeating; $('repeatCountField').hidden = timing?.mode !== 'repeat-count';
  $('duration').disabled = !active || timing?.mode === 'repeat-count';
  $('durationCaption').textContent = timing?.mode === 'repeat-count' ? 'Total (calculated)' : repeating ? 'Repeat for' : 'Play for';
  $('speedLabel').textContent = timing ? `${timing.speed.toFixed(2)}×${active.reverse ? ' reverse' : ''}` : 'Direction';
  $('timingSummary').textContent = timing ? `${seconds(timing.span)}s trimmed source · ${seconds(timing.duration)}s total${repeating ? ` · ${Number(timing.cycles.toFixed(3))} cycles, ${seconds(timing.cycleDuration)}s each. Loop seams are not blended.` : ' · one pass, stretched to fit.'}${clip && active.end > clip.duration + 0.001 ? ' Saved end exceeds this export; preview holds its last frame. Trim is preserved.' : ''}` : 'Transition notes reserve timeline time; they do not animate a character.';
  $('editingHint').textContent = !active ? 'Choose a clip or a slot to trim it.' : selectedId ? 'Changes save to this slot.' : 'Trim here, then drag the card or add it below.';
  $('addSelected').disabled = !clip || board.items.length === SLOT_COUNT;
  $('play').disabled = !active; $('playSequence').disabled = board.items.length === 0;
}
function edit(field, value) {
  if (!active) return;
  let next = { ...active, [field]: value }; const clip = clipFor(next);
  try { if (clip) next = editItem(active, field, value, clip.duration); else if (!Number.isFinite(next.duration) || next.duration < 0.05 || next.duration > 3600) throw new Error('Choose a duration between 0.05 and 3600 seconds.'); }
  catch (error) { toast(error.message); renderEditor(); return; }
  if (selectedId) { checkpoint(); board.items = board.items.map(x => x.id === selectedId ? next : x); changed(); } else draft = next;
  active = next; elapsed = Math.min(elapsed, sequence ? total() : next.duration); renderEditor();
}
function addToSlot(library, clip, slot) {
  if (!library || !clip) return toast('Reselect the source GLB or FBX file to use this move.');
  checkpoint(); const item = active?.library === library.id && active?.clip === clip.name ? { ...active, id: crypto.randomUUID(), slot } : makeItem(library.id, clip, slot);
  const replaced = board.items.some(x => x.slot === slot); board.items = placeItem(board.items, item, slot); changed(); selectSlot(item);
  if (replaced) toast('Slot replaced. Undo restores the previous move.');
}
function nextSlot() { return Array.from({ length: SLOT_COUNT }, (_, i) => i).find(i => !board.items.some(x => x.slot === i)); }
function renderSlots() {
  $('slots').replaceChildren(); $('total').textContent = `${total().toFixed(1)} seconds`; $('playSequence').disabled = !board.items.length;
  for (let slot = 0; slot < SLOT_COUNT; slot++) {
    const item = board.items.find(x => x.slot === slot), el = document.createElement('div');
    el.className = `slot ${item ? 'filled' : 'empty'}${selectedId === item?.id ? ' active' : ''}`; el.dataset.slot = slot; el.tabIndex = 0;
    el.append(text('span', String(slot + 1).padStart(2, '0'), 'number'));
    if (item) {
      el.draggable = true; el.append(text('strong', item.clip ? pretty(item.clip) : 'Transition direction'));
      el.append(text('small', `${seconds(item.duration)}s${item.reverse ? ' · reversed' : ''}`));
      el.append(text('small', item.clip ? `${seconds(item.start)} → ${seconds(item.end)}s` : (item.note || 'Add a direction')));
      if (item.clip && item.playbackMode && item.playbackMode !== 'stretch') el.append(text('small', `${Number(playbackTiming(item).cycles.toFixed(3))} cycles · ${item.playbackSpeed ?? 1}×`));
      const remove = text('button', '×', 'remove'); remove.setAttribute('aria-label', `Remove slot ${slot + 1}`);
      remove.onclick = event => { event.stopPropagation(); checkpoint(); board.items = board.items.filter(x => x.id !== item.id); if (selectedId === item.id) { active = null; selectedId = null; playing = false; setMain(null); renderEditor(); } changed(); };
      el.append(remove); el.onclick = () => selectSlot(item);
      el.ondragstart = event => { event.dataTransfer.setData('application/x-motion', JSON.stringify({ itemId: item.id })); event.dataTransfer.effectAllowed = 'move'; };
    } else { el.append(text('span', 'Drop a move here')); el.onclick = () => { if (active?.clip) addToSlot(libraries.get(active.library), clipFor(active), slot); }; }
    el.onkeydown = event => { if (event.key === 'Enter') el.click(); };
    el.ondragover = event => { event.preventDefault(); el.classList.add('over'); };
    el.ondragleave = () => el.classList.remove('over');
    el.ondrop = event => {
      event.preventDefault(); el.classList.remove('over');
      try {
        const data = JSON.parse(event.dataTransfer.getData('application/x-motion'));
        if (data.itemId) { const existing = board.items.find(x => x.id === data.itemId); if (!existing) return; checkpoint(); board.items = placeItem(board.items, existing, slot); changed(); selectSlot(board.items.find(x => x.id === existing.id)); }
        else { const library = libraries.get(data.library), clip = library?.clips.find(c => c.name === data.clip); if (clip) addToSlot(library, clip, slot); }
      } catch { toast('Drag a move from this library.'); }
    };
    $('slots').append(el);
  }
}

function catalogClips(clips) {
  return (clips || []).filter(c => typeof c.name === 'string' && Number.isFinite(c.duration) && c.duration >= 0.01).map(c => ({ name: c.name, duration: c.duration }));
}
function refreshPackages() {
  const selected = $('package').value;
  $('package').replaceChildren(text('option', 'All packages'));
  $('package').firstChild.value = 'all';
  for (const library of libraries.values()) { const opt = text('option', `${library.name} (${library.clips.length})`); opt.value = library.id; $('package').append(opt); }
  $('package').value = libraries.has(selected) ? selected : 'all';
}
function registerLibrary(meta) {
  const existing = libraries.get(meta.id);
  if (existing) {
    // Keep loaded source identity and the owner's active clip/trim on refresh.
    if (!existing.gltf && !existing.pending) {
      Object.assign(existing, { url: meta.url, name: meta.name, fileName: meta.fileName, sourceHash: meta.sourceHash, error: null });
      if (Array.isArray(meta.clips)) existing.clips = catalogClips(meta.clips);
    }
    return existing;
  }
  const library = { ...meta, clips: catalogClips(meta.clips), gltf: null, status: 'idle', error: null, pending: null, used: 0 };
  libraries.set(meta.id, library); return library;
}
function addLibrary(gltf, meta) {
  if (!gltf.animations.length) throw new Error(`${meta.name}: no animation clips. Export this file with baked animations and try again.`);
  const existing = libraries.get(meta.id);
  if (existing?.gltf) return existing;
  const names = new Set();
  const clips = gltf.animations.filter(c => c.duration >= 0.01).map((c, i) => { if (!c.name) c.name = `Clip ${i + 1}`; if (names.has(c.name)) c.name += ` [${i + 1}]`; names.add(c.name); return c; });
  if (!clips.length) throw new Error(`${meta.name}: no timed animation clips.`);
  let meshes = 0, bones = 0;
  gltf.scene.traverse(o => { if (o.isMesh) meshes++; if (o.isBone) bones++; });
  if (!meshes && bones < 2) throw new Error(`${meta.name}: animations have no previewable mesh or skeleton. Export with its armature or a compatible mesh.`);
  const library = existing || registerLibrary(meta);
  // Textures are not needed for motion proposals. Release them after parsing.
  const textures = new Set(), materials = new Set();
  gltf.scene.traverse(o => { if (o.isMesh) { for (const m of Array.isArray(o.material) ? o.material : [o.material]) { if (!m) continue; materials.add(m); for (const v of Object.values(m)) if (v?.isTexture) textures.add(v); } o.material = neutral; } });
  textures.forEach(t => { t.dispose(); if (typeof t.image?.close === 'function') t.image.close(); }); materials.forEach(m => m.dispose());
  const oldCatalog = JSON.stringify(library.clips);
  Object.assign(library, { gltf, clips: catalogClips(clips), skeletonOnly: !meshes, fbxPreview: /\.fbx$/i.test(meta.fileName || meta.sourceFile?.name || ''), status: 'ready', error: null, used: performance.now() });
  // Catalogued packs already have their cards. Do not rebuild every preview or
  // reset a field being edited just because a background download finished.
  if (JSON.stringify(library.clips) !== oldCatalog) { refreshPackages(); renderCards(); }
  return library;
}
function ensureLibrary(library, priority = false) {
  if (!library) return Promise.resolve(null);
  library.used = performance.now();
  if (library.gltf) return Promise.resolve(library);
  if (library.pending) {
    if (priority) { const at = loadQueue.findIndex(job => job.library === library); if (at > 0) loadQueue.unshift(loadQueue.splice(at, 1)[0]); }
    return library.pending;
  }
  if ((!library.url && !library.sourceFile) || library.error) return Promise.resolve(null);
  library.status = 'queued';
  library.pending = new Promise(resolve => {
    const job = { library, resolve }; if (priority) loadQueue.unshift(job); else loadQueue.push(job);
  });
  pumpLoads(); return library.pending;
}
function pumpLoads() {
  while (activeLoads < 2 && loadQueue.length) {
    const { library, resolve } = loadQueue.shift(); activeLoads++; library.status = 'loading'; libraryStatus();
    const loading = library.sourceFile ? library.sourceFile.arrayBuffer().then(buffer => parseLocalFile(buffer, library.sourceFile.name)) : loader.loadAsync(library.url);
    loading.then(gltf => { addLibrary(gltf, library); resolve(library); })
      .catch(error => { library.status = 'error'; library.error = error.message; resolve(null); toast(`${library.name}: ${error.message}`); })
      .finally(() => { activeLoads--; library.pending = null; evictLibraries(); libraryStatus(); pumpLoads(); });
  }
}
function evictLibraries() {
  // Local File handles can be read again during this browser session. Keep only
  // small catalogs/handles when unused meshes and curves are evicted.
  const loaded = [...libraries.values()].filter(l => l.gltf && (l.url || l.sourceFile));
  if (loaded.length <= 4) return;
  const protectedIds = new Set([...visibleLibraryIds, ...cards.filter(c => c.view).map(c => c.library.id)]);
  if (active?.library) protectedIds.add(active.library);
  if (nextLibraryId) protectedIds.add(nextLibraryId);
  const candidates = loaded.filter(l => !protectedIds.has(l.id) && !l.pending).sort((a, b) => a.used - b.used);
  for (const library of candidates.slice(0, Math.max(0, loaded.length - 4))) {
    const geometry = new Set(), skeletons = new Set();
    library.gltf.scene.traverse(o => { if (o.geometry) geometry.add(o.geometry); if (o.skeleton) skeletons.add(o.skeleton); });
    geometry.forEach(g => g.dispose()); skeletons.forEach(s => s.dispose());
    library.gltf = null; library.status = 'idle';
  }
}
async function reloadLibraries(notify = true) {
  const button = $('reloadLibraries'); button.disabled = true;
  try {
    const response = await fetch('/api/info', { cache: 'no-store' }); const info = await response.json();
    if (!response.ok) throw new Error(info.error || 'Could not read library manifest.');
    let added = 0; const discover = [];
    for (const meta of info.libraries || []) {
      if (!meta.url) continue;
      if (!libraries.has(meta.id)) added++;
      const library = registerLibrary(meta);
      // Older manifest records need one download to discover clip names.
      if (!library.clips.length && !library.gltf) discover.push(ensureLibrary(library));
    }
    refreshPackages(); renderCards(); libraryStatus();
    await Promise.all(discover);
    libraryStatus();
    if (notify) toast(added ? `${added} new package(s) available. Your proposal is unchanged.` : 'Library list refreshed. Your proposal is unchanged.');
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; }
}
async function parseLocalFile(buffer, name) {
  if (/\.fbx$/i.test(name)) {
    const scene = fbxLoader.parse(buffer, '');
    return { scene, animations: scene.animations || [] };
  }
  return loader.parseAsync(buffer, '');
}
async function importFiles(files) {
  const sources = [...files].filter(file => /\.(glb|fbx)$/i.test(file.name));
  if (!sources.length) { toast('Choose animated GLB or FBX files. Unreal UASSET packs need a preview export first.'); return; }
  let added = 0; const failed = [];
  for (const file of sources) {
    $('libraryStatus').textContent = `Reading ${file.name}…`;
    try {
      const buffer = await file.arrayBuffer();
      const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', buffer))].map(b => b.toString(16).padStart(2, '0')).join('');
      const id = `local-${hash.slice(0, 24)}`;
      if (libraries.has(id)) { Object.assign(libraries.get(id), { sourceFile: file, error: null }); continue; }
      const gltf = await parseLocalFile(buffer, file.name);
      addLibrary(gltf, { id, name: file.name.replace(/\.(glb|fbx)$/i, ''), fileName: file.webkitRelativePath || file.name, sourceHash: hash, sourceFile: file }); added++;
      evictLibraries();
    } catch (error) { failed.push(`${file.name}: ${error.message}`); }
  }
  libraryStatus(); if (added) changed();
  toast(failed.length ? `${added} added; ${failed.length} unavailable. ${failed[0]}` : `${added} library file(s) added. Files stay on this PC; reselect them after reopening.`);
}
function libraryStatus(extra = '') {
  const all = [...libraries.values()], ready = all.filter(l => l.gltf).length, loading = all.filter(l => l.pending).length, failed = all.filter(l => l.error).length;
  $('libraryStatus').textContent = `${libraries.size} packages · ${all.reduce((n, l) => n + l.clips.length, 0)} clips · ${ready} loaded${loading ? ` · ${loading} loading` : ''}${failed ? ` · ${failed} unavailable` : ''}${extra ? ' · ' + extra : ''}`;
}
function exportProposal() {
  const proposal = { ...structuredClone(board), libraries: [...new Map([...(board.libraries || []), ...metadata()].map(l => [l.id, l])).values()], playbackPlan: playbackPlan(board.items) };
  const url = URL.createObjectURL(new Blob([JSON.stringify(proposal, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = `MotionProposal-${new Date().toISOString().slice(0, 10)}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast('Proposal exported with source trims, playback modes, loop boundaries and notes.');
}

$('search').oninput = renderCards; $('package').onchange = renderCards; $('showBasics').onchange = renderCards;
$('cardMotion').onclick = () => { cardsPlaying = !cardsPlaying; $('cardMotion').textContent = cardsPlaying ? 'Pause card previews' : 'Play card previews'; };
$('cardSpeed').value = String(cardSpeed);
$('cardSpeed').onchange = () => {
  const speed = Number($('cardSpeed').value);
  if (![0.25, 0.5, 1, 2].includes(speed)) return;
  cardSpeed = speed;
  try { localStorage.setItem('motionBoard.cardSpeed', String(speed)); } catch { /* Keep the current selection without persistence. */ }
};
$('loadFiles').onclick = () => $('files').click(); $('loadFolder').onclick = () => $('folder').click();
$('reloadLibraries').onclick = () => reloadLibraries();
$('files').onchange = () => importFiles($('files').files); $('folder').onchange = () => importFiles($('folder').files);
$('export').onclick = exportProposal;
for (const key of ['start', 'end', 'duration', 'repeatCount', 'playbackSpeed']) $(key).onchange = () => edit(key, Number($(key).value));
$('playbackMode').onchange = () => edit('playbackMode', $('playbackMode').value);
$('trimIn').onchange = () => edit('start', Number($('trimIn').value)); $('trimOut').onchange = () => edit('end', Number($('trimOut').value));
for (const key of ['trimIn', 'trimOut']) $(key).oninput = () => { const max = Number($(key).max); $('trimFill').style.left = `${100 * Number($('trimIn').value) / max}%`; $('trimFill').style.right = `${100 * (1 - Number($('trimOut').value) / max)}%`; };
$('reverse').onchange = () => edit('reverse', $('reverse').checked); $('note').onchange = () => edit('note', $('note').value.slice(0, 4000));
$('addSelected').onclick = () => { if (active?.clip && nextSlot() !== undefined) addToSlot(libraries.get(active.library), clipFor(active), nextSlot()); };
$('addNote').onclick = () => {
  const slot = nextSlot(); if (slot === undefined) return toast('All eight slots are full. Remove a slot first.');
  checkpoint(); const item = { id: crypto.randomUUID(), clip: null, slot, start: 0, end: 0, duration: 2, reverse: false, note: '' };
  board.items.push(item); changed(); selectSlot(item); $('note').focus();
};
$('undo').onclick = () => { if (!history.length) return; board = history.pop(); active = null; selectedId = null; playing = false; setMain(null); changed(); renderEditor(); $('undo').disabled = !history.length; };
$('play').onclick = () => { if (sequence) { sequence = false; elapsed = 0; playing = true; } else playing = !playing; renderEditor(); };
$('playSequence').onclick = () => { if (sequence) { playing = !playing; return; } sequence = true; elapsed = 0; playing = true; renderEditor(); };
$('restart').onclick = () => { elapsed = 0; };
$('scrub').oninput = () => { elapsed = Number($('scrub').value); playing = false; };
$('resetView').onclick = () => { if (mainView) frameCamera(mainView); };
window.addEventListener('resize', () => renderer.setSize(innerWidth, innerHeight));
document.addEventListener('visibilitychange', () => { lastFrame = 0; });

function animate(now) {
  requestAnimationFrame(animate);
  if (document.hidden || now - lastFrame < 33) return;
  const dt = lastFrame ? Math.min((now - lastFrame) / 1000, 0.1) : 0; lastFrame = now;
  // Card browsing speed is independent of authored clip and sequence timing.
  if (cardsPlaying) cardTime += dt * cardSpeed;
  const length = sequence ? total() : active?.duration || 0;
  if (!sequence && active?.clip && !mainView) setMain(active);
  // Buffer a missing package instead of letting its excerpt elapse unseen.
  const currentItem = sequence ? timeline(board.items, elapsed)?.item : active;
  if (currentItem?.clip) ensureLibrary(libraries.get(currentItem.library), true);
  nextLibraryId = null;
  if (sequence && currentItem) {
    const ordered = [...board.items].sort((a, b) => a.slot - b.slot);
    const next = ordered[(ordered.findIndex(item => item.id === currentItem.id) + 1) % ordered.length];
    if (next?.clip) { nextLibraryId = next.library; ensureLibrary(libraries.get(next.library)); }
  }
  const buffered = !currentItem?.clip || !!loadedClipFor(currentItem);
  elapsed = advancePlayback(elapsed, dt, { playing, buffered, duration: length });
  if (sequence) {
    const current = timeline(board.items, elapsed);
    if (current) { active = current.item; setMain(active); if (selectedId !== active.id) { selectedId = active.id; renderEditor(); renderSlots(); } if (mainView) { mainView.action.time = Math.min(mainView.clip.duration - 0.00001, sourceTime(active, current.elapsed)); mainView.mixer.update(0); } }
  } else if (active && mainView) { mainView.action.time = Math.min(mainView.clip.duration - 0.00001, sourceTime(active, elapsed)); mainView.mixer.update(0); }
  $('play').textContent = playing && !sequence ? 'Ⅱ Pause clip' : '▶ Play clip';
  $('playSequence').textContent = sequence && playing ? 'Ⅱ Pause sequence' : '▶ Play sequence';
  $('scrub').max = length || 1; $('scrub').value = elapsed; $('clock').textContent = `${seconds(elapsed)} / ${seconds(length)} s`;
  // Scene backgrounds change the renderer's clear state. Reset alpha before
  // clearing the shared overlay or it hides the page text on the next frame.
  followMotion(mainView); controls.update(); renderer.setScissorTest(false); renderer.setClearColor(0x000000, 0); renderer.clear(); renderer.setScissorTest(true);
  if (mainView) draw(mainView, $('stage'));
  const bounds = $('cards').getBoundingClientRect(); let visible = 0;
  visibleLibraryIds.clear();
  for (const card of cards) {
    const rect = card.viewport.getBoundingClientRect();
    const onScreen = rect.bottom > bounds.top && rect.top < bounds.bottom && rect.bottom > 0 && rect.top < innerHeight;
    if (!onScreen || visible >= 12) { if (card.view) { disposeView(card.view); card.view = null; } continue; }
    visible++;
    visibleLibraryIds.add(card.library.id);
    if (!card.library.gltf) {
      ensureLibrary(card.library);
      card.viewport.textContent = card.library.error ? 'Preview unavailable · Reload libraries to retry' : 'Loading preview…';
      continue;
    }
    const loadedClip = loadedClipFor({ library: card.library.id, clip: card.clip.name });
    if (!loadedClip) { card.viewport.textContent = 'This clip is not in the exported file.'; continue; }
    card.viewport.textContent = ''; card.library.used = now;
    const newView = !card.view;
    if (newView) card.view = makeView(card.library, loadedClip);
    if (newView || (cardsPlaying && now - lastCards >= 85)) { card.view.action.time = cardTime % loadedClip.duration; card.view.mixer.update(0); }
    followMotion(card.view);
    draw(card.view, card.viewport, bounds);
  }
  if (now - lastCards >= 85) lastCards = now;
}
requestAnimationFrame(animate);

async function boot() {
  try {
    const savedResponse = await fetch('/api/project'); const saved = await savedResponse.json();
    if (!savedResponse.ok) throw new Error(saved.error || 'Could not read saved board.');
    revision = saved.revision;
    if (saved.project) { board = saved.project; board.items = board.items.map((item, i) => ({ ...item, slot: item.slot ?? i })); }
    $('saveStatus').textContent = saved.project ? 'Saved board restored' : 'Ready · saves on this PC';
    renderSlots(); renderEditor();
    await reloadLibraries(false);
    libraryStatus();
    const first = [...libraries.values()][0];
    if (!active) {
      if (first?.clips.length) selectClip(first, first.clips.find(c => /Backflip/.test(c.name)) || first.clips[0]);
      else { $('stageMessage').textContent = 'Add an animated GLB to begin.'; renderCards(); }
    }
  } catch (error) { $('saveStatus').textContent = 'Opening failed'; toast(error.message); $('libraryStatus').textContent = error.message; }
}
boot();
