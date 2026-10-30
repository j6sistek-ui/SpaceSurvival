"""CPU S09 proposal: source pull, knee-hook descent and released flip.

No rig, action, skin, native asset or owner board is written. The original
80-second study remains intact; outputs go to its S09Replacement subfolder.
"""
import functools
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import build_performance_study as b
import pole_entry_contact
import pole_transfer_contact
import sliding_contact

V1_SECTIONS = list(b.SECTIONS)
V1_POSE = b.pose_at
V1_LABEL = b.source_label
V1_RENDER = b.render
OUT = b.OUT/'S09Replacement'
WORK = b.WORK/'S09Replacement'
OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)
S09 = ('S09', 44, 62, 'Pull, inverted spiral and flip away', 'Meshy hang + breakdance',
       0, 0, 'hand -> leg hold -> release', 'Compact inversion -> thigh/calf hold -> 2.5 descending turns -> free flip.')
SECTIONS = V1_SECTIONS[:8]+[S09]+[
    (s[0], s[1]+8, s[2]+8, *s[3:]) for s in V1_SECTIONS[9:]]
hang = b.GLBPose(b.glb_dir/'meshy_hangs.glb', 'Upside_Down_Rope_Hang')
exit_clip = b.GLBPose(b.glb_dir/'meshy_hangs.glb', 'Rope_Hang_Backflip_to_Crouch')
breakdance = b.GLBPose(b.ROOT/'SourceAssets/MotionBoard/Meshy_Reference.glb', 'Breakdance_1990')
PARENTS = [-1, 0, 1, 2, 1, 4, 5, 6, 1, 8, 9, 10, 0, 12, 13, 14, 0, 16, 17, 18]
SWAP = [0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7, 16, 17, 18, 19, 12, 13, 14, 15]


@functools.lru_cache(maxsize=4096)
def original(t):
    current = b.SECTIONS
    b.SECTIONS = V1_SECTIONS
    try:
        return V1_POSE(t)[0]
    finally:
        b.SECTIONS = current


def unit(v):
    return v/max(np.linalg.norm(v), 1e-10)


def blend_pose(a, c, f):
    """Planning bone directions blend without shrinking limbs to zero."""
    f = float(np.clip(f, 0, 1))
    result = np.zeros_like(a)
    result[0] = a[0]*(1-f)+c[0]*f
    for i, parent in enumerate(PARENTS[1:], 1):
        av, cv = a[i]-a[parent], c[i]-c[parent]
        avn, cvn = unit(av), unit(cv)
        dot = float(np.clip(np.dot(avn, cvn), -1, 1))
        angle = math.acos(dot)
        if dot < -.999:
            tangent = unit(np.cross(avn, [0, 0, 1]))
            if np.linalg.norm(tangent) < .5:
                tangent = unit(np.cross(avn, [0, 1, 0]))
            direction = avn*math.cos(math.pi*f)+tangent*math.sin(math.pi*f)
        elif angle < 1e-6:
            direction = avn
        else:
            direction = (avn*math.sin((1-f)*angle)+cvn*math.sin(f*angle))/math.sin(angle)
        length = np.linalg.norm(av)*(1-f)+np.linalg.norm(cv)*f
        result[i] = result[parent]+direction*length
    return result


ENTRY = original(44).copy()
LENGTHS = np.array([0.0]+[float(np.linalg.norm(ENTRY[i]-ENTRY[parent]))
                        for i, parent in enumerate(PARENTS[1:], 1)])


def fixed_proportions(p):
    """Retain directions/root, rebuilding the unchanged S08 proxy proportions.

    This does not edit a character mesh or source rig. The CPU stick figure
    must not stretch while blending poses from different source skeletons.
    """
    result = np.zeros_like(p)
    result[0] = p[0]
    for i, parent in enumerate(PARENTS[1:], 1):
        direction = p[i]-p[parent]
        if np.linalg.norm(direction) < 1e-8:
            raise ValueError(f'Collapsed planning direction at joint {i}')
        result[i] = result[parent]+unit(direction)*LENGTHS[i]
    return result


def source_pose(p):
    return fixed_proportions(p-p[0])


def continuation(t):
    return fixed_proportions(original(t-8))


HAND = ENTRY[6].copy()
PHASE = sum((12 if s[7] in ('free', 'approach') else 22)*max(0, min(44, s[2])-s[1]) for s in V1_SECTIONS)
BD_AXIS0 = breakdance.sample(0)[16]-breakdance.sample(0)[12]
BD_ANGLE0 = math.degrees(math.atan2(BD_AXIS0[1], BD_AXIS0[0]))


