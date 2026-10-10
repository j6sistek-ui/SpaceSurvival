"""Measured private docked-cargo variant and matching station gangway.

The lead invokes this file separately in a dedicated offscreen editor to prepare
the private cargo level (dry-run by default, -SSApplyStationCargo to author).
apply(ctx) then places it in the owner preview; apply never loads/saves a level.
Saved cargo probes establish geometry/collision inputs, not gameplay acceptance.
"""
import hashlib
import json
import shutil
import sys
import traceback
from pathlib import Path

import unreal as u

SOURCE = '/Game/BuildingLibrary/Ships/L_CargoShip_Complete'
PRIVATE = '/Game/OutpostSandbox/StationRefinement/Cargo/'
LEVEL = PRIVATE + 'L_DockedCargo'
WRAPPER = PRIVATE + 'BP_DockedCargo'
SOURCE_HASH = 'd2601cf5d7881481ba2be26d09af64b3776cefee75c1a1e54b49af6c74dab588'
POSITION = (-3000., -8000., -484.)
ENTRY_Y = -1140.
FLOOR_Z = 484.
CUT_MIN = (235., -1250., 472.)
CUT_MAX = (710., -1030., 742.)
CUT_ACTORS = ('StaticMeshActor_157', 'StaticMeshActor_15', 'StaticMeshActor_39')
PANEL = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_UniversalPanel400X200_V2.SM_UniversalPanel400X200_V2'
METAL = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Materials/Instances/Opaque/MI_Metal02_AnodizedAluminium.MI_Metal02_AnodizedAluminium'
DARK = '/Game/OutpostSandbox/Materials/M_OutpostGraphite.M_OutpostGraphite'


def _root():
    return Path(u.Paths.project_dir()).resolve()


def _file(package, world=False):
    if package.startswith('/Engine/'):
        content = Path(u.Paths.convert_relative_path_to_full(u.Paths.engine_content_dir()))
        relative = package.removeprefix('/Engine/')
    else:
        assert package.startswith('/Game/'), 'Unexpected asset mount: ' + package
        content = _root() / 'Content'
        relative = package.removeprefix('/Game/')
    return content / (relative.split('.')[0] + ('.umap' if world else '.uasset'))


