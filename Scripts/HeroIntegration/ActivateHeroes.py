"""Prepend verified playable heroes to the real tuning roster, preserving all existing rows and tuning.

Default is a read-only plan. -SSActivatePlayableHeroes requires the unchanged plan, native validation,
and source package. It does not edit player profiles, maps, old heroes or Blender originals.
"""
import hashlib
import json
import shutil
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/HeroIntegration_20261020'
FILE = ROOT / 'Content/SpaceSurvival/Data/DA_Phase1.uasset'
APPLY = '-SSActivatePlayableHeroes' in u.SystemLibrary.get_command_line().split() and not globals().get('HERO_ACTIVATION_DRY_RUN', False)
data = u.load_asset('/Game/SpaceSurvival/Data/DA_Phase1')
validation_file = OUT / 'NativeValidation.json'
validation = json.loads(validation_file.read_text())
assert validation['success'] and len(validation['heroes']) == 4
ground = json.loads((OUT / 'GroundContact.json').read_text())
assert ground['success']
assert json.loads((OUT / 'ChaosBinding.json').read_text())['success']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain(value):
    if hasattr(value, 'export_text'):
        return value.export_text()
    if isinstance(value, u.Object):
        return value.get_path_name()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, 'items'):
        return {str(k): plain(v) for k, v in value.items()}
    if hasattr(value, '__iter__'):
        return [plain(v) for v in value]
    return str(value)


def other_tuning():
    result = {}
    for name in dir(data):
        if name.startswith('_') or name == 'heroes':
            continue
        try:
            value = data.get_editor_property(name)
        except Exception:
            continue
        result[name] = plain(value)
    return result


old = list(data.heroes)
defaults = u.new_object(u.SSPhase1Data).heroes
new_ids = ['EX7Hero', 'GreenHero', 'BlueHero', 'ClothHero']
incoming = []
for key, identifier in zip(['EX7', 'Green', 'Blue', 'Cloth'], new_ids):
    row = next(r for r in defaults if str(r.id) == identifier)
    for field, gait in [('walk_speed', 'Walk'), ('jog_speed', 'Jog'), ('run_speed', 'Run')]:
        row.set_editor_property(field, round(validation['heroes'][key]['gaits'][gait]['contact_speed_cm_s'], 1))
    row.set_editor_property('pilot_mount_offset', u.Vector(*validation['heroes'][key]['pilot_mount_aligns_existing_seat_pelvis']))
    assert u.load_asset(row.mesh_path), row.mesh_path
    incoming.append(row)
retained = [r for r in old if str(r.id) not in new_ids]
before_tuning = other_tuning()
record = {'applied': False, 'tuning_before_sha256': sha(FILE), 'validation_sha256': sha(validation_file),
          'previous_rows': [r.export_text() for r in old], 'retained_rows': [r.export_text() for r in retained],
          'added_rows': [r.export_text() for r in incoming], 'other_tuning': before_tuning,
          'new_default': 'EX7Hero', 'player_saves_edited': False}
plan = OUT / 'ActivationPlan.json'
if APPLY:
    expected = json.loads(plan.read_text())
    assert all(expected[k] == record[k] for k in ['tuning_before_sha256', 'validation_sha256', 'previous_rows', 'added_rows', 'other_tuning']), 'Activation inputs changed after dry run'
    archive = Path('D:/SpaceSurvival_AssetArchive/HeroUnreal_20261020/Tuning')
    archive.mkdir(parents=True, exist_ok=True)
    backup = archive / ('DA_Phase1_' + record['tuning_before_sha256'] + '.uasset')
    if not backup.exists():
        shutil.copy2(FILE, backup)
    assert sha(backup) == record['tuning_before_sha256']
    data.set_editor_property('heroes', incoming + retained)
    assert other_tuning() == before_tuning
    assert [r.export_text() for r in list(data.heroes)[4:]] == record['retained_rows']
    assert u.EditorAssetLibrary.save_loaded_asset(data, False)
    assert other_tuning() == before_tuning
    record.update(applied=True, tuning_after_sha256=sha(FILE), backup=str(backup), heroes=[str(r.id) for r in data.heroes])
    (OUT / 'Activation.json').write_text(json.dumps(record, indent=2))
else:
    assert sha(FILE) == record['tuning_before_sha256']
    plan.write_text(json.dumps(record, indent=2))
print('HERO_ACTIVATION_' + ('APPLIED' if APPLY else 'DRY_RUN'), record['new_default'], len(incoming + retained), flush=True)