def crease(p):
    # Show the nearest proposed support surface, not an arbitrary marker
    # declared to be a successful grip. Actual skin is absent from this proxy.
    choices = []
    for a, c, radius in [(12, 13, .09), (13, 14, .06)]:
        d = p[c]-p[a]
        f = np.clip(-float(p[a,:2]@d[:2])/max(float(d[:2]@d[:2]), 1e-12), 0, 1)
        point = p[a]+f*d
        surface = point-unit(point*[1, 1, 0])*radius
        choices.append((float(np.linalg.norm(surface[:2])), surface))
    return min(choices, key=lambda x: x[0])[1]


def pull_donor(t):
    u = np.clip((t-44)/3.5, 0, 1)
    p = source_pose(hang.sample(.533333+.566667*u))
    # Source pull raises the right arm. Mirror the donor to continue S08's
    # existing LEFT support; no hidden wrist switch at the boundary.
    p = fixed_proportions(p[SWAP]*[-1, 1, 1])
    p = p @ b.rotation(0, 0, PHASE+35*u).T
    p += HAND-p[6]
    return p+HAND-p[6]


def entry_continuation(t):
    if t <= 44:
        return original(t)
    velocity = (ENTRY-original(43.999))/.001
    return ENTRY+velocity*(t-44)


def pull_source(t):
    if t < 44.85:
        return bridge(entry_continuation, pull_donor, 44, 44.85, t)
    return pull_donor(t)


def pull(t):
    return pole_entry_contact.place(pull_source(t))


PULL_END = pole_entry_contact.place(pull_donor(47.5))
KNEE_HEIGHT = float(crease(PULL_END)[2])


def breakdance_pose(source_time):
    raw = breakdance.sample(source_time)
    axis = raw[16]-raw[12]
    source_yaw = math.degrees(math.atan2(axis[1], axis[0]))-BD_ANGLE0
    # Remove the donor's own 360-degree axial turn before authoring stage
    # rotation. Keep its knee, torso and arm articulation, not double-spin it.
    return source_pose(raw) @ b.rotation(0, 0, -source_yaw).T


def breakdance_loop(source_time):
    phase = source_time % .5
    # The donor meets in position but not velocity. Smooth just 0.025 source
    # seconds either side of its loop seam, retaining fixed segment lengths.
    if phase > .475 or phase < .025:
        unwrapped = phase if phase > .475 else phase+.5
        return bridge(breakdance_pose, lambda x: breakdance_pose(x-.5),
                      .475, .525, unwrapped)
    return breakdance_pose(phase)


@functools.lru_cache(maxsize=1)
def contact_recipe():
    result = sliding_contact.fit(breakdance_loop)
    if not result['feasible']:
        raise ValueError(result['reason'])
    return result


def descending_shape(t):
    u = np.clip((t-49.5)/10, 0, 1)
    source_time = u*2.5*.5
    p = breakdance_loop(source_time)
    offset = sliding_contact.evaluate(contact_recipe()['coefficients'], source_time)
    p[:,:2] -= offset
    yaw = PHASE+35+900*u
    # The pole can shift along the folded calf/upper thigh. Rotate the body
    # around the pole with that small smooth relative adjustment; preserve
    # the original limb directions and descend at a constant vertical speed.
    p = p @ b.rotation(0, 0, yaw).T
    return p+[0, 0, KNEE_HEIGHT-breakdance_loop(0)[13,2]-.95*u]


def transfer_block(t):
    u = np.clip((t-47.5)/2, 0, 1)
    target = descending_shape(49.5)
    result = blend_pose(PULL_END, target, b.smooth(u))
    # Keep hand support early; hand releases as knee contact becomes the load
    # reference. The marker reaches its target before the long descent.
    if u < .35:
        result += (PULL_END[6]-result[6])*(1-b.smooth(u/.35))
    return result


def release_block(t):
    u = np.clip((t-59.5)/2.5, 0, 1)
    held = descending_shape(59.5)
    raw = source_pose(exit_clip.sample(.9+.4*u))
    # New donor contributes inverted-to-open airborne exit, without landing.
    raw = raw @ b.rotation(0, 0, PHASE+935+110*u).T
    theta = math.radians(PHASE+935+110*u)
    radial = np.array([math.cos(theta), math.sin(theta), 0])
    center = held[0]+radial*(.7*b.smooth(u))+[0, 0, .18*math.sin(math.pi*u)]
    target = raw+center
    return blend_pose(held, target, b.smooth(u))


def derivative(fn, t, step=.0005):
    return (fn(t+step)-fn(t-step))/(2*step)


