"""Two native open ceiling coffers; lead owns map transaction and fresh renders.

No vendor/material/light edits. Geometry checks use actual source triangles, so
the coffer's whole bounds may overlap the lamps while its open center stays clear.
"""
import hashlib
import math
import re
from pathlib import Path

from OutpostGeometryUtils import mesh_union
from RefineStationSocialSeatedCrew import _geometry, _one

MAP = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
MESH = '/Game/CyberPunkBarAssetSet01/StaticMeshes/SM_BarCeilingAsset03'
MATERIAL = '/Game/CyberPunkBarAssetSet01/Materials/M_BarCeilingMat02'
ORIGIN = (-3.6629486083984375, 1.3104248046875, 18.42432403564453)
EXTENT = (181.7845001220703, 270.1405334472656, 31.7786865234375)
PREFIX = 'Refine/LoungeCeiling/Coffer '
CEILING_Z = 397.57


def _sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _triangle_box(points, center, extent):
    """Separating-axis test: triangle normal, box axes and nine edge cross axes."""
    p = [_sub(value, center) for value in points]
    edges = [_sub(p[(i+1) % 3], p[i]) for i in range(3)]
    axes = [(1., 0., 0.), (0., 1., 0.), (0., 0., 1.)]
    axes += [_cross(edges[0], edges[1])]
    axes += [_cross(edge, axis) for edge in edges for axis in axes[:3]]
    for axis in axes:
        if sum(v*v for v in axis) < 1.e-16:
            continue
        radius = sum(abs(axis[i])*extent[i] for i in range(3))
        values = [sum(point[i]*axis[i] for i in range(3)) for point in p]
        if min(values) > radius+1.e-7 or max(values) < -radius-1.e-7:
            return False
    return True


def _snapshot(actor, u):
    transform = actor.get_actor_transform()
    materials = {c.get_path_name(): [m.get_path_name() if m else None for m in c.get_materials()]
                 for c in actor.get_components_by_class(u.MeshComponent)}
    lights = {c.get_path_name(): (float(c.intensity), bool(c.is_visible()))
              for c in actor.get_components_by_class(u.LightComponent)}
    return {'location': tuple(transform.translation.to_tuple()),
            'rotation': tuple(transform.rotation.to_tuple()), 'scale': tuple(transform.scale3d.to_tuple()),
            'hidden': bool(actor.get_editor_property('hidden')),
            'materials': materials, 'lights': lights}


