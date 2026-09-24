"""Focused Unreal validation for portable material overrides; run offscreen in the owner project."""
import importlib.util
import json
from pathlib import Path
import unreal as u

code = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ss_surfaces', code / 'Content/Python/ss_surfaces.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
s.ROOT = '/Game/SpaceSurvival/Licensed/_SSSurfaceReview20260922'
values = {'base_color': [0.4, 0.5, 0.6], 'metallic': 1.0, 'roughness': 0.02,
          'opacity': 1.0, 'transmission': 0.0, 'ior': 1.45}
mesh = u.load_asset('/Engine/BasicShapes/Cube.Cube')
original = mesh.get_material(0).get_path_name()
rows = [{'asset': mesh.get_path_name(), 'surface_overrides': {'0': values}}]
resolved = s.resolve_rows(rows)
first = resolved[0]['materials'][0]
assert s.resolve_rows(rows)[0]['materials'][0] == first
assert mesh.get_material(0).get_path_name() == original
glass = dict(values, metallic=0.0, opacity=0.18, transmission=1.0)
second = s.material_for(glass)
assert u.load_asset(second).get_editor_property('blend_mode') == u.BlendMode.BLEND_TRANSLUCENT
try:
    s.resolve_rows([{'asset': mesh.get_path_name(), 'surface_overrides': {'12': values}}])
    raise AssertionError('invalid slot accepted')
except ValueError:
    pass
assert hasattr(u.get_editor_subsystem(u.LevelEditorSubsystem), 'is_in_play_in_editor')
receipt = {'result': 'PASS', 'checks': ['opaque and translucent materials', 'idempotent reuse', 'mesh default unchanged', 'invalid slot rejected'], 'generated': [first, second]}
(code / 'Artifacts/LibraryReview').mkdir(parents=True, exist_ok=True)
(code / 'Artifacts/LibraryReview/surfaces-unreal.json').write_text(json.dumps(receipt, indent=2))
# The test owns exactly these two new assets. Leave all original game/vendor assets untouched.
for path in (first, second):
    assert path.startswith(s.ROOT + '/')
    assert u.EditorAssetLibrary.delete_asset(path)
u.log('SS_SURFACE_TEST_OK')