def hermite(a, c, va, vc, u, duration):
    """Position and tangent continuity for the CPU timing sketch only."""
    return ((2*u**3-3*u**2+1)*a+(u**3-2*u**2+u)*duration*va+
            (-2*u**3+3*u**2)*c+(u**3-u**2)*duration*vc)


def bridge(fn0, fn1, start, end, t):
    # Use position tangents for travel and direction tangents for each limb;
    # rebuild the hierarchy at fixed lengths before displaying it. Direct
    # joint-position Hermite can shrink a forearm or stretch a thigh badly.
    return fixed_proportions(hermite(
        fn0(start), fn1(end), derivative(fn0, start), derivative(fn1, end),
        (t-start)/(end-start), end-start))


def descent_continuation(t):
    # A short tangent outside the descent window prevents clamped source time
    # from reporting a false half-speed endpoint derivative in the bridges.
    if t < 49.5:
        p = descending_shape(49.5)
        v = (descending_shape(49.501)-p)/.001
        return p+v*(t-49.5)
    if t > 59.5:
        p = descending_shape(59.5)
        v = (p-descending_shape(59.499))/.001
        return p+v*(t-59.5)
    return descending_shape(t)


def transfer(t):
    if t < 48:
        p = bridge(pull, transfer_block, 47, 48, t)
    else:
        p = bridge(transfer_block, descent_continuation, 48, 49.5, t)
    corrected = pole_transfer_contact.place_calibrated(p, t, pull(47))
    # The original near-extended wrist differs by a fraction of a millimetre
    # from the conservative reach cap. Fade that correction in with zero
    # endpoint tangents, not a small but instantaneous contact teleport.
    return blend_pose(p, corrected, b.smooth((t-47)/.2))


def release(t):
    if t < 60.4:
        return bridge(descent_continuation, release_block, 59.5, 60.4, t)
    return release_block(t)


@functools.lru_cache(maxsize=4096)
def unadjusted_pose_at(t):
    if t < 44:
        p = original(t)
        if t >= 43:
            # Prepare the approach in the final second of S08, preserving
            # that phrase's directions/proportions before the new pull.
            target = pole_entry_contact.place(p)
            p = blend_pose(p, target, b.smooth((t-43)/.75))
        return p, next(s for s in SECTIONS if s[1] <= t < s[2])
    if t < 47:
        return pull(t), S09
    if t < 49.5:
        return transfer(t), S09
    if t < 59.5:
        return descending_shape(t), S09
    if t < 61.2:
        return release(t), S09
    if t < 64:
        s = S09 if t < 62 else SECTIONS[9]
        # Blend a moving outgoing donor to a moving S10 pose; a frozen end
        # pose blended over two seconds would reintroduce the docking pause.
        return bridge(release, continuation, 61.2, 64, t), s
    p = continuation(t)
    s = next((s for s in SECTIONS if s[1] <= t < s[2]), SECTIONS[-1])
    return p, s


@functools.lru_cache(maxsize=1)
def release_radius_nodes():
    def boundary(t):
        p = unadjusted_pose_at(t)[0][0]
        v = derivative(lambda x: unadjusted_pose_at(x)[0], t)[0]
        r = float(np.linalg.norm(p[:2]))
        return t, r, float(p[:2]@v[:2]/r)
    return [boundary(59.5), (60.4, .92, .10), (61.2, 1.02, .06),
            (63.5, 1.15, .05), boundary(64)]


def pose_at(t):
    p, section = unadjusted_pose_at(t)
    if 59.5 < t < 64:
        # Continuous outward travel replaces rejected clearance bumps that
        # moved away, recoiled toward the pole, then departed a second time.
        # This changes only whole-body translation, never limb articulation.
        for (a, ra, va), (c, rc, vc) in zip(release_radius_nodes(), release_radius_nodes()[1:]):
            if a <= t <= c:
                radius = hermite(ra, rc, va, vc, (t-a)/(c-a), c-a)
                direction = unit(p[0]*[1, 1, 0])
                p = p+direction*(radius-np.linalg.norm(p[0,:2]))
                break
    return p, section


def source_label(s, t):
    if s[0] != 'S09':
        if 62 <= t < 64:
            return 'Meshy exit + original S10 sideflip'
        return V1_LABEL(V1_SECTIONS[int(s[0][1:])-1], t-8 if t >= 62 else t)
    if t < 47.5:
        return 'new Meshy Hang .533-1.10s / mirrored'
    if t < 49.5:
        return 'Hang -> prior Meshy Breakdance_1990'
    if t < 59.5:
        return 'Breakdance / donor turn removed'
    return 'new Meshy Rope Backflip .90-1.30s'


