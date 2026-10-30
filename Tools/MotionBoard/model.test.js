import { test } from 'node:test';
import assert from 'node:assert/strict';
import { placeItem, sourceTime, timeline, validateItem, editItem, playbackTiming, playbackPlan, advancePlayback } from './model.js';

test('trim, retime and reverse retain source boundaries', () => {
  const item = {start:2,end:5,duration:6,reverse:false};
  assert.equal(sourceTime(item,3),3.5);
  assert.equal(sourceTime({...item,reverse:true},0),5);
  assert.equal(sourceTime({...item,reverse:true},6),2);
  assert.equal(sourceTime(item,20),5);
});
test('sparse slots concatenate in numbered order with exact boundaries', () => {
  const items=[{id:'b',slot:7,duration:2},{id:'a',slot:1,duration:3}];
  assert.equal(timeline(items,2.9).item.id,'a');
  assert.deepEqual(timeline(items,3),{item:items[0],offset:3,elapsed:0});
  assert.equal(timeline(items,20).elapsed,2);
});
test('moving occupied slots swaps and importing replaces only the destination', () => {
  const a={id:'a',slot:0},b={id:'b',slot:1};
  assert.deepEqual(placeItem([a,b],a,1),[{...b,slot:0},{...a,slot:1}]);
  assert.deepEqual(placeItem([a,b],{id:'c'},0),[{id:'c',slot:0},b]);
  assert.throws(()=>placeItem([],a,8));
});
test('invalid trims and nonfinite timing are rejected', () => {
  const good={start:0,end:5,duration:6};
  assert.equal(validateItem(good,5),good);
  for(const bad of [{...good,start:6},{...good,end:6},{...good,duration:NaN},{...good,duration:0}]) assert.throws(()=>validateItem(bad,5));
});

