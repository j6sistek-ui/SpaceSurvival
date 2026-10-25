"""Correct only derived jump-start/landing root curves using actual CPU-skinned boot contact."""
import hashlib
import json
import shutil
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/HeroIntegration_20261020'
assert '-SSCorrectHeroFeet' in u.SystemLibrary.get_command_line().split()
BASE = '/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020'
ARCHIVE = Path('D:/SpaceSurvival_AssetArchive/HeroUnreal_20261020/BeforeFootContact')
REPORT = {'heroes': {}, 'geometry_edited': False}
for key in ['EX7', 'Green', 'Blue', 'Cloth']:
    folder = BASE + '/' + key
    mesh = u.load_asset(folder + '/SK_' + key)
    REPORT['heroes'][key] = {}
    for name in ['JumpStart', 'JumpLand']:
        clip = u.load_asset(folder + '/A_' + name)
        # Template clips carry forced root locking; that would discard the measured curve below.
        clip.set_editor_property('force_root_lock', False)
        clip.set_editor_property('enable_root_motion', False)
        frames = round(clip.sequence_length * 30)
        measured = json.loads(u.SSPlayableHeroTools.measure_motion(mesh, clip, frames + 1))
        assert measured['success'], measured
        corrections = [-row['sole_z_cm'] if name == 'JumpLand' else max(0., -row['sole_z_cm']) for row in measured['frames']]
        transforms = [u.AnimationLibrary.get_bone_pose_for_time(clip, 'root', row['seconds'], False) for row in measured['frames']]
        original_file = ROOT / 'Content' / Path((folder + '/A_' + name).removeprefix('/Game/')).with_suffix('.uasset')
        digest = hashlib.sha256(original_file.read_bytes()).hexdigest()
        backup = ARCHIVE / key / (name + '_' + digest[:16] + '.uasset')
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(original_file, backup)
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == digest
        controller = clip.get_editor_property('controller')
        controller.open_bracket('Measured boot contact for derived playable hero', False)
        controller.set_frame_rate(u.FrameRate(30, 1), False)
        controller.set_number_of_frames(u.FrameNumber(frames), False)
        assert controller.set_bone_track_keys('root', [t.translation + u.Vector(0, 0, dz) for t, dz in zip(transforms, corrections)],
                                              [t.rotation for t in transforms], [t.scale3d for t in transforms], False)
        controller.close_bracket(False)
        assert u.EditorAssetLibrary.save_loaded_asset(clip, False)
        after = json.loads(u.SSPlayableHeroTools.measure_motion(mesh, clip, frames + 1))
        assert after['success']
        assert min(row['sole_z_cm'] for row in after['frames']) > -.05, (key, name, after)
        REPORT['heroes'][key][name] = {'maximum_root_correction_cm': max(map(abs, corrections)), 'before_sha256': digest,
                                      'after_sha256': hashlib.sha256(original_file.read_bytes()).hexdigest(), 'after': after}
    (OUT / 'GroundContact.json').write_text(json.dumps(REPORT, indent=2))
    print('HERO_GROUND_CONTACT', key, flush=True)
REPORT['success'] = True
(OUT / 'GroundContact.json').write_text(json.dumps(REPORT, indent=2))
