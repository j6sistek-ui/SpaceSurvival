"""Collision-bearing derivatives of the meshes the space scenery places.

Both vendor packs ship every mesh authored CTF_UseComplexAsSimple. That flag makes the
engine ignore the mesh's own simple primitives and fall back to render triangles, and an
instanced static mesh component cannot use complex collision at all, so the scenery clutter
is unhittable no matter what its component says.

The meshes do in fact carry a convex hull already; the flag was simply telling the engine
not to use it. So this mostly flips the flag on a private copy, and only generates hulls
for a mesh that genuinely has none. Vendor assets are never modified in place.

Note for anyone extending this: StaticMeshEditorSubsystem.get_simple_collision_count does
NOT count convex elements, only boxes, spheres and capsules. Using it as the success check
reports zero on a mesh that is fully collidable. Count the aggregate geometry instead.
"""
import unreal as u
from pathlib import Path
import json

KIT = '/Game/Megastructure_Scifi_World/Meshes/'
ROCK = '/Game/Asteroid_Library/Static_Meshes/'
WRECK = '/Game/SpaceSurvival/Licensed/OrbitalWreck/'
ASSEMBLY = '/Game/SpaceSurvival/Licensed/SpatialAssemblies/'
STATION = '/Game/SpaceSurvival/Licensed/StationVisualPass/Meshes/'
SOLID = '/Game/SpaceSurvival/Licensed/SolidScenery'
LIB = u.EditorAssetLibrary

# Mirrors the placements and clutter candidates in AuthorSpaceAreas.py. A mesh absent here
# stays decorative, which is a silent hole, so the receipt records exactly what was covered.
SOURCES = (
    [ROCK + n for n in ('SM_Asteroid_Barren_1', 'SM_Asteroid_Barren_2', 'SM_Asteroid_Barren_3',
                        'SM_AsteroidBarren_4')] +
    [ROCK + f'SM_AsteroidMineral_{i}' for i in range(1, 5)] +
    [ROCK + f'SM_AsteroidFragment_{i}' for i in range(1, 5)] +
    [KIT + f'Pillar/SM_architecture_module_{n:02}' for n in (2, 3, 4, 7, 12)] +
    [KIT + f'Pannels/SM_Pannel_part_{n:02}' for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15)] +
    [KIT + f'Floor/SM_floor_module_{n:02}' for n in (1, 2, 3, 4)] +
    [KIT + 'Arch/SM_arch_01', KIT + 'Arch/SM_arch_03', KIT + 'Arch/SM_triangle_arch'] +
    [WRECK + 'BrokenArc/SM_BrokenArc', WRECK + 'RingFragment/SM_RingFragment', WRECK + 'KitBeam/SM_KitBeam'] +
    [ASSEMBLY + n for n in ('SM_BrokenHullSpine', 'SM_ButtressedChunk', 'SM_FragmentedArch')] +
    [STATION + 'SM_Station3Exterior']
)

HULLS, HULL_VERTS, PRECISION = 8, 24, 100000


def primitives(mesh):
    """Every simple-collision element the body actually carries, convex hulls included."""
    agg = mesh.get_editor_property('body_setup').get_editor_property('agg_geom')
    total = 0
    for field in ('convex_elems', 'box_elems', 'sphere_elems', 'sphyl_elems'):
        try:
            total += len(agg.get_editor_property(field))
        except Exception:
            pass
    return total


def main():
    editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    LIB.make_directory(SOLID)
    receipt = {'solid': [], 'missing': [], 'unchanged': [], 'generated': []}
    for source in SOURCES:
        if not LIB.does_asset_exist(source):
            receipt['missing'].append(source)
            continue
        target = f'{SOLID}/{source.rsplit("/", 1)[1]}'
        mesh = LIB.load_asset(target) if LIB.does_asset_exist(target) else LIB.duplicate_asset(source, target)
        assert isinstance(mesh, u.StaticMesh), target
        body = mesh.get_editor_property('body_setup')
        # Rebuilding collision that is already correct changes the GUID and dirties the binary on
        # every run, so only touch a mesh whose flag is wrong or that genuinely has no primitives.
        changed = False
        if body.get_editor_property('collision_trace_flag') != u.CollisionTraceFlag.CTF_USE_DEFAULT:
            body.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_DEFAULT)
            changed = True
        if primitives(mesh) == 0:
            # Both of these report success while producing nothing on some meshes, so each attempt is
            # judged by what it actually left behind rather than by what it returned.
            route = None
            for attempt, run in (('convex', lambda: editor.set_convex_decomposition_collisions(
                                      mesh, HULLS, HULL_VERTS, PRECISION)),
                                 ('ndop18', lambda: editor.add_simple_collisions(
                                      mesh, u.ScriptCollisionShapeType.NDOP18)),
                                 ('box', lambda: editor.add_simple_collisions(
                                      mesh, u.ScriptCollisionShapeType.BOX))):
                try:
                    run()
                except Exception as exc:
                    u.log_warning(f'{target}: {attempt} raised {exc}')
                    continue
                if primitives(mesh) > 0:
                    route = attempt
                    break
            assert route, f'No collision route produced primitives for {target}'
            receipt['generated'].append({'target': target, 'route': route})
            changed = True
        count = primitives(mesh)
        # The whole point is that usable primitives exist. A silent zero would ship a field that is
        # query-only against nothing, which is exactly the state this pass exists to end.
        assert count > 0, f'No simple collision on {target}'
        if changed:
            assert LIB.save_loaded_asset(mesh, only_if_is_dirty=False), target
            receipt['solid'].append({'source': source, 'target': target, 'primitives': count})
        else:
            receipt['unchanged'].append(target)
    assert not receipt['missing'], f'Scenery meshes not found: {receipt["missing"]}'
    assert receipt['solid'] or receipt['unchanged'], 'No scenery meshes were processed'
    probe = f'{SOLID}/PROBE_Barren_1'
    if LIB.does_asset_exist(probe):
        LIB.delete_asset(probe)
    out = Path(u.Paths.project_dir(), 'Artifacts/SolidScenery')
    out.mkdir(parents=True, exist_ok=True)
    (out / 'SolidScenery.json').write_text(json.dumps(receipt, indent=2))
    u.log(f'SOLID_SCENERY_AUTHORED {len(receipt["solid"])} written, {len(receipt["unchanged"])} already correct, '
          f'{len(receipt["generated"])} needed new hulls')


if __name__ == '__main__':
    main()