def _sha(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _hit(result):
    f = result.to_tuple() if result is not None else None
    return ({'actor': f[9].get_name() if f[9] else None,
             'label': f[9].get_actor_label() if f[9] else None,
             'point': list(f[5].to_tuple()), 'normal': list(f[7].to_tuple()),
             'initial_overlap': bool(f[1])} if f and f[0] else None)


def _intersects(center, extent, minimum, maximum):
    c, e = center.to_tuple(), extent.to_tuple()
    return all(c[i]+e[i] > minimum[i] and c[i]-e[i] < maximum[i] for i in range(3))


def _material_paths(mesh):
    return [slot.material_interface.get_path_name() if slot.material_interface else None
            for slot in mesh.get_editor_property('static_materials')]


def _remove_box_cap(dynamic, component, axis, position, required=True):
    # Remove only triangles wholly on an artificial subtraction-box face.
    transform = component.get_world_transform()
    assert all(abs(v-1) < 1.e-6 for v in transform.scale3d.to_tuple())
    assert all(abs(v) < 1.e-6 for v in transform.rotation.to_tuple()[:3])
    lo, hi = [v-.02 for v in CUT_MIN], [v+.02 for v in CUT_MAX]
    lo[axis], hi[axis] = position-.02, position+.02
    minimum = u.MathLibrary.inverse_transform_location(transform, u.Vector(*lo))
    maximum = u.MathLibrary.inverse_transform_location(transform, u.Vector(*hi))
    _, selection = u.GeometryScript_MeshSelection.select_mesh_elements_in_box(dynamic,
        u.Box(min=minimum, max=maximum), min_num_triangle_points=3)
    _, count = u.GeometryScript_MeshSelection.get_mesh_selection_info(selection)
    assert (1 if required else 0) <= count <= 2048, 'Unexpected Boolean cap population: ' + str(count)
    if not count:
        return 0
    before = dynamic.get_triangle_count()
    _, deleted = u.GeometryScript_MeshEdits.delete_selected_triangles_from_mesh(dynamic, selection)
    assert deleted == count and dynamic.get_triangle_count() == before-count
    return deleted


def _remove_hatch_end_cap(dynamic, component):
    return _remove_box_cap(dynamic, component, 0, CUT_MIN[0])


def _remove_sheet_window(dynamic, component):
    # Open-sheet Boolean output can retain a one-sided window face. Remove
    # only triangles wholly inside the already cut box, preserving its border.
    transform = component.get_world_transform()
    rotation = transform.rotation.to_tuple()
    assert abs(rotation[0]) < 1.e-5 and abs(rotation[2]) < 1.e-5
    assert abs(abs(rotation[1])-.70710678) < 1.e-5 and abs(abs(rotation[3])-.70710678) < 1.e-5
    points = [u.MathLibrary.inverse_transform_location(transform, u.Vector(x,y,z)).to_tuple()
        for x in (CUT_MIN[0]-.02,CUT_MAX[0]+.02)
        for y in (CUT_MIN[1]-.02,CUT_MAX[1]+.02)
        for z in (CUT_MIN[2]-.02,CUT_MAX[2]+.02)]
    box = u.Box(min=u.Vector(*(min(p[i] for p in points) for i in range(3))),
                max=u.Vector(*(max(p[i] for p in points) for i in range(3))))
    _, selection = u.GeometryScript_MeshSelection.select_mesh_elements_in_box(dynamic,
        box, min_num_triangle_points=3)
    _, count = u.GeometryScript_MeshSelection.get_mesh_selection_info(selection)
    before = dynamic.get_triangle_count()
    assert 0 < count < before <= 64, 'Unexpected private backing-sheet topology'
    _, deleted = u.GeometryScript_MeshEdits.delete_selected_triangles_from_mesh(dynamic, selection)
    assert deleted == count and dynamic.get_triangle_count() == before-count
    return deleted


def _cut_component(component, package, cut_min=CUT_MIN, cut_max=CUT_MAX, open_end=False):
    """Subtract only the measured hatch volume; retain source materials/UV overlays."""
    assert not u.EditorAssetLibrary.does_asset_exist(package), 'Preserve existing private geometry: ' + package
    source = component.static_mesh
    materials = _material_paths(source)
    smes = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    source_uvs = smes.get_num_uv_channels(source, 0)
    dynamic = u.DynamicMesh()
    _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        source, dynamic, u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False),
        u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0))
    assert outcome == u.GeometryScriptOutcomePins.SUCCESS
    before = dynamic.get_triangle_count()
    tool = u.DynamicMesh()
    # AppendBox's default origin is its base, so Z is the bottom of the cut.
    u.GeometryScript_Primitives.append_box(tool, u.GeometryScriptPrimitiveOptions(),
        u.Transform(location=u.Vector((cut_min[0]+cut_max[0])/2,
            (cut_min[1]+cut_max[1])/2, cut_min[2])),
        cut_max[0]-cut_min[0], cut_max[1]-cut_min[1], cut_max[2]-cut_min[2])
    u.GeometryScript_MeshBooleans.apply_mesh_boolean(dynamic, component.get_world_transform(),
        tool, u.Transform(), u.GeometryScriptBooleanOperation.SUBTRACT,
        u.GeometryScriptMeshBooleanOptions(simplify_output=False))
    assert dynamic.get_triangle_count() > 0, 'Hatch cut removed an entire backing mesh'
    removed_cap = _remove_hatch_end_cap(dynamic, component) if open_end else 0
    removed_sheet = _remove_sheet_window(dynamic, component) if source.get_path_name() == '/Engine/BasicShapes/Plane.Plane' else 0
    # Duplicate keeps material slots/Nanite/build configuration local to this copy.
    target = u.EditorAssetLibrary.duplicate_asset(source.get_path_name(), package)
    assert target
    _, outcome = u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic, target,
        u.GeometryScriptCopyMeshToAssetOptions(), u.GeometryScriptMeshWriteLOD())
    assert outcome == u.GeometryScriptOutcomePins.SUCCESS
    assert _material_paths(target) == materials, 'Material slots changed during hatch cut'
    assert smes.get_num_uv_channels(target, 0) == source_uvs, 'UV channels lost during hatch cut'
    # Preserve the vendor's Nanite fallback policy; fresh capsule sweeps verify
    # the actual opening. Avoid redundant PostEditChange/rebuild calls.
    if smes.get_simple_collision_count(target):
        smes.remove_collisions(target)
    target.get_editor_property('body_setup').set_editor_property('collision_trace_flag',
                                                               u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    for section in range(target.get_num_sections(0)):
        if not smes.is_section_collision_enabled(target, 0, section):
            smes.enable_section_collision(target, True, 0, section)
    assert u.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False)
    component.set_static_mesh(target)
    return {'source': source.get_path_name(), 'private': target.get_path_name(),
            'triangles_before': before, 'triangles_after': dynamic.get_triangle_count(),
            'removed_artificial_cap_triangles': removed_cap,
            'removed_one_sided_sheet_triangles': removed_sheet,
            'uv_channels': source_uvs, 'materials': materials,
            'uv_method': 'GeometryScript Boolean retains existing overlays; no global unwrap or simplification',
            'sha256': _sha(_file(package))}


def _inspect_cargo_world():
    """Acquire fresh references after loading; never carry source actors into edits."""
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    actors = list(u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors())
    names = {a.get_name(): a for a in actors}
    assert all(name in names for name in CUT_ACTORS)
    assert names[CUT_ACTORS[0]].static_mesh_component.static_mesh.get_name() == 'SM_SpaceShip_Outer_Body2'
    clutter = []
    for actor in actors:
        if actor.get_name() in CUT_ACTORS:
            continue
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            if not c.static_mesh or 'Floor' in c.static_mesh.get_name():
                continue
            center, extent, _ = u.SystemLibrary.get_component_bounds(c)
            # Structural roof beams start at Z711.2, leaving 227cm headroom.
            if _intersects(center, extent, (140, -1250, 484), (650, -1030, 700)):
                if max(extent.x, extent.y, extent.z) > 200:
                    raise RuntimeError('Unexpected large hatch obstruction: ' + actor.get_actor_label())
                parent = actor.get_attach_parent_actor()
                candidate = parent if parent else actor
                if candidate not in clutter:
                    clutter.append(candidate)
    assert 5 <= len(clutter) <= 35, 'Unexpected hatch clutter population'
    return world, actors, names, clutter


def _copy_signature(actors):
    """Compare placed content across SaveAs, excluding regenerated UObject names."""
    def transform(value):
        return [[round(float(n), 4) for n in part.to_tuple()]
                for part in (value.translation, value.rotation, value.scale3d)]

    rows = []
    for actor in actors:
        components = []
        for component in actor.get_components_by_class(u.PrimitiveComponent):
            row = {'class': component.get_class().get_name(),
                   'transform': transform(component.get_world_transform()),
                   'visible': bool(component.get_editor_property('visible')),
                   'hidden': bool(component.get_editor_property('hidden_in_game')),
                   'collision': str(component.get_collision_enabled()),
                   'profile': str(component.get_collision_profile_name()),
                   'pawn': str(component.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN))}
            if isinstance(component, u.StaticMeshComponent):
                row['mesh'] = component.static_mesh.get_path_name() if component.static_mesh else None
                row['materials'] = [m.get_path_name() if m else None for m in component.get_materials()]
            components.append(json.dumps(row, sort_keys=True))
        rows.append(json.dumps({'class': actor.get_class().get_name(),
            'transform': transform(actor.get_actor_transform()),
            'hidden': bool(actor.get_editor_property('hidden')),
            'collision': actor.get_actor_enable_collision(),
            'tags': sorted(str(tag) for tag in actor.tags),
            'components': sorted(components)}, sort_keys=True))
    return sorted(rows)