const halfSecond = {id:'short',slot:0,library:'test',clip:'Half_second',start:2,end:2.5,duration:0.5,reverse:false,note:''};
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`);

test('half-second source repeats ten times in five seconds, not stretched', () => {
  let item = editItem(halfSecond, 'playbackMode', 'repeat-count', 3);
  item = editItem(item, 'repeatCount', 10, 3);
  assert.equal(item.duration, 5);
  assert.equal(playbackTiming(item).speed, 1);
  assert.equal(playbackTiming(item).cycles, 10);
  for (let cycle = 0; cycle < 10; cycle++) near(sourceTime(item, cycle * 0.5 + 0.25), 2.25);
  assert.equal(sourceTime(item, 0.5), 2); // Interior boundary starts next cycle.
  assert.equal(sourceTime(item, 5), 2.5); // Final endpoint completes last cycle.
  assert.equal(sourceTime(item, 99), 2.5);
  assert.equal(sourceTime(item, -1), 2);
});

test('repeat for seconds keeps source speed and samples a partial last cycle', () => {
  let item = editItem(halfSecond, 'playbackMode', 'repeat-duration', 3);
  item = editItem(item, 'duration', 10, 3);
  assert.equal(playbackTiming(item).cycles, 20);
  assert.equal(sourceTime(item, 0.25), 2.25);
  item = editItem(item, 'duration', 1.125, 3);
  assert.equal(playbackTiming(item).cycles, 2.25);
  assert.equal(sourceTime(item, 1.125), 2.125);
  assert.equal(sourceTime({...item,reverse:true}, 0), 2.5);
  assert.equal(sourceTime({...item,reverse:true}, 0.5), 2.5);
  assert.equal(sourceTime({...item,reverse:true}, 1.125), 2.375);
  const integral = {...item,duration:1,reverse:true};
  assert.equal(sourceTime(integral, 1), 2);
});

test('speed and trim edits preserve the selected duration or count semantics', () => {
  const counted = {...halfSecond, playbackMode:'repeat-count',repeatCount:10,duration:5};
  assert.equal(editItem(counted,'playbackSpeed',0.5,3).duration,10);
  assert.equal(editItem(counted,'start',2.25,3).duration,2.5);
  const timed = {...halfSecond,playbackMode:'repeat-duration',duration:10};
  const faster = editItem(timed,'playbackSpeed',2,3);
  assert.equal(faster.duration,10); assert.equal(playbackTiming(faster).cycles,40);
  assert.equal(editItem(timed,'end',3,3).duration,10);
  assert.equal(editItem({...halfSecond,duration:5},'end',3,3).duration,10); // Legacy stretch maintains speed.
  const stretch = editItem(counted,'playbackMode','stretch',3);
  assert.equal(stretch.duration,5); assert.equal(stretch.repeatCount,undefined);
  assert.equal(stretch.playbackSpeed,undefined); assert.equal(playbackTiming(stretch).speed,0.1);
});

test('JSON reload retains legacy data and repeated sampling with pause and resume', () => {
  const legacy = {...halfSecond,duration:6,note:'Keep exactly'};
  const repeat = {...halfSecond,id:'repeat',slot:2,playbackMode:'repeat-count',repeatCount:2.5,playbackSpeed:0.5,duration:2.5,reverse:true};
  const original = {version:1,title:'Old and new',items:[legacy,repeat]};
  const restored = JSON.parse(JSON.stringify(original));
  assert.deepEqual(restored,original);
  assert.equal('playbackMode' in restored.items[0],false);
  for (const t of [0,0.4,1,2,2.5]) assert.equal(sourceTime(restored.items[1],t),sourceTime(repeat,t));
  assert.equal(advancePlayback(1.25,0.1,{playing:false,buffered:true,duration:2.5}),1.25);
  assert.equal(advancePlayback(1.25,0.1,{playing:true,buffered:false,duration:2.5}),1.25);
  near(advancePlayback(1.25,0.1,{playing:true,buffered:true,duration:2.5}),1.35);
  // Card rate cannot affect the shared clock or source sampler, paused or running.
  for (const cardSpeed of [0.25,0.5,1,2]) {
    near(advancePlayback(1.25,0.1,{playing:true,buffered:true,duration:2.5,cardSpeed}),1.35);
    assert.equal(sourceTime({...repeat,cardSpeed},1.25),sourceTime(repeat,1.25));
  }
});

test('mixed sparse timeline and export preserve exact repeat boundary semantics', () => {
  const repeated = {...halfSecond,playbackMode:'repeat-count',repeatCount:10,duration:5,reverse:true};
  const after = {...halfSecond,id:'after',slot:7,duration:2};
  assert.equal(timeline([after,repeated],4.999).item.id,'short');
  assert.equal(timeline([after,repeated],5).item.id,'after');
  assert.equal(timeline([after,repeated],5).elapsed,0);
  const before = JSON.stringify([after,repeated]);
  const plan = playbackPlan([after,repeated]);
  assert.equal(JSON.stringify([after,repeated]),before);
  assert.deepEqual(plan[0].loopBoundaries,[0,0.5,1,1.5,2,2.5,3,3.5,4,4.5,5]);
  assert.equal(plan[0].sourceStart,2.5); assert.equal(plan[0].sourceEnd,2);
  assert.equal(plan[1].timelineStart,5); assert.equal(plan[1].timelineEnd,7);
  const partial = playbackPlan([{...repeated,playbackMode:'repeat-duration',duration:1.125}])[0];
  assert.deepEqual(partial.loopBoundaries,[0,0.5,1,1.125]);
  assert.equal(partial.sourceEnd,2.375);
  assert.equal(playbackPlan([{...after,clip:null}])[0].mode,'direction-note');
});

test('bad modes, speeds, counts and count-duration disagreement are rejected', () => {
  const good = {...halfSecond,playbackMode:'repeat-count',repeatCount:10,duration:5};
  for (const changes of [{playbackMode:'cycle'}, {playbackMode:null}, {playbackSpeed:NaN},
    {playbackSpeed:0}, {playbackSpeed:true}, {playbackSpeed:9}, {repeatCount:0},
    {repeatCount:'10'}, {repeatCount:Infinity}, {repeatCount:10001}, {duration:6},
    {playbackMode:'repeat-duration',duration:3600,playbackSpeed:8}]) {
    assert.throws(()=>validateItem({...good,...changes},3),JSON.stringify(changes));
  }
  const missing = {...good}; delete missing.repeatCount;
  assert.throws(()=>validateItem(missing,3));
});

test('unchanged legacy trim beyond a newer export survives timing edits only', () => {
  const legacy = {...halfSecond,start:4.87,end:10.9333,duration:8};
  const repeat = editItem(legacy,'playbackMode','repeat-duration',10.9);
  const edited = editItem(repeat,'duration',12,10.9);
  assert.equal(edited.start,4.87); assert.equal(edited.end,10.9333);
  assert.equal(legacy.duration,8); assert.equal(legacy.playbackMode,undefined);
  assert.throws(()=>editItem(edited,'end',10.92,10.9));
  assert.equal(editItem(edited,'end',10.89,10.9).end,10.89);
});
