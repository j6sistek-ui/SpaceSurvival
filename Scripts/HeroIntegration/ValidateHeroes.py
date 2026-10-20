"""Read-only native render-skin, shader, clip, ground-contact and seat-fit measurements."""
import json
import math
import statistics
from pathlib import Path

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/HeroIntegration_20261020'
BASE = '/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020'
P = u.AnimPoseExtensions
OPTIONS = u.AnimPoseEvaluationOptions()
REPORT = {'heroes': {}, 'assets_edited': False}


def persist():
    (OUT / 'NativeValidation.json').write_text(json.dumps(REPORT, indent=2))


def bone(clip, name, time):
    pose = P.get_anim_pose_at_time(clip, time, OPTIONS)
    return P.get_bone_pose(pose, name, u.AnimPoseSpaces.WORLD).translation


data = u.load_asset('/Game/SpaceSurvival/Data/DA_Phase1')
old = next(row for row in data.heroes if str(row.id) == 'Squirrel')
old_mesh = u.load_asset(old.mesh_path)
old_pilot = u.load_asset(old.pilot_clip_path)
old_scale = old.fit_height / (old_mesh.get_bounds().box_extent.z * 2) if old.fit_height > 0 else old.mesh_scale
old_pelvis = bone(old_pilot, old.pelvis_bone, 0) * old_scale

for key in ['EX7', 'Green', 'Blue', 'Cloth']:
    folder = BASE + '/' + key
    mesh = u.load_asset(folder + '/SK_' + key)
    assert mesh and mesh.skeleton, key
    entry = {'mesh': mesh.get_path_name(), 'import': json.loads(u.SSPlayableHeroTools.inspect_mesh(mesh)), 'clips': {}}
    REPORT['heroes'][key] = entry
    persist()
    assert entry['import']['success'], entry['import']
    assert entry['import']['triangles'] <= 150000, entry['import']
    for name in ['Idle', 'Walk', 'Jog', 'Run', 'JumpStart', 'JumpAir', 'JumpLand', 'Pilot']:
        clip = u.load_asset(folder + '/A_' + name)
        assert isinstance(clip, u.AnimSequence) and clip.sequence_length > 0, (key, name)
        assert clip.get_editor_property('skeleton') == mesh.skeleton, (key, name)
        assert clip.get_editor_property('additive_anim_type') == u.AdditiveAnimationType.AAT_NONE, (key, name, 'Single-node playback requires a full pose')
        result = json.loads(u.SSPlayableHeroTools.measure_motion(mesh, clip, 25))
        entry['clips'][name] = result
        persist()
        assert result['success'], (key, name, result)
        assert all(math.isfinite(f['height_cm']) for f in result['frames'])
        if name in ['Idle', 'Walk', 'Jog', 'Run']:
            assert all(145 < f['height_cm'] < 225 for f in result['frames']), (key, name, 'Unexpected animated stature')
    entry['gaits'] = {}
    for name in ['Walk', 'Jog', 'Run']:
        clip = u.load_asset(folder + '/A_' + name)
        n = round(clip.sequence_length * 60)
        dt = clip.sequence_length / n
        samples = [[bone(clip, foot, i * dt) for foot in ['ball_l', 'ball_r']] for i in range(n + 1)]
        speeds = []
        for side in range(2):
            low = min(row[side].z for row in samples)
            for prev, curr in zip(samples, samples[1:]):
                if prev[side].z < low + 2 and curr[side].z < low + 2:
                    delta = curr[side] - prev[side]
                    distance = math.hypot(delta.x, delta.y)
                    if distance / dt > 5:
                        speeds.append(distance / dt)
        entry['gaits'][name] = {'contact_speed_cm_s': statistics.median(speeds) if speeds else None, 'samples': len(speeds)}
    pilot = u.load_asset(folder + '/A_Pilot')
    new_pelvis = bone(pilot, 'pelvis', 0)
    mount = u.MathLibrary.quat_rotate_vector(u.Rotator(yaw=-90).quaternion(), old_pelvis - new_pelvis) + old.pilot_mount_offset
    entry['pilot_mount_aligns_existing_seat_pelvis'] = [mount.x, mount.y, mount.z]
    entry['sole_range_cm'] = {n: [min(f['sole_z_cm'] for f in r['frames']), max(f['sole_z_cm'] for f in r['frames'])] for n, r in entry['clips'].items()}
    persist()
    print('HEROVALIDATE|', key, entry['import'], 'gaits', entry['gaits'], 'soles', entry['sole_range_cm'], flush=True)
REPORT['success'] = True
persist()
print('ALL_HERO_NATIVE_CHECKS_PASS', flush=True)
