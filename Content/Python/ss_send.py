"""Send to Unreal, editor side: meshes that arrive from Blender, and meshes handed to Blender to be fixed.

Loaded by Content/Python/init_unreal.py when the editor starts; the Blender add-on (Tools/SSLiveLink,
send.py) calls it over Python remote execution while the editor is open. Three jobs:

  import_outbox()         Blender writes <Name>.glb and a sidecar <Name>.json into
                          Artifacts/LiveLink/Outbox/<Category>/. Every sidecar whose GLB is newer than the
                          import recorded for its target in Outbox/imported.json is imported.
  import_mesh(glb, to)    One GLB as one static mesh, through Interchange, exactly as
                          Scripts/ImportVaultGlb.py imports a vault listing. When the target already exists
                          it is imported over in place: the asset path stays, so every instance placed in
                          a level takes the new shape. The saved file it replaces is copied to
                          Artifacts/LiveLink/Backups/<time>/ first, byte for byte: a pack asset is
                          git-ignored, so that copy is the only way back from a fix that went wrong.
  export_for_edit(asset)  The real mesh of an asset as Artifacts/LiveLink/Edit/<name>.glb for Blender's Edit
                          Mesh, every material slot named, and textured where the material is plain enough
                          for the exporter to read without baking (a pack's layered material arrives grey;
                          the fix keeps the asset's own materials whatever Blender showed).

GLB is metres and Interchange converts to centimetres, so no scale offset is applied. Blender's +Y (up
in the file) and Unreal's left-handed frame make the mesh arrive mirrored in Y, which is the same Y flip
the live link applies to transforms: what is sent looks the same placed here as it did in Blender.

A mesh sent from Blender lives under /Game/Blender/<Category>/ and brings its own materials and textures,
which land beside it; two sends that use one material name share that material, and the later send wins
(so meshes that share a trim sheet belong in one category, or each category gets its own copy of it).
/Game/Blender is outside /Game/SpaceSurvival on purpose: that folder is always cooked, and an experiment
sent once would ship to testers for good; here a mesh ships when something in the game uses it. A fix to
an asset anywhere else keeps the asset's own materials: a pack's material is more than glTF can carry
back, so only the geometry is taken and each slot gets its old material again.

Nothing outside /Game/Blender is imported over unless the send is a fix Edit Mesh made: its sidecar sits in
Outbox/_Edits and says "edit": true. Any other sidecar naming such a target is refused.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import time

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
LINK = ROOT / 'Artifacts' / 'LiveLink'
OUTBOX = LINK / 'Outbox'
EDIT = LINK / 'Edit'
EDITS = '_Edits'                    # the Outbox folder of fixes that go back over the asset Edit Mesh fetched (send.EDITS in the add-on)
BACKUPS = LINK / 'Backups'          # <time>/<path under Content>.uasset: the saved file each import went over
KEEP_OWN = 5                        # backups kept of one asset under BLENDER_BASE, whose source is the owner's .blend; a pack asset's are all kept
RECORD = OUTBOX / 'imported.json'   # target -> the GLB time last imported, so an unchanged send is not imported twice
BLENDER_BASE = '/Game/Blender'      # as in the add-on's send.py
NANITE_TRIANGLES = 20000
COPY_SUFFIX = re.compile(r'[._]\d{3,}$')   # Blender's 'Name.001' for a taken name, or 'Name_001' once it is an asset's name
LIB = u.EditorAssetLibrary


def _log(msg):
    u.log(f'SSSend: {msg}')


# ---------------------------------------------------------------- import
def _pipeline(name, with_materials):
    pipeline = u.new_object(u.InterchangeGenericAssetsPipeline, name=f'SSSendImport_{name}')
    for k, v in {'asset_name': name, 'use_source_name_for_asset': False,
                 'asset_type_sub_folders': False, 'scene_name_sub_folder': False}.items():
        pipeline.set_editor_property(k, v)
    # Whatever Blender wrote, a library part is static; without this a rigged file yields no static mesh at all.
    common = pipeline.get_editor_property('common_meshes_properties')
    common.set_editor_property('force_all_mesh_as_type', u.InterchangeForceMeshType.IFMT_STATIC_MESH)
    mesh_pipeline = pipeline.get_editor_property('mesh_pipeline')
    mesh_pipeline.set_editor_property('import_static_meshes', True)
    # One send is one asset, however many nodes and primitives the file holds.
    mesh_pipeline.set_editor_property('combine_static_meshes_behavior', u.InterchangeCombineStaticMeshesBehavior.ALL)
    mesh_pipeline.set_editor_property('import_skeletal_meshes', False)
    # The pipeline's own default builds Nanite for everything, a 24 triangle crate and a glass door alike (Nanite
    # draws no translucent material). import_mesh decides: on for a heavy mesh, or for an asset that had it on.
    try:
        mesh_pipeline.set_editor_property('build_nanite', False)
    except Exception as e:  # import_mesh sets the mesh's own switch afterwards either way
        _log(f'pipeline option build_nanite skipped: {e}')
    pipeline.get_editor_property('animation_pipeline').set_editor_property('import_animations', False)
    materials = pipeline.get_editor_property('material_pipeline')
    materials.set_editor_property('import_materials', with_materials)
    materials.get_editor_property('texture_pipeline').set_editor_property('import_textures', with_materials)
    return pipeline


def _unset(material):
    """True for a slot nothing was assigned to: empty, or wearing the engine's grid, which is what Interchange
    leaves on a slot whose material it was told not to import."""
    return material is None or material.get_path_name().startswith('/Engine/EngineMaterials/WorldGridMaterial')


def _restore_materials(mesh, before):
    """Give each slot of a re-imported mesh the material it had. before is [(slot name, material)].

    A slot is matched by its name, then by the name of the material it held (the glTF round trip names a
    slot after its material), then by either name without a copy suffix, then by position when the slot
    count is unchanged. Blender calls a material 'Name.001' whenever its file already holds a 'Name' (a
    placed proxy of the part is enough), which arrives here as 'Name.001' or 'Name_001'; the add-on sends
    the real name, and this is for the file that did not come through it. The exact names go first, so a
    pack's own 'M_Wall_001' is never mistaken for a copy of 'M_Wall'. Returns the names of the slots left
    without a material: ones the fix added in Blender.
    """
    by_slot = {slot: mat for slot, mat in before if mat}
    by_material = {mat.get_name(): mat for _, mat in before if mat}
    same_count = len(before) == len(mesh.static_materials)
    empty = []
    for i, slot in enumerate(mesh.static_materials):
        slot_name = str(slot.material_slot_name)
        came_with = '' if _unset(slot.material_interface) else slot.material_interface.get_name()
        names = [n for n in (slot_name, came_with) if n]
        names += [COPY_SUFFIX.sub('', n) for n in names]
        keep = next((m for m in (by_slot.get(n) or by_material.get(n) for n in names) if m), None) or (before[i][1] if same_count else None)
        if keep:
            mesh.set_material(i, keep)
        elif _unset(slot.material_interface):
            empty.append(slot_name)
    return empty


def _disk(package):
    return ROOT / 'Content' / (package[len('/Game/'):] + '.uasset')


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def backup_asset(package):
    """Copy the saved file of package into BACKUPS before it is imported over. Returns the copy.

    Refuses an asset with no saved file: imported over, there would be nothing to go back to. Of an asset
    under BLENDER_BASE the newest KEEP_OWN copies are kept; of anything else, every copy, the first of which
    is the pack's own original.
    """
    disk = _disk(package)
    if not disk.is_file():
        raise RuntimeError(f'{package} has no saved file to back up: save it in the editor, then send again')
    rel = Path(package[len('/Game/'):] + '.uasset')
    stamp, n = time.strftime('%Y%m%d-%H%M%S'), 1
    copy = BACKUPS / stamp / rel
    while copy.exists():
        n += 1
        copy = BACKUPS / f'{stamp}-{n}' / rel
    copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(disk, copy)
    if _sha256(copy) != _sha256(disk):
        raise RuntimeError(f'the backup at {copy} does not match {disk}; nothing was imported')
    if package.startswith(BLENDER_BASE + '/'):
        older = sorted((p for p in BACKUPS.glob('*/' + rel.as_posix()) if p != copy), key=lambda p: p.stat().st_mtime)
        for stale in older[:max(0, len(older) - (KEEP_OWN - 1))]:
            try:
                stale.unlink()
            except OSError:
                pass
    return copy


def _reload_from_disk(package):
    """Put back what the saved file holds, after an import over it failed half way: a mesh left dirty in
    memory would be written over the good file by the next Save All."""
    try:
        loaded = u.find_package(package) or u.load_package(package)
        mode = getattr(u, 'ReloadPackagesInteractionMode', None)
        ok = u.EditorLoadingAndSavingUtils.reload_packages([loaded], mode.ASSUME_POSITIVE) if mode else \
            u.EditorLoadingAndSavingUtils.reload_packages([loaded])
        return bool(ok[0] if isinstance(ok, tuple) else ok)
    except Exception as e:
        u.log_warning(f'SSSend: could not reload {package} ({e})')
        return False


def import_mesh(glb, target, keep_materials=None):
    """Import one GLB as the static mesh at target ('/Game/.../SM_Name', or that with '.SM_Name'). Returns a receipt.

    When target exists the import goes over it, never beside it, so the path stays stable; its saved file
    is copied to BACKUPS first ('backup' in the receipt), and should the import then fail the asset is
    reloaded from that untouched file. keep_materials (default: true for an existing asset outside
    BLENDER_BASE) imports the geometry alone and puts the asset's own materials back on its slots.
    """
    glb = Path(glb)
    package = str(target).split('.')[0]
    assert package.startswith('/Game/') and package.count('/') >= 2, f'not a /Game asset path: {target}'
    assert glb.exists(), f'missing {glb}'
    existing = u.load_asset(package) if LIB.does_asset_exist(package) else None
    if existing is not None and not isinstance(existing, u.StaticMesh):
        raise ValueError(f'{package} exists and is not a static mesh')
    if existing is None and _disk(package).is_file():
        # On disk but not in the registry (a file copied into Content with the editor open): importing 'new' would overwrite it unseen.
        raise RuntimeError(f'{_disk(package)} exists but the editor does not know it yet: restart the editor, then send again')
    backup = backup_asset(package) if existing is not None else None
    try:
        receipt = _import_over(glb, package, existing, keep_materials)
    except Exception as e:
        if existing is not None:
            existing = None
            state = 'it was reloaded from its saved file' if _reload_from_disk(package) else \
                'it may be half replaced in memory: do not save it, and restart the editor'
            raise RuntimeError(f'{e} ({package} was not saved; {state}; the file as it was is also kept at {backup})')
        raise
    receipt['backup'] = str(backup) if backup else None
    _log(f'{receipt["status"]} {receipt["asset"]}: {receipt["triangles"]} triangles' + (f'; the file it replaced is kept at {backup}' if backup else ''))
    return receipt


def _import_over(glb, package, existing, keep_materials):
    target_dir, name = package.rsplit('/', 1)
    if keep_materials is None:
        keep_materials = existing is not None and not package.startswith(BLENDER_BASE + '/')
    before = [(str(s.material_slot_name), s.material_interface) for s in existing.static_materials] if existing else []
    was_nanite = bool(existing and existing.get_editor_property('nanite_settings').get_editor_property('enabled'))
    params = u.ImportAssetParameters()
    params.set_editor_property('is_automated', True)
    params.set_editor_property('replace_existing', True)
    params.set_editor_property('override_pipelines', [u.SoftObjectPath(_pipeline(name, not keep_materials).get_path_name())])
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    assets = manager.import_asset(target_dir, manager.create_source_data(str(glb)), params)
    meshes = [a for a in assets if isinstance(a, u.StaticMesh)]
    assert len(meshes) == 1, f'{name}: expected one static mesh, got {len(meshes)}'
    mesh = meshes[0]
    landed = mesh.get_path_name().split('.')[0]
    if landed != package:
        # Beside an existing target is the one place it must not land: the placed instances would keep the old shape.
        assert existing is None, f'{name}: imported beside the asset, at {landed}, instead of over it'
        assert LIB.rename_asset(mesh.get_path_name(), package), f'{name}: rename failed'
        mesh = u.load_asset(package)
    empty = _restore_materials(mesh, before) if keep_materials else \
        [str(s.material_slot_name) for s in mesh.static_materials if _unset(s.material_interface)]
    if empty:
        u.log_warning(f'SSSend: {name}: no material on {empty}; assign one in the editor')
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    if editor.get_simple_collision_count(mesh) == 0:
        try:
            editor.add_simple_collisions(mesh, u.ScriptCollisionShapeType.BOX)
        except Exception as e:  # a missing box is a prop without a blocker, not a failed import
            u.log_warning(f'SSSend: {name}: box collision not added ({e})')
    triangles = mesh.get_num_triangles(0)
    nanite_on = was_nanite or triangles >= NANITE_TRIANGLES
    touched = []
    nanite = mesh.get_editor_property('nanite_settings')
    if bool(nanite.get_editor_property('enabled')) != nanite_on:
        nanite.set_editor_property('enabled', nanite_on)
        mesh.set_editor_property('nanite_settings', nanite)
    if nanite_on:
        for slot in mesh.static_materials:
            mat = slot.material_interface
            base = mat.get_base_material() if mat and hasattr(mat, 'get_base_material') else mat
            if isinstance(base, u.Material) and not base.get_editor_property('used_with_nanite'):
                base.set_editor_property('used_with_nanite', True)
                u.MaterialEditingLibrary.recompile_material(base)
                touched.append(base)
    for asset in [a for a in assets if a] + touched:
        LIB.save_loaded_asset(asset, only_if_is_dirty=False)
    assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False), f'{name}: save failed'
    bounds = mesh.get_bounds()
    receipt = {'asset': mesh.get_path_name(), 'status': 'reimported' if existing else 'imported', 'triangles': triangles,
               'nanite': nanite_on, 'kept_materials': bool(keep_materials), 'empty_slots': empty,
               'origin_cm': [round(v, 2) for v in (bounds.origin.x, bounds.origin.y, bounds.origin.z)],
               'extent_cm': [round(v, 2) for v in (bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z)],
               'materials': [s.material_interface.get_path_name() if s.material_interface else '' for s in mesh.static_materials]}
    try:
        receipt['library_refreshed'] = _refresh_library(mesh, new=existing is None)
    except Exception as e:  # the asset is imported and saved; a stale proxy is a warning
        u.log_warning(f'SSSend: {name}: parts library not refreshed ({e})')
    return receipt


def _refresh_library(mesh, new=False):
    """After a mesh arrived or changed shape: renew what the prefab library holds of it. Returns True when it wrote anything.

    The catalogue keeps proxies and thumbnails that are already on disk, so without this Blender would go on
    showing the old shape. The proxy is exported again, the thumbnail is drawn again (or removed, for
    Blender's next thumbnail pass), and the catalogue row takes the new bounds.

    A new mesh under BLENDER_BASE gets a row of its own, so the mesh the owner has just sent can be found
    by type and picture like any other part, without a Rebuild Catalogue. Its category is its folder's
    (ss_prefabs.classify). Anything else the catalogue does not already hold is left out, as the catalogue
    leaves it out.
    """
    import ss_prefabs
    path = mesh.get_path_name()
    catalog = ss_prefabs.load_catalog()
    if not catalog:
        return False   # no catalogue yet: Rebuild Catalogue will list the mesh with all the others
    pack = ss_prefabs.pack_of(path)
    proxy_rel = 'proxies/' + pack.replace('/', '_') + '/' + path.split('.')[0][len('/Game/' + pack) + 1:] + '.glb'
    proxy = ss_prefabs.LIBRARY / proxy_rel
    row = next((m for m in catalog.get('meshes', []) if m.get('asset') == path), None)
    adding = row is None and new and path.startswith(BLENDER_BASE + '/')
    if not proxy.exists() and row is None and not adding:
        return False
    if proxy.exists() or adding:
        ss_prefabs.export_proxy(mesh, proxy)
    thumb = ss_prefabs.thumb_rel(proxy_rel) if proxy.exists() else None
    drawn = False
    if thumb:
        try:
            drawn = ss_prefabs.export_thumbnail(mesh, ss_prefabs.LIBRARY / thumb)
        except Exception as e:
            _log(f'thumbnail not drawn for {path}: {e}')
        if not drawn and (ss_prefabs.LIBRARY / thumb).exists():
            (ss_prefabs.LIBRARY / thumb).unlink()   # the old shape's picture: Blender's next thumbnail pass renders it again
    b = mesh.get_bounds()
    if adding:
        category = ss_prefabs.classify(path)
        row = {'asset': path, 'name': path.split('.')[-1], 'pack': pack, 'group': ss_prefabs.group_of(category), 'category': category}
        catalog.setdefault('meshes', []).append(row)
        for key, value in (('categories', category), ('groups', row['group'])):
            if isinstance(catalog.get(key), dict):
                catalog[key][value] = catalog[key].get(value, 0) + 1
    if row is not None:
        row.update(origin=[b.origin.x, b.origin.y, b.origin.z], extent=[b.box_extent.x, b.box_extent.y, b.box_extent.z],
                   radius=b.sphere_radius, triangles=mesh.get_num_triangles(0),
                   materials=[s.material_interface.get_path_name() if s.material_interface else '' for s in mesh.static_materials])
        if proxy.exists():
            row['proxy'] = proxy_rel
        row.pop('thumb', None)
        row.pop('thumb_source', None)
        if drawn:
            row.update(thumb=thumb, thumb_source='unreal')
        ss_prefabs.CATALOG.write_text(json.dumps(catalog, indent=1), encoding='utf-8')
    return True


# ---------------------------------------------------------------- the outbox
def _read_record():
    try:
        data = json.loads(RECORD.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def queued(only=None):
    """[(name, glb, sidecar dict)] for every send in the Outbox, in a stable order. A sidecar that cannot be
    read, names no /Game target, or names one it has no right to (see _allowed) comes back with an 'error'
    in its dict. only: nothing but these, each an Outbox folder ('Props') or one send in a folder
    ('_Edits/SM_Door_1a2b'); a name or a list of them."""
    rows = []
    if not OUTBOX.exists():
        return rows
    wanted = None if only is None else {only} if isinstance(only, str) else set(only)
    for path in sorted(OUTBOX.rglob('*.json')):
        if path == RECORD or (wanted is not None and not {path.parent.name, f'{path.parent.name}/{path.stem}'} & wanted):
            continue
        try:
            side = json.loads(path.read_text(encoding='utf-8'))
            assert isinstance(side, dict) and str(side.get('target', '')).startswith('/Game/'), 'no /Game target'
        except Exception as e:
            rows.append((path.stem, path.with_suffix('.glb'), {'error': f'unreadable sidecar: {e}'}))
            continue
        refusal = _allowed(path, side)
        if refusal:
            rows.append((path.stem, path.with_suffix('.glb'), {'error': refusal, 'target': side['target']}))
            continue
        # The GLB sits beside its sidecar; "glb" (relative to the project) is for a sidecar someone moved.
        glb = path.with_suffix('.glb')
        if not glb.exists() and side.get('glb'):
            glb = Path(side['glb']) if Path(side['glb']).is_absolute() else ROOT / side['glb']
        rows.append((path.stem, glb, side))
    return rows


def _allowed(path, side):
    """'' when this sidecar may be imported, else why not.

    Everything the owner models lands under BLENDER_BASE. The one send that may go over an asset anywhere
    else is a fix Edit Mesh made: the add-on files it in Outbox/_Edits with "edit": true, and only for the
    one object Edit Mesh brought in. A sidecar that names a pack asset from any other folder is a mistake
    or a stale file, and importing it would replace licensed content nobody asked to replace.
    """
    package = str(side['target']).split('.')[0]
    if package.startswith(BLENDER_BASE + '/'):
        return ''
    if path.parent.name == EDITS and side.get('edit') is True:
        return '' if LIB.does_asset_exist(package) else f'{package} is not there to be fixed (was it moved or deleted?)'
    return (f'{package} is outside {BLENDER_BASE}: only a fix made with Edit Mesh (Outbox/{EDITS}, "edit": true) may replace '
            f'an asset there')


def pending():
    """The names in the Outbox that import_outbox() would import now."""
    record = _read_record()
    return [name for name, glb, side in queued() if 'error' not in side and glb.exists()
            and glb.stat().st_mtime > record.get(side['target'], {}).get('mtime', 0.0)]


def import_outbox(force=False, only=None):
    """Import every send whose GLB is newer than its last recorded import. Returns
    {"imported": [names], "kept": [names], "failed": [[name, error]], "backups": [[name, the file kept of what it replaced]]}.

    A send that fails is recorded too, with its error, and is reported as failed without another attempt
    until Blender sends it again: a broken file must not cost every editor start an import. only keeps
    this to the named folders or sends, as queued() reads it, and leaves the rest queued
    (Scripts/TestSendScenes.py, which must not import what the owner has waiting).
    """
    record = _read_record()
    imported, kept, failed, backups = [], [], [], []
    for name, glb, side in queued(only):
        if 'error' in side:
            failed.append([name, side['error']])
            continue
        if not glb.exists():
            failed.append([name, f'missing {glb.name}'])
            continue
        last = record.get(side['target'], {})
        mtime = glb.stat().st_mtime
        if not force and mtime <= last.get('mtime', 0.0):
            if last.get('error'):
                failed.append([name, last['error']])
            else:
                kept.append(name)
            continue
        entry = {'mtime': mtime, 'glb': str(glb), 'when': time.strftime('%Y-%m-%d %H:%M:%S')}
        try:
            receipt = import_mesh(glb, side['target'])
            entry.update(asset=receipt['asset'], status=receipt['status'], triangles=receipt['triangles'],
                         empty_slots=receipt['empty_slots'], backup=receipt.get('backup'))
            imported.append(name)
            if receipt.get('backup'):
                backups.append([name, receipt['backup']])
        except Exception as e:  # one bad send must not stop the rest
            u.log_error(f'SSSend: {name}: {e}')
            entry['error'] = str(e)
            failed.append([name, str(e)])
        record[side['target']] = entry
        OUTBOX.mkdir(parents=True, exist_ok=True)
        RECORD.write_text(json.dumps(record, indent=1), encoding='utf-8')   # after each one: a crash keeps what was done
    summary = {'imported': imported, 'kept': kept, 'failed': failed, 'backups': backups}
    if imported or failed:
        _log(f'outbox: {summary}')
    return summary


# ---------------------------------------------------------------- export for Edit Mesh
def _edit_options():
    opts = u.GLTFExportOptions()
    # The source model, not the render data: for a Nanite mesh the render data is only the coarse fallback.
    for k, v in {'export_uniform_scale': 0.01, 'bake_material_inputs': u.GLTFMaterialBakeMode.DISABLED,
                 'texture_image_format': u.GLTFTextureImageFormat.PNG, 'export_source_model': True,
                 'export_proxy_materials': False, 'export_vertex_colors': False, 'default_level_of_detail': 0,
                 'export_lightmaps': False, 'export_material_variants': u.GLTFMaterialVariantMode.NONE}.items():
        try:
            opts.set_editor_property(k, v)
        except Exception as e:  # an option missing in this engine version is not fatal
            _log(f'glTF option {k} skipped: {e}')
    return opts


def export_for_edit(asset):
    """Write the real mesh of asset for Blender to edit, with what textures export without baking. Returns
    {"glb": absolute path, "asset": ..., "triangles": n}."""
    mesh = u.load_asset(asset)
    if not isinstance(mesh, u.StaticMesh):
        raise ValueError(f'not a static mesh: {asset}')
    if not hasattr(u, 'GLTFExporter'):
        raise RuntimeError('the GLTFExporter plugin is not enabled')
    out = EDIT / (str(asset).split('.')[0].rsplit('/', 1)[-1] + '.glb')
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()   # so a failed export cannot hand Blender the last asset edited under this name
    result = u.GLTFExporter.export_to_gltf(mesh, str(out), _edit_options(), set())
    ok = result[0] if isinstance(result, tuple) else bool(result)
    if not ok or not out.exists():
        raise RuntimeError(f'glTF export of {asset} failed')
    _log(f'for edit: {asset} -> {out}')
    return {'glb': str(out), 'asset': mesh.get_path_name(), 'triangles': mesh.get_num_triangles(0)}


# ---------------------------------------------------------------- editor start
_waiting = {'handle': None}


def _interactive():
    """True in the open editor. A commandlet must not import: it may be running beside an editor doing the same."""
    try:
        return u.ToolMenus.get() is not None and not u.SystemLibrary.is_unattended()
    except Exception:
        return False


def _import_when_ready(delta_seconds):
    """Slate tick: import the Outbox once the asset registry knows what exists, then stop ticking."""
    if u.AssetRegistryHelpers.get_asset_registry().is_loading_assets():
        return
    if _waiting['handle'] is not None:
        u.unregister_slate_post_tick_callback(_waiting['handle'])
        _waiting['handle'] = None
    try:
        import_outbox()
    except Exception as e:
        u.log_warning(f'SSSend: outbox not imported ({e})')


def register():
    """Called by init_unreal.py at editor start: nothing to set up, but what Blender queued while the editor
    was closed arrives now."""
    try:
        if not _interactive():
            return
        waiting = pending()
        _log(f'ready; {len(waiting)} queued in the outbox' + (f': {", ".join(waiting)}' if waiting else ''))
        if not waiting:
            return
        if u.AssetRegistryHelpers.get_asset_registry().is_loading_assets():
            # Too early to ask whether a target exists: importing now could land beside an asset instead of over it.
            if _waiting['handle'] is None:
                _waiting['handle'] = u.register_slate_post_tick_callback(_import_when_ready)
        else:
            import_outbox()
    except Exception as e:  # start-up must never fail the editor over a queued mesh
        u.log_warning(f'SSSend: outbox not imported ({e})')
