"""Read back the sparse, held Joy patch. Numerical checks are not visual approval."""
from copy import deepcopy
from pathlib import Path
import argparse
import hashlib
import json
import math
import numpy as np
from JoyPourFrameRepair import (
    NATIVE_SHA256, ORIGINAL_SHA256, angle, fk, inv, original_frame, pose,
    qr, read, unit,
)

PATCH_SHA256 = 'be9e2d6a88c28d84b6865f64defd34ee81e5d468e8d5a34b1c59895898e32eb4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-poses', type=Path, required=True)
    parser.add_argument('--original-poses', type=Path, required=True)
    parser.add_argument('--patch', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Report already exists; choose a new private report path')
    assert sha(args.native_poses) == NATIVE_SHA256
    assert sha(args.original_poses) == ORIGINAL_SHA256
    assert sha(args.patch) == PATCH_SHA256
    inputs = read(args.native_poses)['joy']
    base = dict(inputs['poses']['Pour'], names=inputs['names'], parents=inputs['parents'])
    patch = read(args.patch)
    assert patch['base_inputs_sha256'] == NATIVE_SHA256
    expected = ['CC_Base_'+s+'_'+part for s in ['L','R'] for part in ['Upperarm','Forearm','Hand']]
    assert set(patch['tracks']) == set(expected)
    assert len(base['frames']) == 381 and len(base['names']) == 101
    candidate = deepcopy(base)
    for name, values in patch['tracks'].items():
        k = base['names'].index(name)
        assert len(values) == len(base['frames'])
        for dst, src, v in zip(candidate['frames'], base['frames'], values):
            assert src[k][0] == v[0] and src[k][2] == v[2]
            dst[k] = v
    protected = [i for i,n in enumerate(base['names']) if n not in expected]
    assert all(all(a[i] == b[i] for i in protected) for a,b in zip(base['frames'],candidate['frames']))
    assert base['frames'][0] == candidate['frames'][0]
    assert base['frames'][-1] == candidate['frames'][-1]
    p0,q0,ids = fk(base)
    p1,q1,_ = fk(candidate)
    left,right = [ids['CC_Base_'+s+'_Hand'] for s in ['L','R']]
    relative_error = float(np.linalg.norm((p1[:,right]-p1[:,left])-(p0[:,right]-p0[:,left]),axis=1).max())
    orientation_error = max(angle(a,b) for k in [left,right] for a,b in zip(q0[:,k],q1[:,k]))
    assert relative_error < 1e-6 and orientation_error < 1e-4
    sources = read(args.original_poses)
    raw, standing = sources['A_Joy_Bar_PourAndServe'], sources['A_Joy_PourStanding']
    source = pose(standing, original_frame(standing, raw, 60))
    directions = {}
    for side in ['L','R']:
        names = ['CC_Base_'+side+'_'+part for part in ['Upperarm','Forearm','Hand']]
        a,b,c = [source[n][0] for n in names]
        calibration = qr(inv(source[names[0]][1]),unit(np.cross(b-a,c-b)))
        directions[side] = {}
        for label,p,q in [('baseline',p0,q0),('candidate',p1,q1)]:
            a,b,c = [ids[n] for n in names]
            values = []
            for i in range(60,241):
                normal = unit(np.cross(p[i,b]-p[i,a],p[i,c]-p[i,b]))
                local = unit(qr(inv(q[i,a]),normal))
                values.append(math.degrees(math.acos(float(np.clip(np.dot(local,calibration),-1,1)))))
            directions[side][label] = max(values)
    assert all(directions[s]['candidate'] < 1e-4 for s in ['L','R'])
    steps = {}
    event_frames = [27,82,115,132,170,0,379]
    for label,row in [('baseline',base),('candidate',candidate)]:
        steps[label] = {}
        for name in expected:
            k = ids[name]
            values = [angle(a[k][1],b[k][1]) for a,b in zip(row['frames'],row['frames'][1:])]
            steps[label][name] = dict(max_degrees=max(values),time_seconds=int(np.argmax(values))/30,
                specified_steps={str(i/30):values[i] for i in event_frames})
    assert sha(args.native_poses) == NATIVE_SHA256 and sha(args.original_poses) == ORIGINAL_SHA256
    receipt = dict(status='HELD: numerical verification only',patch_sha256=PATCH_SHA256,
        native_inputs_sha256=NATIVE_SHA256,original_inputs_sha256=ORIGINAL_SHA256,
        frames=381,frame_rate=30,changed_rotation_tracks=expected,protected_local_tracks=len(protected),
        local_translation_scale_unchanged=True,endpoints_exact=True,
        hand_pair_relative_position_max_error_cm=relative_error,
        hand_world_orientation_max_error_degrees=orientation_error,
        calibrated_hinge_direction_max_deviation_degrees=directions,local_rotation_steps=steps,
        imported=False,rendered=False,visual_acceptance=False,current_runtime_verified=False,
        limitations=['Skin and helper-bone response needs current Joy visual review',
                    'CounterCandidateV8 delivery is separate and unpatched',
                    'Body, jacket, actual counter and prop clearance remain unverified'])
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x', encoding='utf-8') as report:
        report.write(json.dumps(receipt,indent=2))
    print(json.dumps(dict(status=receipt['status'],frames=381,protected_tracks=len(protected),
        hand_relative_error_cm=relative_error,hand_orientation_error_degrees=orientation_error,
        report=str(args.report)),indent=2))


if __name__ == '__main__':
    main()
