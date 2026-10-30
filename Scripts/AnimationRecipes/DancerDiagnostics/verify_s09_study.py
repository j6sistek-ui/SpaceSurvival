"""Audit the private CPU study; this is not a native rig acceptance test.

Run after build_s09_replacement.py. Reports retained comparison problems
separately from the new S09 route, and binds checks to source/output hashes.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

import build_s09_replacement as m


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def segment_gap(a, c, radius):
    direction = c-a
    fraction = np.clip(-float(a@direction)/max(float(direction@direction), 1e-12), 0, 1)
    return float(np.linalg.norm(a+fraction*direction)-radius-.035)


def capsule_gaps(p):
    return [segment_gap(p[a,:2], p[c,:2], radius)
            for a, c, radius in m.sliding_contact.CAPSULES]


def torso_gap(p):
    # Project the convex hull of the renderer's flat torso onto pole XY.
    # A separate capsule covers its central thickness; neither is actual skin.
    points = sorted(set(map(tuple, p[[4, 8, 16, 12],:2])))
    def cross(a, c, d):
        return (c[0]-a[0])*(d[1]-a[1])-(c[1]-a[1])*(d[0]-a[0])
    lower, upper = [], []
    for seq, hull in [(points, lower), (points[::-1], upper)]:
        for point in seq:
            while len(hull) >= 2 and cross(hull[-2], hull[-1], point) <= 0:
                hull.pop()
            hull.append(point)
    hull = lower[:-1]+upper[:-1]
    if len(hull) < 2:
        return float(np.linalg.norm(points[0])-.035)
    pairs = list(zip(hull, hull[1:]+hull[:1]))
    distance = min(segment_gap(np.array(a), np.array(c), 0)+.035 for a, c in pairs)
    inside = len(hull) >= 3 and all(cross(a, c, (0, 0)) >= 0 for a, c in pairs)
    return (-distance if inside else distance)-.035


def inspect_window(start, end, hz=120):
    times = np.linspace(start, end, round((end-start)*hz)+1)
    positions = np.array([m.pose_at(float(t))[0] for t in times])
    gaps = np.array([min(min(capsule_gaps(p)), torso_gap(p)) for p in positions])
    lengths = np.array([[np.linalg.norm(p[j]-p[parent])
                         for j, parent in enumerate(m.PARENTS[1:], 1)] for p in positions])
    speeds = np.linalg.norm(np.diff(positions, axis=0)*hz, axis=2)
    finger = positions[:,7]-positions[:,6]
    finger /= np.linalg.norm(finger, axis=1)[:,None]
    angular = np.arccos(np.clip(np.sum(finger[1:]*finger[:-1], axis=1), -1, 1))*hz
    worst = int(np.argmin(gaps))
    return {
        'start': start, 'end': end, 'hz': hz, 'samples': len(times),
        'minProxyGapM': float(gaps[worst]), 'worstTime': float(times[worst]),
        'overlapSampleCount': int(np.count_nonzero(gaps < -1e-6)),
        'maxLengthErrorM': float(np.max(np.abs(lengths-m.LENGTHS[1:]))),
        'maxJointSpeedMps': float(speeds.max()),
        'maxLeftFingerDirectionRadPerSecond': float(angular.max()),
        'maxRadiusM': float(np.linalg.norm(positions[:,:,:2], axis=2).max()),
        'zRangeM': [float(positions[:,:,2].min()), float(positions[:,:,2].max())],
    }, positions


def main():
    m.configure()
    out = m.OUT
    failures = []
    receipt = json.loads((out/'Receipt.json').read_text())
    sources = {path: digest(path) == expected for path, expected in receipt['sources'].items()}
    checks = {
        'candidateScriptSha256': Path(m.__file__),
        'contactScriptSha256': Path(m.sliding_contact.__file__),
        'entryScriptSha256': Path(m.pole_entry_contact.__file__),
        'transferScriptSha256': Path(m.pole_transfer_contact.__file__),
        'proxyPoseSamplesSha256': out/'ProxyPoseSamples.npz',
        'movieSha256': out/'FullPerformance_2fps.mp4',
        'scriptSha256': Path(m.b.__file__), 'planSha256': m.b.PLAN,
    }
    hashes = {key: digest(path) == receipt.get(key) for key, path in checks.items()}
    if not all(sources.values()) or not all(hashes.values()):
        failures.append('Source or output receipt mismatch; rebuild before making quality claims.')
    data = np.load(out/'ProxyPoseSamples.npz')
    old = np.load(out.parent/'ProxyPoseSamples.npz')
    shape_ok = data['positions'].shape == (176, 20, 3) and np.isfinite(data['positions']).all()
    prefix_ok = np.array_equal(data['positions'][:86], old['positions'][:86])
    if not shape_ok or not prefix_ok:
        failures.append('Unexpected sample shape or change before the S08 approach preparation at43s.')
    sampled = np.array([m.pose_at(float(t))[0] for t in data['times']])
    matches = bool(np.allclose(sampled, data['positions'], rtol=0, atol=1e-10))
    if not matches:
        failures.append('Saved poses do not represent the current source.')
    frames = []
    for side, rect in [(False, (20, 96, 668, 609)), (True, (688, 96, 1260, 609))]:
        xy = np.array([m.b.view_points(p, side)[0] for p in sampled])
        low, high = xy.min(axis=(0, 1)), xy.max(axis=(0, 1))
        framed = bool(low[0] > rect[0]+8 and high[0] < rect[2]-8 and
                      low[1] > rect[1]+8 and high[1] < rect[3]-8)
        if not framed:
            failures.append(f'Camera crops a proxy joint: side={side}')
        frames.append({'side': side, 'min': low.tolist(), 'max': high.tolist(), 'framed': framed})
    joins = []
    for t in [43, 43.75, 44, 44.85, 47, 47.2, 47.5, 48, 48.7, 48.9, 49, 49.5, 59.5, 60.4, 61.2, 62, 63.5, 64]:
        step = .0001
        a, p, c = [m.pose_at(t+x)[0] for x in [-step, 0, step]]
        jump = float(np.linalg.norm(p-a, axis=1).max())
        velocity = float(np.linalg.norm((c-p)/step-(p-a)/step, axis=1).max())
        if jump > .001 or velocity > .03:
            failures.append(f'New join discontinuity at{t}s: position={jump}, velocity={velocity}')
        joins.append({'time': t, 'stepDisplacementM': jump, 'velocityDifferenceMps': velocity})
    windows = []
    for a, c in [(43, 44), (44, 47), (47, 49.5), (49.5, 59.5), (59.5, 64)]:
        record, positions = inspect_window(a, c)
        record['inheritedComparisonWindow'] = a < 44
        if a >= 44 and (record['overlapSampleCount'] or record['maxLengthErrorM'] > 1e-8):
            failures.append(f'New route has a proxy overlap or proportion change at{a}–{c}s.')
        if a == 47 and record['maxLeftFingerDirectionRadPerSecond'] > 10:
            # Specific proposal regression alarm, not a human wrist ROM limit.
            # Near-opposite normalized blends previously caused a sharp snap.
            failures.append('Transfer finger direction exceeds the calibrated arc speed review bound.')
        if record['maxRadiusM'] > 2.8:
            failures.append(f'New route exceeds the2.8m planning ring at{a}–{c}s.')
        if a == 59.5:
            radius = np.linalg.norm(positions[:,0,:2], axis=1)
            record['maximumInwardStepM'] = float(max(0, -np.diff(radius).min()))
            if record['maximumInwardStepM'] > 1e-7:
                failures.append('Release recoils toward the pole.')
        windows.append(record)
    ffmpeg = 'C:/Program Files/Lian-Li/L-Connect 3/x64/ffmpeg.exe'
    decoded = subprocess.run([ffmpeg, '-hide_banner', '-nostdin', '-i',
        str(out/'FullPerformance_2fps.mp4'), '-f', 'null', '-'], capture_output=True, text=True)
    decode_ok = (decoded.returncode == 0 and 'Duration: 00:01:28.00' in decoded.stderr
                 and bool(re.search(r'frame=\s*176\b', decoded.stderr)))
    if not decode_ok:
        failures.append('Expected176 frames/88 seconds did not decode.')
    result = {'status': 'PASS_NEW_ROUTE_WITH_OPEN_COMPARISON' if not failures else 'NEEDS_WORK', 'failures': failures,
        'sourceHashes': sources, 'receiptHashes': hashes, 'frames': 176, 'seconds': 88, 'fps': 2,
        'decoded': decode_ok, 'before43SecondsUnchanged': prefix_ok, 'samplesMatchSource': matches,
        'viewBounds': frames, 'joins': joins, 'windows': windows,
        'scope': 'CPU proxy geometry/travel/provenance only. S01–S08 comparison remains unvalidated contact. No native skin, fingers, joint-limit, physical support, chamber, loop or owner acceptance claim.'}
    (out/'Verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({'status': result['status'], 'failures': failures, 'report': str(out/'Verification.json')}))
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
