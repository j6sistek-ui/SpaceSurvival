"""Import the GLB-only Fab downloads in the vault cache, so they join the prefab library.

  UnrealEditor-Cmd.exe <project> -unattended -stdout -FullStdOutLogOutput \
      -ExecutePythonScript="<abs path>/Scripts/ImportVaultGlb.py [-- --only arcade] [--skip planet] [--force]"

Some Fab listings arrive as a single converted GLB under
`User downloaded assets/VaultCache/FabLibrary/<Listing>-<hash>/glb/converted/` and are never seen by the
project: they are not under /Game, so the catalogue, the Blender panel and the gallery cannot show them.
This brings each one in as one static mesh with its materials and textures at
/Game/Fab/<Listing>/SM_<Listing>, writes a receipt, and leaves the rest to
Scripts/ExportPrefabCatalog.py. Licensed content stays out of git (the folder is ignored); the receipts
in Artifacts/VaultImport say what was imported from what.

GLB is metres and Interchange converts to centimetres, so no scale offset is applied here (the pit stop
import needs one only because that composition is authored in centimetres).
"""
from pathlib import Path
import hashlib
import json
import re
import sys

import unreal as u

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / 'User downloaded assets' / 'VaultCache' / 'FabLibrary'
# Outside /Game/SpaceSurvival on purpose: that tree is always cooked, and a 355 MB planet nobody has placed yet
# does not belong in the tester download. Here a listing cooks only once a level or prefab references it.
BASE = '/Game/Fab'
OUT = ROOT / 'Artifacts' / 'VaultImport'
LIB = u.EditorAssetLibrary
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FORCE = '--force' in argv
ONLY = [argv[i + 1].lower() for i, a in enumerate(argv) if a == '--only' and i + 1 < len(argv)]
SKIP = [argv[i + 1].lower() for i, a in enumerate(argv) if a == '--skip' and i + 1 < len(argv)]
# Listings the project already imported by hand under another path: importing them twice only costs disk.
ALREADY = {'Space_Station_4': '/Game/SpaceSurvival/Licensed/StationExterior/SM_StationExterior'}
NANITE_TRIANGLES = 20000


def listing_title(folder):
    """The Fab title from the listing's metadata, which is UTF-8 for some downloads and UTF-16 for others."""
    meta = folder / 'glb' / 'converted' / 'metadata'
    if not meta.exists():
        return ''
    raw = meta.read_bytes()
    for encoding in ('utf-8-sig', 'utf-16'):
        try:
            return json.loads(raw.decode(encoding)).get('listing', {}).get('title', '')
        except (UnicodeDecodeError, ValueError):
            continue
    return ''


def downloads():
    """(safe name, folder, glb) for every GLB-only download; a repeated listing name takes its hash as a suffix."""
    seen = {}
    rows = []
    for folder in sorted(p for p in VAULT.iterdir() if p.is_dir()):
        glbs = sorted((folder / 'glb' / 'converted').glob('*.glb')) if (folder / 'glb' / 'converted').is_dir() else []
        if not glbs:
            continue
        match = re.match(r'^(.*)-([0-9a-f]{8})$', folder.name)
        base, digest = (match.group(1), match.group(2)) if match else (folder.name, '')
        safe = re.sub(r'_+', '_', re.sub(r'[^A-Za-z0-9]+', '_', base)).strip('_')
        if safe in seen:
            safe = f'{safe}_{digest[:4]}'
        seen[safe] = folder
        rows.append((safe, folder, glbs[0]))
    return rows