def prepare(resume_copy=None):
    """Separate guarded cargo-only authoring pass; original and owner maps untouched."""
    root = _root()
    output = root / '.agent/local/StationRefinement/CargoVariant'
    output.mkdir(parents=True, exist_ok=True)
    apply_changes = '-SSApplyStationCargo' in u.SystemLibrary.get_command_line()
    assert '-renderoffscreen' in u.SystemLibrary.get_command_line().lower() or '-nullrhi' in u.SystemLibrary.get_command_line().lower()
    assert not u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
    assert _sha(_file(SOURCE, True)) == SOURCE_HASH
    probe = json.loads((root/'.agent/local/StationRefinement/CargoProbe/probe.json').read_text())
    openings = json.loads((root/'.agent/local/StationRefinement/CargoOpenings/inspection.json').read_text())
    assert probe['status'] == 'PASS_READ_ONLY_DIAGNOSTICS' and probe['protected_files_unchanged']
    assert openings['status'] == 'PASS_INSPECTION_ONLY' and openings['source_unchanged']
    assert len(probe['entry_sweeps']) == 114 and all(q['hit'] for q in probe['entry_sweeps'])
    filename = 'apply.json' if apply_changes else 'dry-run.json'
    assert not (output/filename).exists(), 'Preserve existing cargo receipt'
    if resume_copy:
        assert apply_changes, 'Copy recovery requires explicit apply mode'
        failed_path = Path(resume_copy['failed_receipt'])
        assert _sha(failed_path) == resume_copy['failed_receipt_sha256']
        failed = json.loads(failed_path.read_text())
        assert failed['status'] == 'FAILED' and failed['originals_preserved'] and not failed['cut_meshes']
        assert failed['source'] == SOURCE and failed['level'] == LEVEL and failed['wrapper'] == WRAPPER
        assert len(failed['errors']) == 1 and 'SaveAs did not switch to private world' in failed['errors'][0]
        assert _sha(_file(LEVEL, True)) == resume_copy['private_copy_sha256'], 'Private copy changed since safe failure'
    else:
        assert not u.EditorAssetLibrary.does_asset_exist(LEVEL), 'Preserve an already authored/edited cargo variant'
    assert not u.EditorAssetLibrary.does_asset_exist(WRAPPER), 'Preserve an already authored/edited wrapper'
    for name in CUT_ACTORS:
        assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE + 'SM_DockingHatch_' + name)
    protected = {str(p): _sha(p) for p in (_file(SOURCE, True),
        _file('/Game/CargoShip/Maps/L_Showcase', True),
        _file('/Game/BuildingLibrary/Assembled/Ships/BP_CargoShip_Complete'),
        _file('/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006', True))}
    report = {'apply': apply_changes, 'source': SOURCE, 'level': LEVEL, 'wrapper': WRAPPER,
              'protected_before': protected, 'cut_min': CUT_MIN, 'cut_max': CUT_MAX,
              'entry_floor_cm': FLOOR_Z, 'cut_meshes': [], 'retired_clutter': [],
              'errors': [], 'runtime_traversal_verified': False, 'status': 'PREPARING'}
    level = u.get_editor_subsystem(u.LevelEditorSubsystem)
    try:
        assert level.load_level(SOURCE)
        u.AutomationLibrary.finish_loading_before_screenshot()
        world, actors, names, clutter = _inspect_cargo_world()
        assert world.get_path_name().split('.')[0] == SOURCE
        for name in (*CUT_ACTORS, 'StaticMeshActor_478'):
            source = names[name].static_mesh_component.static_mesh
            file = _file(source.get_path_name())
            protected[str(file)] = _sha(file)
        report['retired_clutter'] = [{'name': a.get_name(), 'label': a.get_actor_label()} for a in clutter]
        if not apply_changes:
            report['status'] = 'PASS_DRY_RUN'
            return report
        source_signature = _copy_signature(actors)
        source_clutter = sorted(a.get_name() for a in clutter)
        # SaveMap can write a copy without changing the editor's current world.
        # Load the derivative explicitly, then discard every source UObject reference.
        if not resume_copy:
            assert u.EditorLoadingAndSavingUtils.save_map(world, LEVEL)
        report['private_copy_sha256'] = _sha(_file(LEVEL, True))
        report['resumed_safe_copy'] = bool(resume_copy)
        assert level.load_level(LEVEL)
        u.AutomationLibrary.finish_loading_before_screenshot()
        world, actors, names, clutter = _inspect_cargo_world()
        assert world.get_path_name().split('.')[0] == LEVEL, 'Private world must be active before edits'
        private_signature = _copy_signature(actors)
        assert private_signature == source_signature, 'Private copy differs from source placed content'
        assert sorted(a.get_name() for a in clutter) == source_clutter
        report['copy_actor_count'] = len(actors)
        report['copy_matches_source'] = True
        report['copy_signature_sha256'] = hashlib.sha256(json.dumps(source_signature).encode()).hexdigest()
        for name in CUT_ACTORS:
            report['cut_meshes'].append(_cut_component(names[name].static_mesh_component,
                PRIVATE + 'SM_DockingHatch_' + name, open_end=name == CUT_ACTORS[0]))
        assert names['StaticMeshActor_478'].static_mesh_component.static_mesh.get_name() == 'SM_Floor_02'
        report['cut_meshes'].append(_cut_component(names['StaticMeshActor_478'].static_mesh_component,
            PRIVATE + 'SM_DockingHatch_Floor', (140, -1250, 483), (710, -1030, 530)))
        sys.path.insert(0, str(root/'Scripts'))
        from StationRefinementSupport import Context
        ctx = Context()
        for actor in clutter:
            ctx.hide(actor)
            for child in actor.get_all_child_actors(include_descendants=True):
                ctx.hide(child)
            if actor.get_name() in ('Bp_outside_light_C_1', 'Bp_little_red_light_C_16'):
                ctx.records.append({'kind': 'remove_private_blueprint_placement', 'name': actor.get_name()})
                assert ctx.eas.destroy_actor(actor), 'Retired Blueprint must not respawn colliding children'
        # Flat 2.2m-wide docking sleeve, slightly above existing uneven floor trim.
        ctx.box('Cargo/Sleeve floor', (420, ENTRY_Y, FLOOR_Z-6), (560, 220, 12), METAL)
        ctx.box('Cargo/Sleeve ceiling', (477, ENTRY_Y, FLOOR_Z+238), (326, 252, 16), DARK)
        for side in (-1, 1):
            ctx.box('Cargo/Sleeve wall ' + str(side), (477, ENTRY_Y+side*119, FLOOR_Z+115),
                    (326, 18, 230), METAL)
            ctx.box('Cargo/Hatch jamb ' + str(side), (595, ENTRY_Y+side*126, FLOOR_Z+118),
                    (34, 30, 236), DARK)
        ctx.box('Cargo/Hatch lintel', (595, ENTRY_Y, FLOOR_Z+238), (34, 282, 22), METAL)
        ctx.light('Cargo/Hatch task light', (565, ENTRY_Y, FLOOR_Z+210), 650, 520,
                  color=(.65, .8, 1), shadows=False)
        assert u.EditorLoadingAndSavingUtils.save_map(world, LEVEL)
        bp = u.BlueprintEditorLibrary.create_blueprint_asset_with_parent(WRAPPER, u.LevelInstance)
        assert bp
        u.BlueprintEditorLibrary.compile_blueprint(bp)
        u.get_default_object(bp.generated_class()).set_editor_property('world_asset', u.load_asset(LEVEL))
        assert u.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
        report.update(level_sha256=_sha(_file(LEVEL, True)), wrapper_sha256=_sha(_file(WRAPPER)),
                      created=ctx.summary(), status='AUTHORED_REQUIRES_RELOAD_AND_WALK')
        return report
    except Exception:
        report['errors'].append(traceback.format_exc())
        report['status'] = 'FAILED'
        raise
    finally:
        level.load_level('/Engine/Maps/Entry')
        report['originals_preserved'] = all(_sha(Path(f)) == value for f, value in protected.items())
        if not report['originals_preserved']:
            report['status'] = 'FAILED'
            report['errors'].append('Protected source bytes changed')
        assert not (output/filename).exists(), 'Preserve existing cargo receipt'
        (output/filename).write_text(json.dumps(report, indent=2), encoding='utf-8')