def apply(ctx, expected_map_sha256):
    """Stage two unsaved purchased modules after all geometry/preservation guards."""
    import unreal as u
    root = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if not re.fullmatch('[0-9a-f]{64}', expected_map_sha256):
        raise ValueError('Require the exact current map SHA256 from the lead receipt')
    map_file = root / ('Content/' + MAP[6:] + '.umap')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split('.')[0] != MAP or sha(map_file) != expected_map_sha256:
        raise RuntimeError('Lounge coffer helper targets only the guarded owner preview')
    actors = list(ctx.eas.get_all_level_actors())
    if any(a.get_actor_label().startswith(PREFIX) for a in actors):
        raise RuntimeError('Preserve an existing coffer pass')
    mesh = ctx.asset(MESH)
    bounds = mesh.get_bounds()
    if (math.dist(bounds.origin.to_tuple(), ORIGIN) > .02 or
            math.dist(bounds.box_extent.to_tuple(), EXTENT) > .02):
        raise RuntimeError('Native coffer bounds differ from OrbitPoolProbeWrapper1')
    materials = [slot.material_interface for slot in mesh.get_editor_property('static_materials')]
    if len(materials) != 1 or not materials[0] or materials[0].get_path_name().split('.')[0] != MATERIAL:
        raise RuntimeError('Coffer native material differs from the inspected purchased mesh')
    sources = {p: sha(root / ('Content/' + p[6:] + '.uasset')) for p in (MESH, MATERIAL)}
    _, geometry = _geometry(mesh, False, u)
    triangles = [[geometry['vertices'][index] for index in face] for face in geometry['triangles']]
    if not triangles or len(triangles) > 20000:
        raise RuntimeError('Unexpected coffer source geometry')
    before = {a.get_path_name(): _snapshot(a, u) for a in actors}
    ceiling_actors = [a for a in actors if a.get_actor_label().startswith(
        ('QuietCeiling/Engineering/Panel ', 'Engineering/Ceiling panel'))]
    candidates = []
    for index, y in enumerate((-3000., -3600.), 1):
        housing = _one(actors, 'Refine/SocialAtmosphereFollowup/Aisle %d/Housing' % index)
        hangers = [_one(actors, 'Refine/SocialAtmosphereFollowup/Aisle %d/Hanger %d' % (index, side))
                   for side in (-1, 1)]
        supports = []
        for actor in ceiling_actors:
            if actor.get_editor_property('hidden'):
                continue
            center, extent = mesh_union(actor)
            if abs(center.x-4200.) <= extent.x+.01 and abs(center.y-y) <= extent.y+.01:
                bottom = center.z-extent.z
                if abs(bottom-CEILING_Z) < .1:
                    supports.append({'actor': actor.get_actor_label(), 'underside_z': bottom})
        if not supports:
            raise RuntimeError('No actual reviewed ceiling support above coffer %d' % index)
        top = min(s['underside_z'] for s in supports)
        location = (4200.-ORIGIN[0], y-ORIGIN[1], top-ORIGIN[2]-EXTENT[2])
        if top-2*EXTENT[2] < 330.:
            raise RuntimeError('Coffer violates overhead clearance')
        clearances = []
        for fixture in [housing, *hangers]:
            c, e = mesh_union(fixture)
            center = _sub(c.to_tuple(), location)
            expanded = tuple(v+3. for v in e.to_tuple())
            hits = [i for i, triangle in enumerate(triangles) if _triangle_box(triangle, center, expanded)]
            if hits:
                raise RuntimeError('Coffer solid geometry intersects fixture/hanger clearance: '
                                   + fixture.get_actor_label() + ' triangles=' + str(hits[:10]))
            clearances.append({'actor': fixture.get_actor_label(), 'expanded_bounds_cm': list(expanded),
                               'triangle_intersections': 0, 'clearance_padding_cm': 3.})
        candidates.append({'index': index, 'location': location, 'top_z': top,
                           'bottom_z': top-2*EXTENT[2], 'supports': supports,
                           'actual_triangle_clearances': clearances})
    created = []
    for row in candidates:
        actor = ctx.raw('LoungeCeiling/Coffer %d' % row['index'], mesh, row['location'], collision=False)
        center, extent = mesh_union(actor)
        if abs(center.z+extent.z-row['top_z']) > .02 or abs(center.z-extent.z-row['bottom_z']) > .02:
            raise RuntimeError('Native placed coffer did not align to the roof underside')
        component = actor.static_mesh_component
        component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        if component.get_material(0) != materials[0]:
            raise RuntimeError('Coffer lost its original material')
        row.update(actor=actor.get_path_name(), center=list(center.to_tuple()), extent=list(extent.to_tuple()))
        created.append(row)
    after = {a.get_path_name(): _snapshot(a, u) for a in actors}
    if before != after:
        raise RuntimeError('Coffer pass altered an existing actor pose, material, visibility or light')
    for package, digest in sources.items():
        if sha(root / ('Content/' + package[6:] + '.uasset')) != digest:
            raise RuntimeError('Coffer pass changed a purchased source asset')
    return {'module': 'lounge_native_coffers', 'dirty_assets': [], 'created': created,
            'native_mesh': MESH, 'native_material': MATERIAL, 'native_triangle_count': len(triangles),
            'source_hashes_preserved': sources, 'protected_existing_actors': len(before),
            'lighting_changed': False, 'collision': 'Disabled on both overhead decorative modules',
            'limits': 'Unsaved composition only; actual material emission and whole-room quality await native render.'}