def render(t, index):
    im, p, s = V1_RENDER(t, index)
    if 44 <= t < 62:
        draw = ImageDraw.Draw(im)
        beat = 'a' if t < 47.5 else ('b' if t < 49.5 else ('c' if t < 59.5 else 'd'))
        draw.text((710, 582), f'S09{beat} / replacement beat', font=b.font(16), fill='#ffda72')
    if 47.5 <= t < 59.5:
        draw = ImageDraw.Draw(im)
        marker = crease(p)
        for side in [False, True]:
            xy = b.view_points(np.array([marker]), side)[0][0]
            x, y = xy
            draw.ellipse((x-6, y-6, x+6, y+6), outline='#ffda72', width=2)
        if t >= 49.5:
            draw.text((32, 582), f'Descent: {(t-49.5)/4:.2f} / 2.50 turns', font=b.font(16), fill='#ffda72')
    return im, p, s


def configure():
    b.OUT, b.WORK, b.SECTIONS, b.DURATION = OUT, WORK, SECTIONS, 88
    b.pose_at, b.source_label, b.render = pose_at, source_label, render


if __name__ == '__main__':
    configure()
    b.build()
    path = OUT/'Review.html'
    page = path.read_text(encoding='utf-8').replace('Current-state audit and written plan', 'Written plan and S09 changes')
    page = page.replace('../../docs/', '../../../docs/').replace('../DanceRefinement_', '../../DanceRefinement_')
    page = page.replace('<h1>Full performance study', '<p><a href="../Review.html">Compare previous 80-second study</a></p><h1>Full performance study')
    page = page.replace('Finger contact, full-rate transitions,', 'S09 now proposes a pull into inversion, a folded-leg hold with limited contact movement, 2.5 descending turns and a flip out. The yellow marker indicates the nearest thigh/calf proxy surface. Actual skin clearance is not established. Finger contact, full-rate transitions,')
    path.write_text(page, encoding='utf-8')
    changes = {'version':3, 'seconds':88, 'previousSeconds':80, 'unchangedBefore':43,
               'newSources': ['meshy_hangs.glb', 'Meshy_Reference.glb'],
               'beats':[{'id':'S09a','start':44,'end':47.5}, {'id':'S09b','start':47.5,'end':49.5},
                        {'id':'S09c','start':49.5,'end':59.5,'turns':2.5,'descentMetres':.95},
                        {'id':'S09d','start':59.5,'end':62}],
               'modifications':['Mirror pull source for existing left support',
                                'Prepare whole-body placement in final S08 second; retain incoming velocity',
                                '83mm wrist stand-off and length-preserving source-plane arm IK for pull',
                                'Clearance corridor and sliding hand-to-leg transfer; release at48.90s',
                                'Outward spherical finger arc avoids near-opposite direction cancellation',
                                'Pelvis/root alignment replaces raw donor travel',
                                'Remove Breakdance donor yaw before stage turns',
                                'Original donor leg directions; no forced knee widening',
                                'Fixed S08 proxy segment lengths throughout new motion',
                                'Smooth bounded pole-relative movement along thigh/calf proxy surfaces',
                                'Periodic source seam smoothing over .025s each side',
                                'Root/direction tangent bridges at fixed lengths; CPU arm proxy only',
                                'Monotonic outward release replaces rejected outward-then-inward clearance bumps'],
               'scope':'CPU proxy only. Joint limits, skin, actual surface contact and continuous dynamics are unverified.'}
    (OUT/'S09Changes.json').write_text(json.dumps(changes,indent=2))
    (OUT/'ContactPlacement.json').write_text(json.dumps(contact_recipe(), indent=2))
    receipt_path = OUT/'Receipt.json'
    receipt = json.loads(receipt_path.read_text())
    receipt['candidateScriptSha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt['contactScriptSha256'] = hashlib.sha256(Path(sliding_contact.__file__).read_bytes()).hexdigest()
    receipt['entryScriptSha256'] = hashlib.sha256(Path(pole_entry_contact.__file__).read_bytes()).hexdigest()
    receipt['transferScriptSha256'] = hashlib.sha256(Path(pole_transfer_contact.__file__).read_bytes()).hexdigest()
    receipt['proxyPoseSamplesSha256'] = hashlib.sha256((OUT/'ProxyPoseSamples.npz').read_bytes()).hexdigest()
    receipt['fixedProxySegmentLengthsMetres'] = LENGTHS.tolist()
    receipt_path.write_text(json.dumps(receipt, indent=2))
