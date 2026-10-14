"""Adopt the owner's staged 178 cm squirrel without reimporting or altering art.

Run preflight in the owned editor with PIE stopped, then apply with the current
DA_Phase1 SHA and a private backup directory. Save only after native review.
The staged delivery and its derivation receipts remain private licensed inputs.
"""
import hashlib
import json
from pathlib import Path

BASE = '/Game/SpaceSurvival/Licensed/HeroReplacement178'
OLD = '/Game/SpaceSurvival/Licensed/HeroReplacement/Final/SK_SquirrelHeroReplacement.SK_SquirrelHeroReplacement'
DATA = '/Game/SpaceSurvival/Data/DA_Phase1'
CLIPS = {'Idle':'idle_clip_path', 'Walk':'walk_clip_path', 'Jog':'jog_clip_path',
         'Run':'run_clip_path', 'Pilot':'pilot_clip_path', 'JumpStart':'jump_start_clip_path',
         'JumpAir':'jump_air_clip_path', 'JumpLand':'jump_land_clip_path'}


def preflight(u):
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world(), 'Stop PIE first'
    root = Path(u.Paths.project_dir()).resolve()
    copied = json.loads((root / '.agent/local/StationRefinement/Crew52/Hero178Copied.json').read_text('utf-8-sig'))
    for row in copied['Files']:
        file = root / 'Content/SpaceSurvival/Licensed/HeroReplacement178' / row['Path']
        assert hashlib.sha256(file.read_bytes()).hexdigest() == row['Sha256'], str(file)
    mesh = u.load_asset(BASE + '/SK_SquirrelHero178_RedStreaks')
    assert mesh and abs(mesh.get_bounds().box_extent.z * 2. - 178.) < .01
    assert len(mesh.materials) == 3 and all(m.material_interface for m in mesh.materials)
    clips = {name:u.load_asset(BASE + '/A_' + name) for name in CLIPS}
    assert all(c and c.get_editor_property('skeleton') == mesh.skeleton for c in clips.values())
    data = u.load_asset(DATA)
    rows = list(data.heroes)
    indices = [i for i, h in enumerate(rows) if str(h.id) == 'Squirrel']
    assert len(indices) == 1
    return root, data, rows, indices[0], mesh, clips


def apply(u, expected_sha256, backup_directory):
    root, data, rows, index, mesh, clips = preflight(u)
    file = root / 'Content/SpaceSurvival/Data/DA_Phase1.uasset'
    assert hashlib.sha256(file.read_bytes()).hexdigest() == expected_sha256, 'Tuning changed'
    assert not u.EditorLoadingAndSavingUtils.get_dirty_content_packages(), 'Preserve dirty assets'
    hero = rows[index]
    assert hero.mesh_path == OLD, 'Do not replace another selection or apply twice'
    before = hero.export_text()
    backup = Path(backup_directory).resolve()
    assert backup.is_relative_to(root / '.agent/local') and not backup.exists()
    backup.mkdir(parents=True)
    (backup / 'DA_Phase1.before.uasset').write_bytes(file.read_bytes())
    (backup / 'Squirrel.before.txt').write_text(before, encoding='utf-8')
    measurements = json.loads((root / '.agent/local/CharacterAssets/HeroSquirrel_20261008/Integration/derive178.json').read_text('utf-8'))
    envelopes = json.loads((root / '.agent/local/CharacterAssets/HeroSquirrel_20261008/Delivery_RedStreaks/tail_rest_envelopes.json').read_text('utf-8'))
    assert len(envelopes['envelopes']) == 7 and all(measurements['clips'][n]['skeleton_ok'] for n in CLIPS)
    hero.set_editor_property('mesh_path', mesh.get_path_name())
    for name, field in CLIPS.items():
        hero.set_editor_property(field, clips[name].get_path_name())
    hero.set_editor_property('fit_height', 178.)
    hero.set_editor_property('mesh_scale', 1.)
    hero.set_editor_property('sole_offset', 0.)
    hero.set_editor_property('pilot_mount_offset', u.Vector(*measurements['pilot_mount_offset']))
    for name in ('Walk','Jog','Run'):
        hero.set_editor_property(name.lower() + '_speed', measurements['clips'][name]['speed_new'])
    boxes = {}
    for entry in envelopes['envelopes']:
        box = u.Box()
        box.set_editor_property('min', u.Vector(*entry['min']))
        box.set_editor_property('max', u.Vector(*entry['max']))
        box.set_editor_property('is_valid', True)
        boxes[u.Name(entry['bone'])] = box
    hero.set_editor_property('tail_floor_envelopes', boxes)
    rows[index] = hero
    data.modify()
    data.set_editor_property('heroes', rows)
    assert data.heroes[index].mesh_path == mesh.get_path_name()
    (backup / 'Squirrel.after.txt').write_text(data.heroes[index].export_text(), encoding='utf-8')
    return {'mesh':mesh.get_path_name(), 'height_cm':178., 'clip_count':len(clips),
            'tail_envelopes':len(boxes), 'backup':str(backup), 'saved':False,
            'previous_sha256':expected_sha256}
