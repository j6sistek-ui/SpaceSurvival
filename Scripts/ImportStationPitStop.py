"""Import the composed pit stop exterior as a private static mesh, Nanite on, no collision of its own.

Run through the editor Python commandlet after AuthorStationPitStop.py:
  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=Scripts/ImportStationPitStop.py -- --tag a0

Collision is deliberately removed: ASSStation builds the body's collision from the boxes in the
receipt, so that the mouth is exactly the admission gap and nothing invisible can shade the lane.
The receipt's bounds are compared against the imported bounds so an axis mistake in the glTF path
is caught here rather than discovered as a station lying on its side.
"""
from pathlib import Path
import hashlib
import json
import sys
import unreal as u

ROOT = Path(__file__).resolve().parents[1]
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TAG = argv[argv.index('--tag') + 1] if '--tag' in argv else 'default'
OUT = ROOT / 'Artifacts' / 'StationPitStop' / TAG
BASE = '/Game/SpaceSurvival/Licensed/StationPitStop'
NAME = 'SM_StationPitStop'
LIB = u.EditorAssetLibrary


def main():
    receipt = json.loads((OUT / 'PitStop.json').read_text(encoding='utf-8'))
    source = OUT / 'StationPitStop.glb'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == receipt['output_sha256'], 'GLB changed since the receipt'
    target = f'{BASE}/{NAME}'
    # Replaceable: the exterior is iterated on. Prior versions live in git as receipts, not as assets.
    # The folder holds nothing but this import's outputs (mesh, materials, textures, and the per-part
    # meshes an uncombined attempt leaves behind): clear it so a rerun cannot inherit strays.
    for stale in LIB.list_assets(BASE, recursive=True, include_folder=False):
        assert LIB.delete_asset(stale), f'could not remove {stale}'
    pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name='SSStationPitStopImport')
    # The composition is authored in centimetres as Blender units; glTF declares them metres. Undo that here.
    for k, v in {'asset_name': NAME, 'use_source_name_for_asset': False, 'import_offset_uniform_scale': 0.01,
                 'asset_type_sub_folders': False, 'scene_name_sub_folder': False}.items():
        pipeline.set_editor_property(k, v)
    mesh_pipeline = pipeline.get_editor_property('mesh_pipeline')
    mesh_pipeline.set_editor_property('import_static_meshes', True)
    # The composition is hundreds of named parts; they are one exterior, and ASSStation references one mesh.
    mesh_pipeline.set_editor_property('combine_static_meshes_behavior', u.InterchangeCombineStaticMeshesBehavior.ALL)
    mesh_pipeline.set_editor_property('import_skeletal_meshes', False)
    pipeline.get_editor_property('animation_pipeline').set_editor_property('import_animations', False)
    materials = pipeline.get_editor_property('material_pipeline')
    materials.set_editor_property('import_materials', True)
    materials.get_editor_property('texture_pipeline').set_editor_property('import_textures', True)
    params = u.ImportAssetParameters()
    params.set_editor_property('is_automated', True)
    params.set_editor_property('replace_existing', True)
    params.set_editor_property('override_pipelines', [u.SoftObjectPath(pipeline.get_path_name())])
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    assets = manager.import_asset(BASE, manager.create_source_data(str(source)), params)
    meshes = [a for a in assets if isinstance(a, u.StaticMesh)]
    assert len(meshes) == 1, f'expected one static mesh, got {len(meshes)}'
    mesh = meshes[0]
    if mesh.get_path_name().split('.')[0] != target:
        assert LIB.rename_asset(mesh.get_path_name(), target)
    mesh = u.load_asset(target)
    assert all(slot.material_interface for slot in mesh.static_materials), 'a material slot came in empty'
    # Axis check against the receipt: the composition is authored in station-local centimetres.
    b = mesh.get_bounds()
    lo, hi = receipt['composition_bounds_cm']
    expected = [(hi[i] - lo[i]) for i in range(3)]
    got = [b.box_extent.x * 2, b.box_extent.y * 2, b.box_extent.z * 2]
    for axis, (e, g) in enumerate(zip(expected, got)):
        assert abs(e - g) < max(60.0, e * .02), f'axis {"XYZ"[axis]} size {g:.0f} cm, receipt says {e:.0f}; do not adopt'
    # The glTF round trip (Blender right-handed, Unreal left-handed) mirrors one axis. X and Z must land where the
    # receipt says; Y may come back mirrored, and the collision boxes are generated with that sign.
    centre = [(lo[i] + hi[i]) / 2 for i in range(3)]
    tol = [max(60.0, expected[i] * .02) for i in range(3)]
    assert abs(b.origin.x - centre[0]) < tol[0], f'X centre {b.origin.x:.0f} vs receipt {centre[0]:.0f}; do not adopt'
    assert abs(b.origin.z - centre[2]) < tol[2], f'Z centre {b.origin.z:.0f} vs receipt {centre[2]:.0f}; do not adopt'
    if abs(b.origin.y - centre[1]) < tol[1]:
        y_sign = 1
    elif abs(b.origin.y + centre[1]) < tol[1]:
        y_sign = -1
    else:
        raise AssertionError(f'Y centre {b.origin.y:.0f} matches neither {centre[1]:.0f} nor its mirror; do not adopt')
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    editor.remove_collisions(mesh)
    body = mesh.get_editor_property('body_setup')
    body.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    nanite = mesh.get_editor_property('nanite_settings')
    nanite.set_editor_property('enabled', True)
    mesh.set_editor_property('nanite_settings', nanite)
    for slot in mesh.static_materials:
        mat = slot.material_interface
        base = mat.get_base_material() if hasattr(mat, 'get_base_material') else mat
        if isinstance(base, u.Material):
            base.set_editor_property('used_with_nanite', True)
            u.MaterialEditingLibrary.recompile_material(base)
    for asset in assets:
        assert LIB.save_loaded_asset(asset, only_if_is_dirty=False)
    assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False)
    result = dict(mesh=mesh.get_path_name(), tag=TAG, source_sha256=receipt['output_sha256'],
                  bounds_cm_imported=[[b.origin.x - b.box_extent.x, b.origin.y - b.box_extent.y, b.origin.z - b.box_extent.z],
                                      [b.origin.x + b.box_extent.x, b.origin.y + b.box_extent.y, b.origin.z + b.box_extent.z]],
                  bounds_cm_receipt=receipt['composition_bounds_cm'], collision_boxes_cm=receipt['collision_boxes_cm'],
                  y_sign=y_sign, y_note='collision box Y is multiplied by y_sign; -1 means the glTF round trip mirrored Y',
                  materials=[s.material_interface.get_path_name() for s in mesh.static_materials],
                  triangles=receipt['triangles'], engine=u.SystemLibrary.get_engine_version())
    (OUT / 'Import.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    u.log('STATION_PITSTOP_IMPORTED ' + json.dumps(result))


if __name__ == '__main__':
    main()