def import_one(safe, folder, glb):
    target_dir = f'{BASE}/{safe}'
    name = f'SM_{safe}'
    target = f'{target_dir}/{name}'
    if LIB.does_asset_exist(target) and not FORCE:
        return {'name': safe, 'status': 'kept', 'asset': target}
    for stale in LIB.list_assets(target_dir, recursive=True, include_folder=False):
        assert LIB.delete_asset(stale), f'could not remove {stale}'
    pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name=f'SSVaultImport_{safe}')
    for k, v in {'asset_name': name, 'use_source_name_for_asset': False,
                 'asset_type_sub_folders': False, 'scene_name_sub_folder': False}.items():
        pipeline.set_editor_property(k, v)
    # Some listings are rigged (the drone, one of the stations). As library props they are static: without this the
    # importer finds skeletal meshes only and returns no static mesh at all.
    common = pipeline.get_editor_property('common_meshes_properties')
    common.set_editor_property('force_all_mesh_as_type', u.InterchangeForceMeshType.IFMT_STATIC_MESH)
    mesh_pipeline = pipeline.get_editor_property('mesh_pipeline')
    mesh_pipeline.set_editor_property('import_static_meshes', True)
    # A listing is one prop, however many nodes its author split it into.
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
    assets = manager.import_asset(target_dir, manager.create_source_data(str(glb)), params)
    meshes = [a for a in assets if isinstance(a, u.StaticMesh)]
    assert len(meshes) == 1, f'{safe}: expected one static mesh, got {len(meshes)}'
    mesh = meshes[0]
    if mesh.get_path_name().split('.')[0] != target:
        assert LIB.rename_asset(mesh.get_path_name(), target), f'{safe}: rename failed'
        mesh = u.load_asset(target)
    assert all(slot.material_interface for slot in mesh.static_materials), f'{safe}: a material slot came in empty'
    bounds = mesh.get_bounds()
    size = [bounds.box_extent.x * 2, bounds.box_extent.y * 2, bounds.box_extent.z * 2]
    # A prop between a centimetre and a few kilometres is plausible; anything else is a unit mistake to look at.
    plausible = 1.0 <= max(size) <= 500000.0
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    if editor.get_simple_collision_count(mesh) == 0:
        try:
            editor.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX)
        except Exception as e:  # a missing box is a dressing prop without a blocker, not a failed import
            u.log_warning(f'VaultImport: {safe}: box collision not added ({e})')
    triangles = mesh.get_num_triangles(0)
    if triangles >= NANITE_TRIANGLES:
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
        LIB.save_loaded_asset(asset, only_if_is_dirty=False)
    assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False), f'{safe}: save failed'
    receipt = {'name': safe, 'status': 'imported', 'asset': mesh.get_path_name(), 'title': listing_title(folder),
               'source': str(glb.relative_to(ROOT)).replace('\\', '/'), 'source_sha256': hashlib.sha256(glb.read_bytes()).hexdigest(),
               'size_cm': [round(v, 1) for v in size], 'plausible_size': plausible, 'triangles': triangles,
               'nanite': triangles >= NANITE_TRIANGLES,
               'materials': [s.material_interface.get_path_name() for s in mesh.static_materials]}
    (OUT / f'{safe}.json').write_text(json.dumps(receipt, indent=1), encoding='utf-8')
    return receipt


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for safe, folder, glb in downloads():
        key = safe.lower()
        if ONLY and not any(o in key for o in ONLY):
            continue
        if any(s in key for s in SKIP):
            results.append({'name': safe, 'status': 'skipped'})
            continue
        if safe in ALREADY and LIB.does_asset_exist(ALREADY[safe]):
            results.append({'name': safe, 'status': 'already', 'asset': ALREADY[safe]})
            continue
        try:
            results.append(import_one(safe, folder, glb))
        except Exception as e:  # one bad listing must not stop the rest
            u.log_error(f'VaultImport: {safe}: {e}')
            results.append({'name': safe, 'status': 'failed', 'error': str(e)})
    summary = {'imported': [r['name'] for r in results if r['status'] == 'imported'],
               'kept': [r['name'] for r in results if r['status'] in ('kept', 'already')],
               'skipped': [r['name'] for r in results if r['status'] == 'skipped'],
               'failed': [(r['name'], r.get('error')) for r in results if r['status'] == 'failed'],
               'implausible_size': [r['name'] for r in results if r.get('plausible_size') is False]}
    (OUT / 'Summary.json').write_text(json.dumps({'summary': summary, 'results': results}, indent=1), encoding='utf-8')
    u.log('VAULT_GLB_IMPORTED ' + json.dumps(summary))


if __name__ == '__main__':
    main()
