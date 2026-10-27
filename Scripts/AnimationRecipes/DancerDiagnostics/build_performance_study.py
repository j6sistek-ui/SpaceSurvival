"""CPU-only pose animatic. Read private sources; never modify a rig or action.

The result is an articulated planning proxy, not retargeting or skin/contact QA.
Plan documentation must exist before rendering. No Blender/Unreal/GPU calls.
"""
import hashlib
import html
import json
import math
import struct
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'SourceAssets/PerformancePlan_20261027'
WORK = ROOT / '.agent/local/PerformancePlan_20261027'
RAW = ROOT / '.agent/local/AnimationReview_20261025/RawMotionSourceReview'
PLAN = ROOT / 'docs/production/G1_G2_PERFORMANCE_STUDY.md'
assert PLAN.is_file(), 'Document current state, gaps and target before rendering.'
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)
W, H = 1280, 800
FPS, DURATION = 2, 80
NAMES = ['pelvis', 'chest', 'neck', 'head', 'shoulder_l', 'elbow_l', 'wrist_l',
         'finger_l', 'shoulder_r', 'elbow_r', 'wrist_r', 'finger_r',
         'hip_l', 'knee_l', 'ankle_l', 'toe_l', 'hip_r', 'knee_r', 'ankle_r', 'toe_r']
STANDARD = ['pelvis', 'spine_03', 'neck_01', 'head', 'upperarm_l', 'lowerarm_l', 'hand_l',
            'middle_03_l', 'upperarm_r', 'lowerarm_r', 'hand_r', 'middle_03_r',
            'thigh_l', 'calf_l', 'foot_l', 'ball_l', 'thigh_r', 'calf_r', 'foot_r', 'ball_r']
SOURCE = ['hips_JNT', 'spine2_JNT', 'neck_JNT', 'head_JNT', 'l_arm_JNT', 'l_forearm_JNT',
          'l_hand_JNT', 'l_handMiddle3_JNT', 'r_arm_JNT', 'r_forearm_JNT', 'r_hand_JNT',
          'r_handMiddle3_JNT', 'l_upleg_JNT', 'l_leg_JNT', 'l_foot_JNT', 'l_toebase_JNT',
          'r_upleg_JNT', 'r_leg_JNT', 'r_foot_JNT', 'r_toebase_JNT']
SECTIONS = [
    ('S01', 0, 8, 'Gather and exchange', 'g1', 0, 3.5, 'support', 'Knee gathers; opposite leg opens; free arm answers.'),
    ('S02', 8, 16, 'Cradle into an unequal fan', 'g1', 4.5, 9.5, 'support', 'Compact -> scissor -> unequal fan -> re-fold.'),
    ('S03', 16, 22, 'Coil and prepare release', 'g1', 10, 13, 'support', 'Torso coils; knee and free arm prepare departure.'),
    ('S04', 22, 27.5, 'Preserve the liked departure', 'baseline', 22, 27.45, 'original', 'Existing body motion, shown on the same planning proxy.'),
    ('S05', 27.5, 32.5, 'Complete the backward flip', 'backflip', 0, .65, 'free', 'Gather -> inversion -> lead foot -> staggered opening.'),
    ('S06', 32.5, 35.5, 'Twist, unfold, identify the pole', 'twist', .1, .85, 'free', 'Unequal knees; chest opens as the free turn resolves.'),
    ('S07', 35.5, 38, 'Turn into the reaching arc', 'dance6', 3.7, 4.8366667, 'approach', 'Torso turns toward the pole; movement continues into the reach.'),
    ('S08', 38, 44, 'Your Dance6 reach and phrase', 'dance6', 4.8366667, 10.899999, 'reach/support', 'Left hand rises into the catch; legs and torso continue the phrase.'),
    ('S09', 44, 54, 'G2 weave and leg exchange', 'g2', .5, 7.5, 'support', 'New facing and alternating leg shapes, not one held orbit.'),
    ('S10', 54, 63, 'Release into a lateral roll', 'sideflip', .05, .7, 'free', 'Lateral inversion -> cradle -> staggered extension.'),
    ('S11', 63, 67, 'Reach through the returning arc', 'g2', 6, 7.5, 'catch', 'Hand contact loads the torso while the leg sweep continues.'),
    ('S12', 67, 80, 'Supported fan and gathering finish', 'g2', 7.5, 12.5, 'support', 'Fan -> fold -> reopen -> initial support family; join unproven.'),
]
SOURCES = {}


