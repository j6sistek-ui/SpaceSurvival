export const SLOT_COUNT = 8;
export const PLAYBACK_MODES = ['stretch', 'repeat-duration', 'repeat-count'];

// duration always means occupied timeline seconds, never the source trim length.
// Missing fields retain the original one-pass stretch behavior of saved boards.
export function playbackTiming(item) {
  const mode = item.playbackMode ?? 'stretch';
  const span = item.end - item.start;
  const speed = mode === 'stretch' ? span / item.duration : (item.playbackSpeed ?? 1);
  const cycleDuration = mode === 'stretch' ? item.duration : span / speed;
  return { mode, span, speed, cycleDuration, duration: item.duration,
    cycles: mode === 'stretch' ? 1 : item.duration / cycleDuration };
}

export function sourceTime(item, elapsed) {
  const timing = playbackTiming(item);
  const t = Math.min(item.duration, Math.max(0, elapsed));
  const cycles = t / timing.cycleDuration;
  const nearest = Math.round(cycles);
  const atBoundary = Math.abs(cycles - nearest) <= 1e-9;
  // Interior boundaries begin the next loop. The final endpoint shows the
  // completed last loop (or the actual partial-loop pose), never an extra reset.
  const p = timing.mode === 'stretch' ? t / item.duration
    : t === item.duration && atBoundary && nearest > 0 ? 1
    : atBoundary ? 0 : cycles - Math.floor(cycles);
  return item.reverse ? item.end - p * (item.end - item.start) : item.start + p * (item.end - item.start);
}

export function advancePlayback(elapsed, delta, { playing, buffered, duration }) {
  return playing && buffered && duration > 0 ? (elapsed + delta) % duration : elapsed;
}

export function editItem(item, field, value, clipDuration) {
  const next = { ...item, [field]: value };
  if (field === 'playbackMode') {
    if (value === 'stretch') { delete next.playbackSpeed; delete next.repeatCount; }
    else {
      next.playbackSpeed = item.playbackSpeed ?? 1;
      if (value === 'repeat-count') next.repeatCount = item.repeatCount ?? 1;
      else delete next.repeatCount;
    }
  }
  const mode = next.playbackMode ?? 'stretch';
  if (mode === 'stretch' && (field === 'start' || field === 'end')) {
    next.duration = Math.max(0.05, (next.end - next.start) * item.duration / (item.end - item.start));
  }
  if (mode === 'repeat-count') next.duration = (next.end - next.start) / (next.playbackSpeed ?? 1) * next.repeatCount;
  // Re-exports may shorten metadata by a source frame. A timing-only edit must
  // preserve the exact saved trim; newly entered ends must fit the current file.
  validateItem(next, field === 'end' ? clipDuration : Math.max(clipDuration, item.end));
  return next;
}

export function playbackPlan(items) {
  let offset = 0;
  return [...items].sort((a, b) => a.slot - b.slot).map(item => {
    const result = { id: item.id, slot: item.slot, timelineStart: offset,
      timelineEnd: offset + item.duration, duration: item.duration };
    offset += item.duration;
    if (item.clip === null) return { ...result, mode: 'direction-note' };
    const timing = playbackTiming(item);
    const loopBoundaries = [0];
    for (let i = 1; i < Math.ceil(timing.cycles - 1e-9); i++) loopBoundaries.push(i * timing.cycleDuration);
    loopBoundaries.push(item.duration);
    return { ...result, mode: timing.mode, speed: timing.speed, cycles: timing.cycles,
      cycleDuration: timing.cycleDuration, reverse: !!item.reverse,
      sourceStart: sourceTime(item, 0), sourceEnd: sourceTime(item, item.duration),
      loopBoundaries, boundaryRule: 'Interior boundaries restart the trim; final boundary samples the completed or partial cycle. No blending.' };
  });
}

export function timeline(items, time) {
  let offset = 0;
  const ordered = [...items].sort((a, b) => a.slot - b.slot);
  for (let i = 0; i < ordered.length; i++) {
    const item = ordered[i];
    if (time < offset + item.duration || i === ordered.length - 1) {
      return { item, offset, elapsed: Math.max(0, Math.min(item.duration, time - offset)) };
    }
    offset += item.duration;
  }
  return null;
}

export function placeItem(items, item, slot) {
  if (!Number.isInteger(slot) || slot < 0 || slot >= SLOT_COUNT) throw new Error('Choose a slot from 1 to 8.');
  const source = items.find(x => x.id === item.id);
  const occupied = items.find(x => x.slot === slot && x.id !== item.id);
  const next = items.filter(x => x.id !== item.id && x.slot !== slot);
  if (source && occupied) next.push({ ...occupied, slot: source.slot });
  next.push({ ...item, slot });
  return next.sort((a, b) => a.slot - b.slot);
}

export function makeItem(library, clip, slot) {
  return { id: crypto.randomUUID(), slot, library, clip: clip.name, start: 0, end: clip.duration,
    duration: clip.duration, reverse: false, note: '' };
}

export function validateItem(item, clipDuration) {
  if (![item.start, item.end, item.duration].every(Number.isFinite)) throw new Error('Enter valid seconds.');
  if (item.start < 0 || item.end > clipDuration + 0.001 || item.end - item.start < 0.01) throw new Error('The end must come after the start, within this clip.');
  if (item.duration < 0.05 || item.duration > 3600) throw new Error('Choose a duration between 0.05 and 3600 seconds.');
  const mode = item.playbackMode ?? 'stretch';
  if (item.playbackMode !== undefined && !PLAYBACK_MODES.includes(item.playbackMode)) throw new Error('Choose a supported playback mode.');
  if (item.playbackSpeed !== undefined && (!Number.isFinite(item.playbackSpeed) || item.playbackSpeed < 0.05 || item.playbackSpeed > 8)) throw new Error('Choose playback speed between 0.05 and 8×.');
  if (item.repeatCount !== undefined && (!Number.isFinite(item.repeatCount) || item.repeatCount <= 0 || item.repeatCount > 10000)) throw new Error('Choose a repeat count greater than zero, up to 10000.');
  if (mode === 'repeat-count') {
    if (item.repeatCount === undefined) throw new Error('Enter a repeat count.');
    const expected = (item.end - item.start) / (item.playbackSpeed ?? 1) * item.repeatCount;
    if (Math.abs(item.duration - expected) > 1e-7 * Math.max(1, expected)) throw new Error('Repeat count and total duration disagree.');
  }
  if (playbackTiming(item).cycles > 10000 + 1e-9) throw new Error('Use at most 10000 repeats per slot.');
  return item;
}
