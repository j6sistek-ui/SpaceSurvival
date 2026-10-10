"""Repair owner slab overlaps in private geometry; quiet entrance backing only."""
import unreal as u

PRIVATE = '/Game/OutpostSandbox/StationRefinement/Geometry/'
FLOOR_LABELS = ('Owner platform/SM_floor_module_01',
                'Owner platform/SM_floor_module_01.001',
                'Owner platform/SM_floor_module_01.002')
# Preserve the existing recessed stair/corridor/apartment by cutting support slabs
# around those exact protected bounds, never by removing their walkable floors.
HOME_CUTS = ((4890, 6150, 1820, 2130), (5740, 6150, 2110, 4300),
             (5740, 8630, 3430, 5950))


def subtract_box(mesh, world, rect):
    x0, x1, y0, y1 = rect
    tool = u.DynamicMesh()
    u.GeometryScript_Primitives.append_box(tool, u.GeometryScriptPrimitiveOptions(),
        u.Transform(location=u.Vector((x0+x1)/2, (y0+y1)/2, -1200)),
        x1-x0, y1-y0, 1600)
    u.GeometryScript_MeshBooleans.apply_mesh_boolean(mesh, world, tool, u.Transform(),
        u.GeometryScriptBooleanOperation.SUBTRACT, u.GeometryScriptMeshBooleanOptions())


def apply(ctx):
    floors = {a.get_actor_label(): a for a in ctx.actors if a.get_actor_label() in FLOOR_LABELS}
    assert len(floors) == 3, 'Owner floor identity changed; inspect before editing'
    covering = floors[FLOOR_LABELS[2]]
    cover_center, cover_extent = covering.get_actor_bounds(False)
    records = []
    smes = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    for i, label in enumerate(FLOOR_LABELS):
        actor = floors[label]
        component = actor.static_mesh_component
        source = component.static_mesh
        assert source.get_path_name().endswith('/SM_floor_module_01.SM_floor_module_01')
        package = PRIVATE + 'SM_OwnerDeck_NoOverlap_' + str(i)
        assert not u.EditorAssetLibrary.does_asset_exist(package), 'Private floor already authored: ' + package
        dynamic = u.DynamicMesh()
        _, outcome = u.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
            source, dynamic, u.GeometryScriptCopyMeshFromAssetOptions(apply_build_settings=False),
            u.GeometryScriptMeshReadLOD(lod_type=u.GeometryScriptLODType.SOURCE_MODEL, lod_index=0))
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS
        before = dynamic.get_triangle_count()
        world = component.get_world_transform()
        if i == 1:
            # Same-height overlap spans about 46.7m by 92.3m.
            # Use actual native cover bounds plus 0.05cm to avoid coincident seams.
            subtract_box(dynamic, world, (cover_center.x-cover_extent.x-.05,
                cover_center.x+cover_extent.x+.05, cover_center.y-cover_extent.y-.05,
                cover_center.y+cover_extent.y+.05))
        for rect in HOME_CUTS:
            subtract_box(dynamic, world, rect)
        assert dynamic.get_triangle_count() > 0, 'Floor cut removed the entire platform'
        target, outcome = u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
            dynamic, package, u.GeometryScriptCreateNewStaticMeshAssetOptions(enable_nanite=False))
        assert outcome == u.GeometryScriptOutcomePins.SUCCESS and target
        for material_index in range(component.get_num_materials()):
            target.set_material(material_index, component.get_material(material_index))
        smes.remove_collisions(target)
        body = target.get_editor_property('body_setup')
        body.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        for section in range(target.get_num_sections(0)):
            smes.enable_section_collision(target, True, 0, section)
        assert u.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False)
        component.set_static_mesh(target)
        records.append({'actor': label, 'source': source.get_path_name(),
                        'private': target.get_path_name(), 'triangles_before': before,
                        'triangles_after': dynamic.get_triangle_count(),
                        'transform_preserved': True, 'source_uvs_preserved_outside_cuts': True})
    quiet = ctx.asset('/Game/OutpostSandbox/Materials/M_OutpostGraphite.M_OutpostGraphite')
    for actor in ctx.actors:
        label = actor.get_actor_label()
        if label.startswith('EntranceKit/Upper facade/') and any(
                term in label for term in ('Storage infill', 'Crown transition', 'Central seam', 'Service rail')):
            for c in actor.get_components_by_class(u.StaticMeshComponent):
                previous = [c.get_material(i).get_path_name() if c.get_material(i) else None
                            for i in range(c.get_num_materials())]
                for slot in range(c.get_num_materials()):
                    c.set_material(slot, quiet)
                ctx.records.append({'kind':'quiet_backing', 'actor':label,'materials_before':previous})
        if label.startswith('HologramWalls/Arrival') and '/Frame' in label:
            for c in actor.get_components_by_class(u.StaticMeshComponent):
                # Only the frame body. Retain digital glass and edge materials.
                previous = c.get_material(0)
                ctx.records.append({'kind':'quiet_frame','actor':label,
                                    'before':previous.get_path_name() if previous else None})
                c.set_material(0, quiet)
        if label == 'Environment/Cold starlight':
            actor.get_component_by_class(u.DirectionalLightComponent).set_editor_property('forward_shading_priority', 1)
    ctx.records.extend(records)
    return {'floor_variants':records,'protected_basement_cuts':HOME_CUTS,
            'quiet_backing':'Placed component overrides only; original materials unchanged'}