def repair_hatch():
    """Repair only the measured private cap, regenerated trim and raised floor."""
    root = _root()
    output = root/'.agent/local/StationRefinement/CargoHatchRepair'
    assert not output.exists(), 'Preserve prior hatch repair evidence'
    assert '-SSApplyCargoHatchRepair' in u.SystemLibrary.get_command_line()
    assert '-nullrhi' in u.SystemLibrary.get_command_line().lower() or '-renderoffscreen' in u.SystemLibrary.get_command_line().lower()
    proof_file = root/'.agent/local/StationRefinement/CargoVariant/apply.json'
    proof = json.loads(proof_file.read_text())
    diagnosis = json.loads((root/'.agent/local/StationRefinement/CargoHatchDiagnosis.json').read_text())
    assert proof['status'] == 'AUTHORED_REQUIRES_RELOAD_AND_WALK' and proof['originals_preserved']
    assert diagnosis['status'] == 'PASS_READ_ONLY_DIAGNOSIS' and diagnosis['private_files_preserved']
    assert _sha(_file(LEVEL, True)) == proof['level_sha256']
    assert _sha(_file(WRAPPER)) == proof['wrapper_sha256']
    assert not u.EditorAssetLibrary.does_asset_exist(PRIVATE+'SM_DockingHatch_Floor')
    for row in proof['cut_meshes']:
        assert _sha(_file(row['private'])) == row['sha256']
    protected = {p: _sha(Path(p)) for p in proof['protected_before']}
    for p, expected in proof['protected_before'].items():
        if '/OwnerPreview/' not in p.replace('\\', '/'):
            assert protected[p] == expected, 'Original input changed: ' + p
    protected[str(_file(WRAPPER))] = proof['wrapper_sha256']
    for row in proof['cut_meshes'][1:]:
        protected[str(_file(row['private']))] = row['sha256']
    output.mkdir()
    for file in (_file(LEVEL, True), _file(proof['cut_meshes'][0]['private']), proof_file):
        shutil.copy2(file, output/('before-'+file.name))
    report = {'status': 'PREPARING', 'before_level_sha256': proof['level_sha256'],
              'before_hull_sha256': proof['cut_meshes'][0]['sha256'], 'errors': [],
              'runtime_traversal_verified': False}
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    eas = u.get_editor_subsystem(u.EditorActorSubsystem)
    assert not editor.get_game_world()
    try:
        assert levels.load_level(LEVEL)
        u.AutomationLibrary.finish_loading_before_screenshot()
        world = editor.get_editor_world()
        assert world.get_path_name().split('.')[0] == LEVEL
        names = {a.get_name(): a for a in eas.get_all_level_actors()}
        component = names[CUT_ACTORS[0]].static_mesh_component
        target = component.static_mesh
        assert target.get_path_name() == proof['cut_meshes'][0]['private']
        materials = _material_paths(target)
        smes = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        uvs = smes.get_num_uv_channels(target, 0)
        dynamic = u.DynamicMesh()
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(target, dynamic,
            u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False),
            u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0))
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        report['triangles_before'] = dynamic.get_triangle_count()
        report['cap_triangles_removed'] = _remove_hatch_end_cap(dynamic, component)
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic, target,
            u.GeometryScriptCopyMeshToAssetOptions(), u.GeometryScriptMeshWriteLOD())
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        assert _material_paths(target) == materials and smes.get_num_uv_channels(target, 0) == uvs
        assert u.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False)
        report['triangles_after'] = dynamic.get_triangle_count()
        report['hull_sha256'] = _sha(_file(target.get_path_name()))
        floor = names['StaticMeshActor_478'].static_mesh_component
        assert floor.static_mesh.get_path_name() == '/Game/CargoShip/Meshes/SM_Floor_02.SM_Floor_02'
        floor_source_file = _file(floor.static_mesh.get_path_name())
        protected[str(floor_source_file)] = _sha(floor_source_file)
        report['floor_mesh'] = _cut_component(floor, PRIVATE+'SM_DockingHatch_Floor',
            (140, -1250, 483), (710, -1030, 530))
        report['removed_placements'] = []
        for name in ('Bp_outside_light_C_1', 'Bp_little_red_light_C_16'):
            actor = names[name]
            assert actor.get_editor_property('hidden') and not actor.get_actor_enable_collision()
            report['removed_placements'].append({'name': name, 'label': actor.get_actor_label(),
                'class': actor.get_class().get_path_name(),
                'children': [c.get_name() for c in actor.get_all_child_actors(include_descendants=True)]})
            assert eas.destroy_actor(actor)
        assert u.EditorLoadingAndSavingUtils.save_map(world, LEVEL)
        report['level_sha256'] = _sha(_file(LEVEL, True))
        # Verify regenerated state, not the in-memory edits that failed review1.
        assert levels.load_level('/Engine/Maps/Entry')
        assert levels.load_level(LEVEL)
        u.AutomationLibrary.finish_loading_before_screenshot()
        world = editor.get_editor_world()
        report['floors'] = []
        report['clearance'] = []
        for x in range(140, 681, 20):
            hit = _hit(u.SystemLibrary.line_trace_single_by_profile(world, u.Vector(x, ENTRY_Y, 590),
                u.Vector(x, ENTRY_Y, 430), 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
            report['floors'].append({'x': x, 'hit': hit})
        for half_height in (75, 88):
            for y in (-1190, -1140, -1090):
                hit = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
                    u.Vector(680, y, FLOOR_Z+half_height+2), u.Vector(140, y, FLOOR_Z+half_height+2),
                    34, half_height, 'Pawn', False, [], u.DrawDebugTrace.NONE, True))
                report['clearance'].append({'y': y, 'half_height': half_height, 'hit': hit})
        report['supported_hatch_floor'] = all(q['hit'] and not q['hit']['initial_overlap'] and
            abs(q['hit']['point'][2]-FLOOR_Z) < 1 and q['hit']['normal'][2] > .99 for q in report['floors'])
        report['standing_capsules_clear'] = all(q['hit'] is None for q in report['clearance'])
        assert report['supported_hatch_floor'] and report['standing_capsules_clear'], 'Fresh hatch physical checks failed'
        report['status'] = 'REPAIRED_REQUIRES_RENDERED_AND_RUNTIME_REVIEW'
        return report
    except Exception:
        report['status'] = 'FAILED'
        report['errors'].append(traceback.format_exc())
        raise
    finally:
        levels.load_level('/Engine/Maps/Entry')
        report['originals_preserved'] = all(_sha(Path(p)) == expected for p, expected in protected.items())
        if not report['originals_preserved']:
            report['status'] = 'FAILED'
            report['errors'].append('Protected input changed')
        (output/'repair.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


def finish_hatch():
    """Open the measured backing sheet and line the sleeve with owned framed panels."""
    root = _root()
    output = root/'.agent/local/StationRefinement/CargoHatchFinish'
    assert not output.exists(), 'Preserve previous finishing evidence'
    assert '-SSApplyCargoHatchFinish' in u.SystemLibrary.get_command_line()
    assert '-nullrhi' in u.SystemLibrary.get_command_line().lower() or '-renderoffscreen' in u.SystemLibrary.get_command_line().lower()
    proof = json.loads((root/'.agent/local/StationRefinement/CargoVariant/apply.json').read_text())
    previous_path = root/'.agent/local/StationRefinement/CargoHatchRepair/repair.json'
    previous = json.loads(previous_path.read_text())
    diagnosis = json.loads((root/'.agent/local/StationRefinement/CargoOuterBoundary.json').read_text())
    assert previous['status'] == 'REPAIRED_REQUIRES_RENDERED_AND_RUNTIME_REVIEW' and previous['originals_preserved']
    assert diagnosis['status'] == 'PASS_READ_ONLY_DIAGNOSIS' and diagnosis['private_map_preserved']
    hull_path = proof['cut_meshes'][0]['private']
    plane_path = proof['cut_meshes'][2]['private']
    outward = [q for q in diagnosis['rays'] if q['start_x'] == 140]
    assert len(outward) == 9 and all(q['hit'] and q['hit']['mesh'] == plane_path and
        abs(q['hit']['point'][0]-460.29467) < .1 for q in outward), 'Backing-sheet hypothesis not confirmed'
    assert _sha(_file(LEVEL, True)) == previous['level_sha256']
    assert _sha(_file(hull_path)) == previous['hull_sha256']
    assert _sha(_file(WRAPPER)) == proof['wrapper_sha256']
    assert _sha(_file(plane_path)) == proof['cut_meshes'][2]['sha256']
    assert _sha(_file(previous['floor_mesh']['private'])) == previous['floor_mesh']['sha256']
    protected = {p: _sha(Path(p)) for p in proof['protected_before']}
    for p, value in proof['protected_before'].items():
        if '/OwnerPreview/' not in p.replace('\\', '/'):
            assert protected[p] == value
    for path in (WRAPPER, previous['floor_mesh']['private'], PANEL,
                 proof['cut_meshes'][1]['private']):
        protected[str(_file(path))] = _sha(_file(path))
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    editor = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    assert not editor.get_game_world()
    output.mkdir()
    for file in (_file(LEVEL, True), _file(hull_path), _file(plane_path), previous_path):
        shutil.copy2(file, output/('before-'+file.name))
    report = {'status': 'PREPARING', 'errors': [], 'runtime_traversal_verified': False,
              'before_level_sha256': previous['level_sha256'], 'before_hull_sha256': previous['hull_sha256']}
    try:
        assert levels.load_level(LEVEL)
        u.AutomationLibrary.finish_loading_before_screenshot()
        sys.path.insert(0, str(root/'Scripts'))
        from StationRefinementSupport import Context
        ctx = Context()
        names = {a.get_name(): a for a in ctx.actors}
        component = names[CUT_ACTORS[0]].static_mesh_component
        target = component.static_mesh
        assert target.get_path_name() == hull_path
        dynamic = u.DynamicMesh()
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(target, dynamic,
            u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False),
            u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0))
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        report['triangles_before'] = dynamic.get_triangle_count()
        report['removed_caps'] = [{'axis': 1, 'plane_cm': value,
            'triangles': _remove_box_cap(dynamic, component, 1, value)}
            for value in (CUT_MIN[1], CUT_MAX[1])]
        materials = _material_paths(target)
        smes = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        uvs = smes.get_num_uv_channels(target, 0)
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic, target,
            u.GeometryScriptCopyMeshToAssetOptions(), u.GeometryScriptMeshWriteLOD())
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        assert _material_paths(target) == materials and smes.get_num_uv_channels(target, 0) == uvs
        assert u.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False)
        report['triangles_after'] = dynamic.get_triangle_count()
        report['hull_sha256'] = _sha(_file(hull_path))
        plane_component = names[CUT_ACTORS[2]].static_mesh_component
        plane = plane_component.static_mesh
        assert plane.get_path_name() == plane_path
        sheet = u.DynamicMesh()
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(plane, sheet,
            u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False),
            u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0))
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        plane_materials = _material_paths(plane)
        plane_uvs = smes.get_num_uv_channels(plane, 0)
        report['removed_sheet_triangles'] = _remove_sheet_window(sheet, plane_component)
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(sheet, plane,
            u.GeometryScriptCopyMeshToAssetOptions(), u.GeometryScriptMeshWriteLOD())
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        assert _material_paths(plane) == plane_materials and smes.get_num_uv_channels(plane, 0) == plane_uvs
        assert u.EditorAssetLibrary.save_loaded_asset(plane, only_if_is_dirty=False)
        report['plane_sha256'] = _sha(_file(plane_path))
        mesh = ctx.asset(PANEL)
        bounds = mesh.get_bounds()
        report['lining'] = []
        for side in (-1, 1):
            for index in range(2):
                actor = ctx.raw('Cargo/Finished wall %d %d' % (side, index), PANEL,
                    (0, 0, 0), (90, side*90, 0),
                    (230/(2*bounds.box_extent.x), 285/(2*bounds.box_extent.y), 1))
                center, extent, _ = u.SystemLibrary.get_component_bounds(actor.static_mesh_component)
                desired = u.Vector(140+(index+.5)*285, ENTRY_Y+side*(110+extent.y), FLOOR_Z+115)
                actor.set_actor_location(actor.get_actor_location()+desired-center, False, False)
                center, extent, _ = u.SystemLibrary.get_component_bounds(actor.static_mesh_component)
                clear = side*(center.y-ENTRY_Y)-extent.y
                assert abs(clear-110) < .05
                report['lining'].append({'label': actor.get_actor_label(), 'asset': PANEL,
                    'center': list(center.to_tuple()), 'extent': list(extent.to_tuple()), 'inner_edge_cm': clear})
            backing = [a for a in ctx.actors if a.get_actor_label() == 'Refine/Cargo/Sleeve wall '+str(side)]
            assert len(backing) == 1
            # Put the original plain support behind the full framed-panel depth.
            backing[0].set_actor_location(u.Vector(425, ENTRY_Y+side*(111+2*extent.y+9), FLOOR_Z+115), False, False)
            backing[0].set_actor_scale3d(u.Vector(5.7, .18, 2.3))
        world = editor.get_editor_world()
        assert world.get_path_name().split('.')[0] == LEVEL
        assert u.EditorLoadingAndSavingUtils.save_map(world, LEVEL)
        report['level_sha256'] = _sha(_file(LEVEL, True))
        assert levels.load_level('/Engine/Maps/Entry') and levels.load_level(LEVEL)
        u.AutomationLibrary.finish_loading_before_screenshot()
        world = editor.get_editor_world()
        report['floors'], report['clearance'] = [], []
        for x in range(140, 681, 20):
            h = _hit(u.SystemLibrary.line_trace_single_by_profile(world, u.Vector(x,ENTRY_Y,590),
                u.Vector(x,ENTRY_Y,430),'Pawn',False,[],u.DrawDebugTrace.NONE,True))
            report['floors'].append({'x': x, 'hit': h})
        for start, end in ((140, 800), (800, 140)):
            for half in (75, 88):
                for y in (-1190, -1140, -1090):
                    h = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
                        u.Vector(start,y,FLOOR_Z+half+2),u.Vector(end,y,FLOOR_Z+half+2),
                        34,half,'Pawn',False,[],u.DrawDebugTrace.NONE,True))
                    report['clearance'].append({'start_x':start,'end_x':end,'y':y,'half_height':half,'hit':h})
        report['supported_hatch_floor'] = all(q['hit'] and not q['hit']['initial_overlap'] and
            abs(q['hit']['point'][2]-FLOOR_Z)<1 and q['hit']['normal'][2]>.99 for q in report['floors'])
        report['bidirectional_capsules_clear'] = all(q['hit'] is None for q in report['clearance'])
        assert report['supported_hatch_floor'] and report['bidirectional_capsules_clear'], 'Fresh bidirectional hatch check failed'
        report['status'] = 'FINISHED_REQUIRES_RENDERED_AND_RUNTIME_REVIEW'
        return report
    except Exception:
        report['status'] = 'FAILED'
        report['errors'].append(traceback.format_exc())
        raise
    finally:
        levels.load_level('/Engine/Maps/Entry')
        report['originals_preserved'] = all(_sha(Path(p)) == value for p,value in protected.items())
        if not report['originals_preserved']:
            report['status'] = 'FAILED'
            report['errors'].append('Protected input changed')
        (output/'finish.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


def connect_apron(ctx):
    """Join the actual curved berth floor to the already placed gangway.

    The original rectangular-bounds inference left 650cm unsupported. Native
    Pawn rays locate the real circular edge near Y=-4450; overlap that surface
    visibly and physically instead of moving the walking fixture past the gap.
    This edits placed actors only. The caller owns backup, map save and receipt.
    """
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    assert world and world.get_path_name().split('.')[0] == '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
    actors = ctx.actors + ctx.created
    assert not any(a.get_actor_label().startswith('Refine/CargoPort/Apron ') for a in actors)
    deck = [a for a in actors if a.get_actor_label() == 'Refine/CargoPort/Continuous deck support']
    assert len(deck) == 1, 'Expected the existing measured cargo gangway'

    def floor(x, y):
        return _hit(u.SystemLibrary.line_trace_single_by_profile(world,
            u.Vector(x,y,100),u.Vector(x,y,-150),'Pawn',False,[],u.DrawDebugTrace.NONE,True))

    before = []
    for y, label in ((-3900, 'Ground/Visitor berth 02'), (-4100, 'Ground/Visitor berth 02'),
                     (-5200, 'Refine/CargoPort/Continuous deck support')):
        hit = floor(-1860, y)
        assert hit and hit['label'] == label and abs(hit['point'][2]) < .1 and hit['normal'][2] > .99
        before.append({'xy':[-1860,y],'floor':hit})
    assert floor(-1860,-4700) is None, 'The diagnosed gap changed; inspect before adding the extension'
    x, start_y, end_y, top = -1860., -4100., -5100., 2.
    length = start_y-end_y
    bounds = ctx.asset(PANEL).get_bounds()
    for index in range(3):
        segment = length/3
        ctx.grounded('CargoPort/Apron deck %02d' % index, PANEL,
            (x,start_y-(index+.5)*segment), floor=top-2*bounds.box_extent.z,
            scale=(300/(2*bounds.box_extent.x),segment/(2*bounds.box_extent.y),1), collision=False)
    # Ten centimetres of collision overlap under the existing deck avoids a
    # seam. Visible plates end at the old deck, with a measured 2cm step down.
    support = ctx.box('CargoPort/Apron continuous support',
        (x,(start_y+end_y-10)/2,top-9),(300,length+10,18),DARK)
    support.set_actor_hidden_in_game(True)
    support.set_is_temporarily_hidden_in_editor(True)
    for side in (-1,1):
        edge = x+side*155
        ctx.box('CargoPort/Apron rail '+str(side),(edge,(start_y+end_y)/2,105),(10,length,10),METAL)
        ctx.box('CargoPort/Apron toe guard '+str(side),(edge,(start_y+end_y)/2,12),(10,length,24),DARK)
        for index, y in enumerate((start_y,(start_y+end_y)/2)):
            ctx.box('CargoPort/Apron post %d %d' % (side,index),(edge,y,52),(12,12,104),METAL)
    ctx.light('CargoPort/Apron guidance light',(x,-4600,185),650,500,color=(.68,.8,1),shadows=False)
    signs = [a for a in actors if a.get_actor_label() == 'Refine/CargoPort/Boarding sign']
    assert len(signs) == 1
    ctx.move(signs[0],(x,start_y+80,210))
    u.AutomationLibrary.finish_loading_before_screenshot()
    floors, sweeps = [], []
    for y in range(-5200,-4099,25):
        for lateral in (-100,0,100):
            hit = floor(x+lateral,y)
            assert hit and hit['normal'][2] > .99 and -.1 <= hit['point'][2] <= 2.1, 'Unsupported apron surface'
            floors.append({'xy':[x+lateral,y],'floor':hit})
    for a,b in ((-3900.,-5200.),(-5200.,-3900.)):
        hit = _hit(u.SystemLibrary.capsule_trace_single_by_profile(world,
            u.Vector(x,a,top+78),u.Vector(x,b,top+78),34,75,'Pawn',False,[],u.DrawDebugTrace.NONE,True))
        sweeps.append({'from_y':a,'to_y':b,'radius':34,'half_height':75,'hit':hit})
        assert not hit, 'Connected apron capsule path is obstructed'
    result = {'route_world':[[x,-3900,0],[x,-4050,0],[x,-4200,top],[x,-5000,top],
                            [x,-5200,0],[x,-7300,0],[x,-7860,0],[x,-8000,-6.3]],
              'existing_floor_start':before[0], 'before':before, 'floors':floors, 'clearance':sweeps,
              'extension_width_cm':300,'extension_length_cm':length,'surface_step_cm':top,
              'runtime_traversal_verified':False,
              'limits':'Native floor/capsule checks only; actual out-and-back CharacterMovement and rendered join remain required.'}
    ctx.records.append({'kind':'cargo_apron_connection',**result})
    return result


def apply(ctx):
    """Place prepared complete ship and a continuous apron-to-hatch gangway."""
    root = _root()
    receipt = json.loads((root/'.agent/local/StationRefinement/CargoVariant/apply.json').read_text())
    assert receipt['status'] == 'AUTHORED_REQUIRES_RELOAD_AND_WALK' and receipt['originals_preserved']
    repair_path = root/'.agent/local/StationRefinement/CargoHatchRepair/repair.json'
    repair = json.loads(repair_path.read_text()) if repair_path.exists() else None
    finish_path = root/'.agent/local/StationRefinement/CargoHatchFinish/finish.json'
    finish = json.loads(finish_path.read_text()) if finish_path.exists() else None
    if finish:
        assert finish['status'] == 'FINISHED_REQUIRES_RENDERED_AND_RUNTIME_REVIEW' and finish['originals_preserved']
        assert finish['bidirectional_capsules_clear'] and finish['supported_hatch_floor']
        assert _sha(_file(PRIVATE+'SM_DockingHatch_'+CUT_ACTORS[0])) == finish['hull_sha256']
        assert _sha(_file(PRIVATE+'SM_DockingHatch_'+CUT_ACTORS[2])) == finish['plane_sha256']
    if repair:
        assert repair['status'] == 'REPAIRED_REQUIRES_RENDERED_AND_RUNTIME_REVIEW' and repair['originals_preserved']
        if not finish:
            assert _sha(_file(PRIVATE+'SM_DockingHatch_'+CUT_ACTORS[0])) == repair['hull_sha256']
        assert _sha(_file(repair['floor_mesh']['private'])) == repair['floor_mesh']['sha256']
    assert _sha(_file(LEVEL, True)) == (finish or repair or receipt)['level_sha256']
    assert _sha(_file(WRAPPER)) == receipt['wrapper_sha256']
    assert not any(a.get_actor_label().startswith('Refine/CargoPort/') for a in ctx.actors)
    actor = ctx.raw('CargoPort/Complete docked cargo', WRAPPER, POSITION, (0, 90, 0))
    # Yaw90 maps private local-Y to minus world-X, local-X to world-Y.
    entry_x = POSITION[0] - ENTRY_Y
    start_y, end_y = -5100., POSITION[1] + 700.
    length = start_y - end_y
    assert 2000 <= length <= 2600 and entry_x == -1860
    panel_mesh = ctx.asset(PANEL)
    bounds = panel_mesh.get_bounds()
    for index in range(6):
        segment = length/6
        center_y = start_y - (index+.5)*segment
        scale = (300/(2*bounds.box_extent.x), segment/(2*bounds.box_extent.y), 1)
        panel = ctx.grounded('CargoPort/Gangway deck %02d' % index, PANEL,
            (entry_x, center_y), floor=-2*bounds.box_extent.z, scale=scale)
        # Native tile top is exactly zero; an invisible continuous simple floor
        # below it makes seams independent of the decorative mesh's collision.
        panel.set_actor_enable_collision(False)
    support = ctx.box('CargoPort/Continuous deck support',
        (entry_x, (start_y+end_y)/2, -9), (300, length, 18), DARK)
    support.set_actor_hidden_in_game(True)
    support.set_is_temporarily_hidden_in_editor(True)
    for side in (-1, 1):
        x = entry_x + side*155
        ctx.box('CargoPort/Rail ' + str(side), (x, (start_y+end_y)/2, 105),
                (10, length, 10), METAL)
        ctx.box('CargoPort/Toe guard ' + str(side), (x, (start_y+end_y)/2, 12),
                (10, length, 24), DARK)
        for index in range(7):
            y = start_y - index*length/6
            ctx.box('CargoPort/Post %d %d' % (side, index), (x, y, 52), (12, 12, 104), METAL)
    ctx.text('CargoPort/Boarding sign', 'CARGO BERTH\nCREW ACCESS',
             (entry_x, start_y+80, 210), 90, size=27)
    for index, y in enumerate((start_y-220, (start_y+end_y)/2, end_y+220)):
        ctx.light('CargoPort/Guidance light %d' % index, (entry_x, y, 185), 650, 500,
                  color=(.68, .8, 1), shadows=False)
    connection = connect_apron(ctx)
    result = {'level': LEVEL, 'wrapper': WRAPPER, 'location': POSITION, 'yaw': 90, 'scale': 1,
              'hatch_local_y': ENTRY_Y, 'gangway_width_cm': 300, 'gangway_length_cm': length,
              'route_world': connection['route_world'], 'apron_connection':connection,
              'runtime_traversal_verified': False,
              'doors': 'Existing internal gate behavior unchanged; new docking sleeve is deliberately open',
              'source_asset_originals_preserved': True}
    ctx.records.append({'kind': 'cargo_docking_assembly', **result})
    return result


if __name__ == '__main__':
    try:
        result = prepare()
        u.log('STATION_CARGO_PREPARE ' + result['status'])
    except Exception:
        u.log_error(traceback.format_exc())
    finally:
        u.SystemLibrary.quit_editor()
