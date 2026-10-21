"""Retire white EX7 from the roster and put the existing Cloth row first.

Default is a read-only plan. Apply requires -SSRetireWhiteHero and the unchanged
plan. Preserve all other tuning, existing row values, source assets and saves.
"""
import hashlib
import json
import shutil
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / '.agent/local/QualityPass_20261021'
OUT.mkdir(parents=True, exist_ok=True)
FILE = ROOT / 'Content/SpaceSurvival/Data/DA_Phase1.uasset'
APPLY = '-SSRetireWhiteHero' in u.SystemLibrary.get_command_line().split()
data = u.load_asset('/Game/SpaceSurvival/Data/DA_Phase1')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def other_tuning():
    values = {}
    for name in dir(data):
        if name.startswith('_') or name == 'heroes':
            continue
        try:
            value = data.get_editor_property(name)
        except Exception:
            continue
        values[name] = value.export_text() if hasattr(value, 'export_text') else str(value)
    return values


old = list(data.heroes)
cloth = next(row for row in old if str(row.id) == 'ClothHero')
assert u.load_asset(cloth.mesh_path), 'Cloth mesh unavailable'
assert u.load_asset(cloth.idle_clip_path), 'Cloth idle unavailable'
new = [cloth] + [row for row in old if str(row.id) not in ('ClothHero', 'EX7Hero')]
record = {'before_sha256': sha(FILE), 'before_rows': [r.export_text() for r in old],
          'after_rows': [r.export_text() for r in new], 'other_tuning': other_tuning(),
          'new_default': 'ClothHero', 'white_assets_retained': True, 'saves_edited': False}
plan = OUT / 'RosterPlan.json'
if APPLY:
    assert json.loads(plan.read_text()) == record, 'Tuning changed since dry run'
    assert any(str(row.id) == 'EX7Hero' for row in old), 'White already retired'
    archive = Path('D:/SpaceSurvival_AssetArchive/QualityPass_20261021')
    archive.mkdir(parents=True, exist_ok=True)
    backup = archive / ('DA_Phase1_' + record['before_sha256'] + '.uasset')
    if not backup.exists():
        shutil.copy2(FILE, backup)
    assert sha(backup) == record['before_sha256']
    data.set_editor_property('heroes', new)
    assert other_tuning() == record['other_tuning']
    assert [r.export_text() for r in data.heroes] == record['after_rows']
    assert u.EditorAssetLibrary.save_loaded_asset(data, False)
    record.update(applied=True, after_sha256=sha(FILE), backup=str(backup))
    (OUT / 'RosterApplied.json').write_text(json.dumps(record, indent=2))
else:
    plan.write_text(json.dumps(record, indent=2))
print('ROSTER_' + ('APPLIED' if APPLY else 'PLAN'), [str(r.id) for r in new])