def repair_foundation_collision(ctx):
    """Match the enlarged hollow ring's query collision to its existing surface.

    FoundationProbe compared both paths at 46 basement samples: the simple hull
    covered the ring's empty middle, while complex queries reached HomeHub.
    Keep the owner geometry, scale, UVs and placed materials exactly as authored.
    """
    import hashlib
    from pathlib import Path
    matches = [a for a in ctx.actors if a.get_actor_label() == 'Owner platform/SM_Arco_Tubo']
    assert len(matches) == 1, 'Owner ring identity changed'
    actor = matches[0]
    component = actor.static_mesh_component
    source = component.static_mesh
    assert source.get_path_name() == '/Game/SciFiCorridor/Meshes/SM_Arco_Tubo.SM_Arco_Tubo'
    source_file = Path(u.Paths.project_dir()).resolve() / 'Content/SciFiCorridor/Meshes/SM_Arco_Tubo.uasset'
    before_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
    materials = list(component.get_materials())
    transform = actor.get_actor_transform()
    package = PRIVATE + 'SM_OwnerRing_AccurateCollision'
    assert not u.EditorAssetLibrary.does_asset_exist(package), 'Inspect existing private ring before replay'
    target = u.EditorAssetLibrary.duplicate_asset(source.get_path_name(), package)
    assert target
    smes = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    smes.remove_collisions(target)
    target.get_editor_property('body_setup').set_editor_property(
        'collision_trace_flag', u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    for section in range(target.get_num_sections(0)):
        smes.enable_section_collision(target, True, 0, section)
    assert smes.get_number_verts(source,0) == smes.get_number_verts(target,0)
    assert smes.get_num_uv_channels(source,0) == smes.get_num_uv_channels(target,0)
    assert u.EditorAssetLibrary.save_loaded_asset(target, only_if_is_dirty=False)
    component.set_static_mesh(target)
    for slot,material in enumerate(materials):
        component.set_material(slot,material)
    assert actor.get_actor_transform() == transform
    assert list(component.get_materials()) == materials
    assert hashlib.sha256(source_file.read_bytes()).hexdigest() == before_hash
    result = {'source':source.get_path_name(),'private':target.get_path_name(),
        'source_sha256_preserved':before_hash,'vertices':smes.get_number_verts(target,0),
        'owner_geometry_pose_and_materials_preserved':True,
        'collision':'Existing ring triangles, removing the simple hull across its empty middle',
        'runtime_walking_verified':False}
    ctx.records.append({'kind':'foundation_collision',**result})
    return result