def note_source(path):
    SOURCES[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()


def quat_matrix(q):
    x, y, z, w = q / max(np.linalg.norm(q), 1e-12)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


class GLBPose:
    def __init__(self, path, clip):
        note_source(path)
        raw = path.read_bytes()
        length = struct.unpack_from('<I', raw, 12)[0]
        self.g = json.loads(raw[20:20+length])
        self.bin = raw[28+length:]
        self.a = next(a for a in self.g['animations'] if a['name'] == clip)
        self.idx = {n.get('name'): i for i, n in enumerate(self.g['nodes'])}
        self.parent = {c: i for i, n in enumerate(self.g['nodes']) for c in n.get('children', [])}
        self.channels = []
        for channel in self.a['channels']:
            sampler = self.a['samplers'][channel['sampler']]
            assert sampler.get('interpolation', 'LINEAR') in ['LINEAR', 'STEP']
            self.channels.append((channel['target'], self.access(sampler['input']).ravel(),
                                  self.access(sampler['output']), sampler.get('interpolation', 'LINEAR')))

    def access(self, index):
        a = self.g['accessors'][index]
        v = self.g['bufferViews'][a['bufferView']]
        typ = {5126: '<f4', 5123: '<u2', 5125: '<u4', 5121: 'u1'}[a['componentType']]
        cols = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
        size = np.dtype(typ).itemsize
        return np.ndarray((a['count'], cols), typ, self.bin,
                          v.get('byteOffset', 0)+a.get('byteOffset', 0),
                          strides=(v.get('byteStride', size*cols), size)).copy()

    def sample(self, t):
        values = [{k: np.array(n.get(k, default), dtype=float) for k, default in
                   [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]}
                  for n in self.g['nodes']]
        for target, times, vals, interpolation in self.channels:
            if target['path'] == 'weights':
                continue
            lo = max(0, min(len(times)-1, np.searchsorted(times, t, side='right')-1))
            hi = min(lo+1, len(times)-1)
            f = 0 if hi == lo or interpolation == 'STEP' else np.clip((t-times[lo])/(times[hi]-times[lo]), 0, 1)
            a, b = vals[lo], vals[hi]
            if target['path'] == 'rotation' and np.dot(a, b) < 0:
                b = -b
            value = a*(1-f)+b*f
            if target['path'] == 'rotation':
                value = value/max(np.linalg.norm(value), 1e-12)
            values[target['node']][target['path']] = value
        world = {}

        def matrix(i):
            if i not in world:
                v = values[i]
                m = np.eye(4)
                if 'matrix' in self.g['nodes'][i]:
                    m = np.array(self.g['nodes'][i]['matrix']).reshape(4, 4).T
                else:
                    m[:3, :3] = quat_matrix(v['rotation']) @ np.diag(v['scale'])
                    m[:3, 3] = v['translation']
                world[i] = matrix(self.parent[i]) @ m if i in self.parent else m
            return world[i]
        positions = np.array([matrix(self.idx[n])[:3, 3] for n in STANDARD])
        # glTF Y-up -> Blender-style Z-up.
        return positions[:, [0, 2, 1]] * [1, -1, 1]


raw_sources = {}
for key in ('g1', 'g2'):
    p = RAW/key.upper()/'Joints.npz'
    note_source(p)
    data = np.load(p, allow_pickle=False)
    indices = [list(data['names']).index(n) for n in SOURCE]
    raw_sources[key] = (data['seconds'], data['positions'][:, indices])
glb_dir = ROOT/'SourceAssets/MotionBoard/libraries'
native = {key: GLBPose(glb_dir/file, clip) for key, file, clip in [
    ('dance6', 'sensual.glb', 'AS_Dance6'), ('backflip', 'flips.glb', 'RM_Flip_B'),
    ('twist', 'flips.glb', 'RM_ButterflyTwist_L'), ('sideflip', 'flips.glb', 'RM_Flip_L')]}
baseline_file = WORK/'Baseline2Hz.npz'
assert baseline_file.is_file(), 'Export current proof joints before the study.'
note_source(baseline_file)
base = np.load(baseline_file, allow_pickle=False)
tail_file = WORK/'G1Tail24Hz.npz'
note_source(tail_file)
tail = np.load(tail_file, allow_pickle=False)


def interpolate(times, poses, t):
    hi = min(len(times)-1, max(1, np.searchsorted(times, t)))
    lo = hi-1
    f = np.clip((t-times[lo])/max(times[hi]-times[lo], 1e-9), 0, 1)
    return poses[lo]*(1-f)+poses[hi]*f


def rotation(rx=0, ry=0, rz=0):
    a, b, c = np.radians([rx, ry, rz])
    return np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]]) @ np.array(
        [[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]]) @ np.array(
        [[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def normalize(p):
    p = p-p[0]
    height = (np.linalg.norm(p[3]-p[0]) + np.linalg.norm(p[12]-p[13]) +
              np.linalg.norm(p[13]-p[14]) + .15)
    return p*(1.72/height)


def raw_pose(key, t):
    if key in raw_sources:
        return normalize(interpolate(*raw_sources[key], t))
    if key == 'baseline':
        ids = [list(base['names']).index(n) for n in STANDARD]
        return normalize(interpolate(base['times'], base['positions'][:, ids], t))
    return normalize(native[key].sample(t))


def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)


def travel_yaw(t):
    return sum((12 if x[7] in ('free', 'approach') else 22)*max(0, min(t, x[2])-x[1]) for x in SECTIONS)


def section_pose(s, t):
    sid, start, end, title, key, a, b, contact, desc = s
    u = np.clip((t-start)/(end-start), 0, 1)
    if key == 'baseline':
        ids = [list(tail['names']).index(n) for n in STANDARD]
        return interpolate(tail['times'], tail['positions'][:, ids], min(b, t))
    pose = raw_pose(key, a+(b-a)*u)
    # Spatial blocking is proposed independently from the sampled joint poses.
    # Integrate angular speed; changing phrases must not reset world phase.
    yaw = travel_yaw(t)
    tilt = 8*math.sin(t*.3)
    if contact in ('free', 'original'):
        tilt = 10
    pose = pose @ rotation(tilt, 0, yaw).T
    anchor = np.array([.035, 0, 3.0 if start < 35 else (3.15 if start < 63 else 2.95)])
    hand = 6 if 35 <= start < 54 else 10
    anchored = pose+anchor-pose[hand]
    theta = math.radians(yaw)
    center = np.array([1.55*math.cos(theta), 1.55*math.sin(theta), 2.45+.3*math.sin(t*.24)])
    if contact in ('free', 'catch', 'approach', 'reach/support'):
        index = SECTIONS.index(s)
        previous_center = section_pose(SECTIONS[index-1], start)[0]
        blend = smooth((t-start)/min(3.0, end-start))
        center = previous_center*(1-blend)+center*blend
        if contact == 'approach':
            # Aim the approach near the left-hand reach, not at a right-hand
            # waist anchor. Dance6 raises the left hand after its entry.
            target_time = 39.2
            target_pose = raw_pose('dance6', 6.05) @ rotation(8*math.sin(target_time*.3), 0, travel_yaw(target_time)).T
            target_center = np.array([.035, 0, 3.15])-target_pose[6]
            center = previous_center*(1-smooth(u))+(target_center+np.array([.3, .2, 0]))*smooth(u)
    free = pose+center
    if contact == 'support':
        result = anchored
    elif contact == 'catch':
        amount = smooth((u-.12)/.7)
        result = free*(1-amount)+anchored*amount
    elif contact == 'reach/support':
        amount = smooth((t-start)/1.2)
        result = free*(1-amount)+anchored*amount
    else:
        result = free
    # Arrive at the saved departure before it starts, preserving that phrase's
    # world-space motion instead of teleporting from the proposed support path.
    if sid == 'S03' and t > end-1.5:
        departure = section_pose(SECTIONS[3], end)
        f = smooth((t-(end-1.5))/1.5)
        result = result*(1-f)+departure*f
    if sid == 'S10' and u > .65:
        donor = raw_pose('g1', 5+(u-.65)/.35*1.5) @ rotation(0, 0, yaw).T + center
        result = result*(1-smooth((u-.65)/.35))+donor*smooth((u-.65)/.35)
    if sid == 'S12' and u > .78:
        donor = raw_pose('g1', (u-.78)/.22*.35) @ rotation(0, 0, yaw).T
        donor += anchor-donor[10]
        result = result*(1-smooth((u-.78)/.22))+donor*smooth((u-.78)/.22)
    return result


def pose_at(t):
    index = next((i for i, s in enumerate(SECTIONS) if s[1] <= t < s[2]), len(SECTIONS)-1)
    section = SECTIONS[index]
    pose = section_pose(section, t)
    # Simple planning crossfades make pose changes visible, not a rig solution.
    if index and section[0] != 'S04' and t < section[1]+.5:
        prior = section_pose(SECTIONS[index-1], SECTIONS[index-1][2])
        f = smooth((t-section[1])/.5)
        pose = prior*(1-f)+pose*f
    return pose, section


def source_label(s, t):
    if s[0] == 'S03' and t > s[2]-1.5:
        return 'g1 + saved departure entry'
    if s[0] == 'S10' and (t-s[1])/(s[2]-s[1]) > .65:
        return 'sideflip + g1 cradle'
    if s[0] == 'S12' and (t-s[1])/(s[2]-s[1]) > .78:
        return 'g2 + g1 entry'
    return s[4]


def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', size)


def view_points(p, side=False):
    r = rotation(0, 0, 86 if side else -28)
    q = p @ r.T
    # Orthographic, slight down angle. Fixed framing exposes travel.
    q = q @ rotation(10, 0, 0).T
    scale = 91 if side else 111
    ox = 970 if side else 338
    return np.column_stack((ox+q[:, 0]*scale, 540-(q[:, 2]-1.1)*scale)), q[:, 1], scale


def draw_figure(draw, points, side=False):
    xy, depth, scale = view_points(points, side)
    shapes = []
    torso = [4, 8, 16, 12]
    shapes.append((np.mean(depth[torso]), 'poly', [tuple(xy[i]) for i in torso], (154, 187, 203), 0))
    for a, b, width in [(0, 1, .28), (1, 2, .11), (2, 3, .105),
                         (4, 5, .12), (5, 6, .09), (6, 7, .07),
                         (8, 9, .12), (9, 10, .09), (10, 11, .07),
                         (12, 13, .18), (13, 14, .12), (14, 15, .09),
                         (16, 17, .18), (17, 18, .12), (18, 19, .09)]:
        color = (118, 210, 202) if a in [4, 5, 6, 12, 13, 14] else (189, 204, 225)
        if a in [0, 1, 2]:
            color = (156, 190, 208)
        shapes.append(((depth[a]+depth[b])/2, 'line', (tuple(xy[a]), tuple(xy[b])), color, max(3, int(scale*width))))
    shapes.sort(key=lambda a: -a[0])
    for _, kind, points2, color, width in shapes:
        if kind == 'poly':
            draw.polygon(points2, fill=color)
        else:
            draw.line(points2, fill=color, width=width)
            for x, y in points2:
                rr = width/2
                draw.ellipse((x-rr, y-rr, x+rr, y+rr), fill=color)
    x, y = xy[3]
    draw.ellipse((x-scale*.085, y-scale*.13, x+scale*.085, y+scale*.08), fill=(204, 215, 226))
    for i, color in [(6, '#68e1cd'), (10, '#ffba66')]:
        x, y = xy[i]
        draw.ellipse((x-4, y-4, x+4, y+4), fill=color)


def render(t, index):
    im = Image.new('RGB', (W, H), '#111e2b')
    draw = ImageDraw.Draw(im)
    p, s = pose_at(t)
    draw.rectangle((20, 96, 668, 609), fill='#1b2c3b')
    draw.rectangle((688, 96, 1260, 609), fill='#172735')
    draw.text((28, 17), 'ZERO-G / FULL PERFORMANCE STUDY', font=font(26), fill='#f4f7fb')
    draw.text((30, 56), 'CPU concept proxy  |  2 frames/sec  |  source poses + proposed travel', font=font(17), fill='#9fb8ce')
    draw.text((1020, 28), f'{s[0]}  F{index+1:03d}', font=font(24), fill='#70e0cc')
    for side in [False, True]:
        ring = np.array([[2.8*math.cos(a), 2.8*math.sin(a), 1.05] for a in np.linspace(0, 2*math.pi, 81)])
        xy, _, _ = view_points(ring, side)
        draw.line(list(map(tuple, xy)), fill='#3b566b', width=2)
        pole, _, _ = view_points(np.array([[0, 0, .45], [0, 0, 4.7]]), side)
        draw.line(list(map(tuple, pole)), fill='#fb8c36', width=7)
        draw_figure(draw, p, side)
        draw.text((710 if side else 38, 109), 'SIDE VIEW' if side else 'FRONT / THREE-QUARTER', font=font(15), fill='#a3bacd')
    draw.text((30, 624), f'{t:04.1f} / {DURATION}s    {s[3]}', font=font(25), fill='#ffffff')
    draw.text((30, 663), s[8], font=font(19), fill='#c4d9e8')
    draw.text((30, 696), f'{s[7].upper()}  |  source: {source_label(s,t)}  |  R hand: amber / L hand: teal', font=font(17), fill='#8de0d1')
    draw.text((30, 766), 'Planning only: no finger grip, skin weights, collision or seamless-loop validation.', font=font(15), fill='#96aabd')
    for j, x in enumerate(SECTIONS):
        x0, x1 = 30+1220*x[1]/DURATION, 30+1220*x[2]/DURATION
        draw.rectangle((x0, 729, x1-2, 750), fill='#4fb6aa' if x[0] == s[0] else '#314c61')
        draw.text((x0+3, 731), x[0], font=font(11), fill='#ffffff')
    x = 30+1220*t/DURATION
    draw.line((x, 724, x, 756), fill='#ffffff', width=2)
    return im, p, s


def write_review():
    rows = '\n'.join(
        f'<button data-time="{s[1]}"><b>{s[0]} · {s[1]:g}–{s[2]:g}s</b>'
        f'<span>{html.escape(s[3])}</span></button>' for s in SECTIONS)
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Full performance study · 2 fps</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#101b27;color:#e6f0f6;font:16px/1.5 system-ui}
main{max-width:1300px;margin:auto;padding:24px}h1{font-size:28px;margin:4px 0 12px}
p{max-width:900px;color:#b8cbd9}a{color:#75dfd0}video{width:100%;display:block;background:#111e2b}
.controls{display:flex;flex-wrap:wrap;gap:12px;margin:12px 0}.sections{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
button{font:inherit;text-align:left;background:#203448;color:#edf6fa;border:1px solid #3e6075;border-radius:8px;padding:10px 14px;cursor:pointer}
button:hover,button:focus-visible{border-color:#75dfd0}button span{display:block;font-size:14px;color:#b8cbd9}
output{align-self:center;font-variant-numeric:tabular-nums}summary{cursor:pointer;padding:12px 0}img{max-width:100%}
</style><main><p>SPACE SURVIVAL · CHOREOGRAPHY PROPOSAL</p>
<h1>Full performance study — 80 seconds</h1>
<p>160 numbered frames at two frames per second. Existing source poses drive a simple figure;
the proposed travel and catches show the idea before character animation. This is not a new Vexa animation or a grip, skin-weight or collision check.</p>
<video id="movie" controls playsinline preload="metadata" poster="Overview.jpg" src="FullPerformance_2fps.mp4"></video>
<div class="controls"><button id="previous">← Previous frame</button><button id="next">Next frame →</button>
<output id="position">S01 · F001 · 0.0s</output><a href="FullPerformance_2fps.mp4" download>Download video</a></div>
<p>Choose a section below. For feedback, name the section or frame, such as “S05, F060.” Teal marks the left side; the right wrist is amber. The orange pole is a placement reference.</p>
<div class="sections">SECTIONS</div>
<p><a href="../../docs/production/G1_G2_PERFORMANCE_STUDY.md">Current-state audit and written plan</a> ·
<a href="../DanceRefinement_20261025/G1G2_Current_LegPass_Unreal.mp4">Existing 82.75-second character performance</a> ·
<a href="TargetPlan.json">Exact source/timing map</a></p>
<details><summary>Show the twelve-section overview</summary><img src="Overview.jpg" alt="Twelve sections shown from two angles"></details>
<p>The plan restores G1/G2 leg variety, keeps the liked departure, completes free flips, and includes your Dance6 selection.
Finger contact, full-rate transitions, the final loop and chamber fit remain to be authored and validated.</p>
<script>
const v=document.querySelector('#movie'),o=document.querySelector('#position');
const sections=PLAN;
function show(){const t=v.currentTime,s=sections.find(s=>t>=s.start&&t<s.end)||sections.at(-1);
o.textContent=`${s.id} · F${String(Math.min(160,Math.floor(t*2)+1)).padStart(3,'0')} · ${t.toFixed(1)}s`;}
function seek(t){v.pause();v.currentTime=Math.max(0,Math.min(79.5,t));show();}
document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>seek(Number(b.dataset.time)));
document.querySelector('#previous').onclick=()=>seek((Math.ceil(v.currentTime*2)-1)/2);
document.querySelector('#next').onclick=()=>seek((Math.floor(v.currentTime*2)+1)/2);
v.addEventListener('timeupdate',show);
</script></main></html>'''
    page = page.replace('SECTIONS', rows).replace('const sections=PLAN;', 'const sections='+json.dumps(
        [dict(id=s[0], start=s[1], end=s[2]) for s in SECTIONS])+';')
    (OUT/'Review.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    plan_data = {'fps': FPS, 'seconds': DURATION, 'sections': [dict(zip(
        ['id', 'start', 'end', 'title', 'source', 'sourceStart', 'sourceEnd', 'contact', 'direction'], s)) for s in SECTIONS],
        'scope': 'Articulated proxy plan. Source motion not edited. Proposed root travel, anchor blocking and simple crossfades are not production choreography.'}
    (OUT/'TargetPlan.json').write_text(json.dumps(plan_data, indent=2))
    frames_dir = WORK/'Frames'
    frames_dir.mkdir(exist_ok=True)
    frame_index, all_poses = [], []
    for i, t in enumerate(np.arange(0, DURATION, 1/FPS)):
        im, p, s = render(t, i)
        im.save(frames_dir/f'{i:04d}.png')
        frame_index.append({'frame': f'F{i+1:03d}', 'seconds': float(t), 'section': s[0],
                            'source': source_label(s,t), 'contactIntent': s[7]})
        all_poses.append(p)
    np.savez_compressed(OUT/'ProxyPoseSamples.npz', times=np.arange(0, DURATION, 1/FPS), names=NAMES, positions=all_poses)
    (OUT/'Frames.json').write_text(json.dumps(frame_index, indent=2))
    overview = Image.new('RGB', (1280, 1200), '#101d29')
    for i, s in enumerate(SECTIONS):
        frame = round(((s[1]+s[2])/2)*FPS)
        tile = Image.open(frames_dir/f'{frame:04d}.png').resize((426, 266))
        overview.paste(tile, ((i % 3)*426, (i//3)*300))
    overview.save(OUT/'Overview.jpg', quality=93)
    ffmpeg = 'C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe'
    movie = OUT/'FullPerformance_2fps.mp4'
    args = [ffmpeg, '-hide_banner', '-nostdin', '-y', '-framerate', str(FPS), '-i', str(frames_dir/'%04d.png'),
            '-c:v', 'libx264', '-threads', '4', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart', str(movie)]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    write_review()
    (OUT/'Receipt.json').write_text(json.dumps({'sources': SOURCES, 'planSha256': hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        'scriptSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'frames': len(frame_index), 'fps': FPS,
        'seconds': DURATION, 'movieSha256': hashlib.sha256(movie.read_bytes()).hexdigest(),
        'gpu': False, 'scope': plan_data['scope']}, indent=2))
    print(json.dumps({'movie': str(movie), 'frames': len(frame_index), 'seconds': DURATION}))
