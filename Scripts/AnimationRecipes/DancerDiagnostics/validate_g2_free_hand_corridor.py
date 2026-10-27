"""Compare released-hand orientation policies without saving any Blender asset.

Run in hidden background Blender with --output NEW_DIRECTORY --calibration
the prior measured corridor Audit.json. Tests the restored G2 return only;
this is not whole-body collision or anatomy acceptance.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from g2_phrase_ik_control import ArmSurfaceScreen, source_return_left_corridor
from g2_source_phrase_control import SourcePhraseControl
from validate_g2_contact_recipe import geometry


def degrees(a, b):
    # abs(dot) avoids treating quaternion sign as a full revolution.
    first = np.asarray(a.to_quaternion(), dtype=np.float64)
    second = np.asarray(b.to_quaternion(), dtype=np.float64)
    dot = abs(float(np.dot(first, second) / (np.linalg.norm(first) * np.linalg.norm(second))))
    return math.degrees(2 * math.acos(min(1., dot)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    calibration = json.loads(args.calibration.read_text())
    assert calibration['unresolved'] == 0
    args.output.mkdir(parents=True, exist_ok=False)
    model = SourcePhraseControl()
    screen = ArmSurfaceScreen(model, geometry(model), 'l')
    arm = ('upperarm_l', 'lowerarm_l', 'hand_l')
    reports = {}
    for policy in ('source_world', 'source_local'):
        rows, previous, max_speed, max_source_speed, max_wrist = [], None, 0., 0., 0.
        outside_error = 0.
        for seconds in np.linspace(48.7875, 50.1125, 319):
            original, _, _ = model.pose(float(seconds))
            pose, metrics = source_return_left_corridor(
                model, original, float(seconds), calibration['residual_chest_m'], policy)
            _, _, _, pairs, pole = screen.sample(pose)
            wrist = degrees(original['lowerarm_l'].inverted() @ original['hand_l'],
                            pose['lowerarm_l'].inverted() @ pose['hand_l'])
            max_wrist = max(max_wrist, wrist)
            if previous:
                old, source = previous
                max_speed = max(max_speed, max(degrees(old[n], pose[n]) * 240 for n in arm))
                max_source_speed = max(max_source_speed, max(degrees(source[n], original[n]) * 240 for n in arm))
            previous = pose, original
            if not 48.8 < seconds < 50.1:
                outside_error = max(outside_error, max(float(np.abs(
                    np.asarray(pose[n]) - np.asarray(original[n])).max()) for n in model.names))
            rows.append({'seconds': float(seconds), 'body_pairs': len(pairs), 'pole': pole,
                         'wrist_local_difference_degrees': wrist, 'ik': metrics})
        assert outside_error == 0
        reports[policy] = {'rows': rows, 'flagged_samples': sum(bool(r['body_pairs'] or r['pole']) for r in rows),
                           'max_joint_speed_deg_s': max_speed, 'max_source_joint_speed_deg_s': max_source_speed,
                           'max_wrist_local_difference_deg': max_wrist, 'outside_matrix_error': outside_error}
        print('CORRIDOR_POLICY', policy, reports[policy]['flagged_samples'], max_speed, max_wrist, flush=True)
    model.assert_guards()
    result = {'sources': model.guards, 'calibration_sha256': hashlib.sha256(args.calibration.read_bytes()).hexdigest(),
              'controller_sha256': hashlib.sha256(Path(__file__).with_name('g2_phrase_ik_control.py').read_bytes()).hexdigest(),
              'sample_hz': 240, 'policies': reports,
              'scope': 'Left distal-arm/body/pole only. Upper-arm, hips, garments, full joint ranges, visual motion and native replay remain open.'}
    (args.output / 'Audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
