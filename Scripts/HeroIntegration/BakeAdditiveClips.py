"""Bake additive source clips to full poses for the game's single-node animation player."""
import hashlib
import json
import shutil
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/HeroIntegration_20261020'
assert '-SSBakeHeroAdditives' in u.SystemLibrary.get_command_line().split()
P = u.AnimPoseExtensions
REPORT = []
for key in ['EX7', 'Green', 'Blue', 'Cloth']:
    folder = '/Game/SpaceSurvival/Licensed/PlayableHeroes_20261020/' + key
    mesh = u.load_asset(folder + '/SK_' + key)
    bones = P.get_bone_names(P.get_reference_pose(mesh.skeleton))
    options = u.AnimPoseEvaluationOptions()
    options.set_editor_property('retrieve_additive_as_full_pose', True)
    options.set_editor_property('optional_skeletal_mesh', mesh)
    for name in ['Idle', 'Walk', 'Jog', 'Run', 'JumpStart', 'JumpAir', 'JumpLand', 'Pilot']:
        clip = u.load_asset(folder + '/A_' + name)
        if clip.get_editor_property('additive_anim_type') == u.AdditiveAnimationType.AAT_NONE:
            continue
        frames = round(clip.sequence_length * 30)
        poses = [P.get_anim_pose_at_time(clip, i / 30., options) for i in range(frames + 1)]
        tracks = {str(b): [P.get_bone_pose(p, b, u.AnimPoseSpaces.LOCAL) for p in poses] for b in bones}
        disk = ROOT / 'Content' / Path((folder + '/A_' + name).removeprefix('/Game/')).with_suffix('.uasset')
        digest = hashlib.sha256(disk.read_bytes()).hexdigest()
        backup = Path('D:/SpaceSurvival_AssetArchive/HeroUnreal_20261020/BeforeAdditiveBake') / key / (name + '_' + digest[:16] + '.uasset')
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(disk, backup)
        assert hashlib.sha256(backup.read_bytes()).hexdigest() == digest
        clip.set_editor_property('additive_anim_type', u.AdditiveAnimationType.AAT_NONE)
        clip.set_editor_property('force_root_lock', False)
        clip.set_editor_property('enable_root_motion', False)
        c = clip.get_editor_property('controller')
        c.open_bracket('Bake evaluated full pose for standalone playback', False)
        c.set_frame_rate(u.FrameRate(30, 1), False)
        c.set_number_of_frames(u.FrameNumber(frames), False)
        for bone, keys in tracks.items():
            c.add_bone_curve(bone, False)
            assert c.set_bone_track_keys(bone, [k.translation for k in keys], [k.rotation for k in keys], [k.scale3d for k in keys], False)
        c.close_bracket(False)
        assert u.EditorAssetLibrary.save_loaded_asset(clip, False)
        REPORT.append({'hero': key, 'clip': name, 'before_sha256': digest, 'after_sha256': hashlib.sha256(disk.read_bytes()).hexdigest()})
        print('HERO_ADDITIVE_BAKED', key, name, flush=True)
(OUT / 'AdditiveBakes.json').write_text(json.dumps(REPORT, indent=2))
