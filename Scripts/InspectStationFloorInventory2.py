"""Read-only actual station floor survey; the lead owns map/PIE/receipt lifecycle.

Candidates are not an author whitelist. Record existing geometry, material slot
roles and inheritance before selecting floor-only white derivatives. No save,
map load, actor or component write, native process launch or top-level Unreal.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'.agent/local/StationRefinement'
TARGET = '/Game/OutpostSandbox/OwnerPreview/L_OwnerPlatformPreview_20261006'
MAP = ROOT/('Content/'+TARGET[6:]+'.umap')
MAP_SHA = 'c1f62aed453362a1eacc20faeb6f9d589bae5e9f42f03053a28dd3e2c5f1371c'
FLOOR = BASE/'StationOperationsFloorProbe1.json'
FLOOR_SHA = 'e8481055d10aa1f11c896b663f95bfabdb76e8096f98d231c98f6c505b1c604a'
P4 = '/Game/P1toP5_Bundle/P4_Genesis_Vol1/Meshes/SM_UniversalPanel400X200_V2.SM_UniversalPanel400X200_V2'
SOURCE_RECIPES = ('AuthorOutpostSandbox.py', 'OutpostQuietPromenade.py', 'OutpostBerthDetails.py',
                  'OutpostObservation.py', 'OutpostInteriorAssemblies.py', 'AuthorHomeApartment.py',
                  'AuthorOutpostHomeHub.py', 'HomeAnnexConnector.py', 'RefineStationCargo.py',
                  'RefineStationSurfaces.py', 'OutpostSurfaceFinish.py', 'PreviewStationOperationsFloors.py')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(value):
    return hashlib.sha256(Path(value).read_bytes()).hexdigest()


def path(obj):
    return obj.get_path_name() if obj else None


def transform(value):
    return {key: list(part.to_tuple()) for key, part in
            (('location', value.translation), ('rotation', value.rotation), ('scale', value.scale3d))}


def candidates(label, mesh):
    """Survey candidates only. No automatically authorized material whitelist."""
    reasons = []
    low, name = label.lower(), mesh.rsplit('.', 1)[-1].lower()
    if any(term in name for term in ('floor', 'deck', 'ramp', 'stair', 'tread')):
        reasons.append('native mesh name identifies floor/ramp/stair candidate')
    if any(term in low for term in ('/deck', '/foot deck', '/floor', 'quietpromenade/', 'gangway deck', 'apron deck')):
        reasons.append('source-author floor/deck label')
    if label.startswith('Observation/') and '/Panel ' in label:
        reasons.append('observation source deck panel; geometry/height must distinguish roof')
    if label.startswith('Owner platform/') and 'Arco_Tubo' in mesh:
        reasons.append('saved private ring walkable foundation; mixed structure must be reviewed')
    if label in ('Atrium/Deck', 'Player berth/Deck', 'Visitor berth 02/Deck', 'Visitor berth 03/Deck', 'Cargo/Sleeve floor'):
        reasons.append('exact source-authored walkable deck')
    if mesh == P4:
        reasons.append('P4 plate reused for floors and walls/roof; not an automatic floor assignment')
    return reasons


def native_api_preflight(u):
    """Resolve only the exact installed C++ identity before any map load.

    Python acronym spelling differs from the C++ GetAllTriangleMaterialIDs.
    Normalize underscores/case only; never call a guessed alternative/fallback.
    The lead wrapper can record this serializable result while still in Entry.
    """
    library = u.GeometryScript_Materials
    canonical = 'getalltrianglematerialids'
    matches = [name for name in dir(library) if name.replace('_', '').lower() == canonical
               and callable(getattr(library, name, None))]
    registered = [name for name in dir(library) if 'material' in name.lower()
                  and callable(getattr(library, name, None))]
    require(len(matches) == 1,
            'Require exactly one registered GetAllTriangleMaterialIDs export; matches='+str(matches)+
            '; registered material callables='+str(registered))
    name = matches[0]
    require(callable(getattr(u.GeometryScript_List, 'convert_index_list_to_array', None)),
            'Registered ConvertIndexListToArray export is missing')
    return {'all_triangle_material_ids': {'cpp_identity': 'GetAllTriangleMaterialIDs',
            'python_name': name, 'normalized_name': canonical,
            'doc': str(getattr(library, name).__doc__), 'callable': True},
            'convert_index_list_to_array': {'python_name': 'convert_index_list_to_array', 'callable': True},
            'fallback_calls_allowed': False}


def collect(world, actors, u):
    """Inspect already-loaded editor actors before PIE; return guarded source hashes."""
    require(world.get_path_name().split('.')[0] == TARGET and sha(MAP) == MAP_SHA and sha(FLOOR) == FLOOR_SHA,
            'Require exact current saved station and preserved native floor proof')
    previous = json.loads(FLOOR.read_text())
    require(previous['success'] and previous['preservation_pass'] and previous['read_only'] and
            previous['scene_unchanged'] and previous['map_sha256'] == MAP_SHA, 'Require preserved FloorProbe1')
    protected = dict(previous['files_after'])
    protected.update({str(ROOT/'Scripts'/name): sha(ROOT/'Scripts'/name) for name in SOURCE_RECIPES})
    protected.update({str(FLOOR): FLOOR_SHA, str(Path(__file__).resolve()): sha(__file__)})
    require(all(Path(p).is_file() and sha(p) == digest for p, digest in protected.items()),
            'Protected native floor/source/map input changed')
    report = {'success': False, 'read_only': True, 'saved': False, 'map_sha256': MAP_SHA,
              'floor_probe_sha256': FLOOR_SHA, 'helper_sha256': sha(__file__),
              'candidates': [], 'excluded_hidden': [], 'render_component_count': 0,
              'meshes': {}, 'materials': {}, 'master_graphs': {},
              'limits': ['Candidate names alone do not authorize material changes; final exact whitelist needs review.',
                         'Upward areas/Z bands expose combined floor/structure meshes; preserve all geometry and collision.',
                         'No canonical map, packaged build, owner acceptance or performance inference.']}

    def protect(obj):
        package = path(obj).split('.')[0]
        if package.startswith('/Engine/'):
            return
        require(package.startswith('/Game/') and ':' not in package, 'Unexpected floor dependency')
        file = ROOT/('Content/'+package[6:]+'.uasset')
        protected.setdefault(str(file), sha(file))
    eas = u.get_editor_subsystem(u.EditorActorSubsystem)
    require({path(a) for a in actors} == {path(a) for a in eas.get_all_level_actors()},
            'The supplied actor inventory is incomplete or stale')
    sys.path.insert(0, str(ROOT/'Scripts'))
    from RefineStationOperationsDisplays import _state
    from RefineStationSocialSeatedCrew import _geometry
    from PreviewStationOperationsFloors import _parameters, _graph
    actors = list(eas.get_all_level_actors())
    before = {a.get_path_name(): _state(a, u) for a in actors}
    report['actor_count'] = len(actors)
    meshes, materials = {}, {}
    for actor in actors:
        label = actor.get_actor_label()
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.static_mesh
            if not mesh:
                continue
            report['render_component_count'] += 1
            reasons = candidates(label, path(mesh))
            if not reasons:
                continue
            visible = (not actor.get_editor_property('hidden') and
                       component.is_visible() and not component.get_editor_property('hidden_in_game'))
            row = {'label': label, 'actor': path(actor), 'component': path(component), 'class': component.get_class().get_name(),
                   'candidate_reasons': reasons, 'tags': list(map(str, actor.tags)), 'mesh': path(mesh),
                   'actor_transform': transform(actor.get_actor_transform()),
                   'world_transform': transform(component.get_world_transform()),
                   'relative_transform': transform(component.get_relative_transform()),
                   'materials': list(map(path, component.get_materials())),
                   'collision': str(component.get_collision_enabled()), 'collision_profile': str(component.get_collision_profile_name()),
                   'visible': visible, 'local_up_world': list(component.get_up_vector().to_tuple())}
            origin, extent, radius = u.SystemLibrary.get_component_bounds(component)
            row['bounds'] = {'minimum': list((origin-extent).to_tuple()), 'maximum': list((origin+extent).to_tuple()),
                             'center': list(origin.to_tuple()), 'extent': list(extent.to_tuple())}
            if isinstance(component, u.InstancedStaticMeshComponent):
                row['instance_count'] = component.get_instance_count()
                require(row['instance_count'] <= 4000, 'Unbounded candidate floor instances')
                row['instance_world_transforms'] = [transform(component.get_instance_transform(i, world_space=True))
                                                    for i in range(row['instance_count'])]
            if visible:
                report['candidates'].append(row)
                meshes[path(mesh)] = mesh
                materials.update({path(m): m for m in component.get_materials() if m})
            else:
                report['excluded_hidden'].append(row)
    require(84 == len([r for r in report['candidates'] if r['label'].startswith('Operations/Deck ')]),
            'Current exact84 T floors missing from survey')
    require(0 < len(meshes) <= 120 and 0 < len(materials) <= 250, 'Survey escaped bounded floor candidate scope')
    edit = u.MaterialEditingLibrary
    masters = {}
    for name, material in materials.items():
        current, lineage, seen = material, [], set()
        value = _parameters(material, u) if isinstance(material, u.MaterialInstanceConstant) else None
        if value:
            for texture in value['textures'].values():
                if texture:
                    protect(u.load_asset(texture))
        while current:
            require(path(current) not in seen, 'Cyclic source floor material lineage')
            seen.add(path(current)); protect(current)
            lineage.append({'asset': path(current), 'class': current.get_class().get_name()})
            if not isinstance(current, u.MaterialInstanceConstant):
                break
            current = current.get_editor_property('parent')
        require(isinstance(current, u.Material), 'Native floor candidate master missing')
        masters[path(current)] = current
        report['materials'][name] = {'lineage': lineage, 'parameters': value}
    for name, master in masters.items():
        graph = _graph(master, u)
        require(len(graph['nodes']) <= 2500, 'Unbounded source floor graph')
        for node in edit.get_material_expressions(master):
            kind = node.get_class().get_name()
            row = next(r for r in graph['nodes'] if r['node'] == path(node))
            if kind == 'MaterialExpressionConstant':
                row['constant'] = float(node.get_editor_property('r'))
            elif kind in ('MaterialExpressionConstant3Vector', 'MaterialExpressionConstant4Vector'):
                row['constant'] = [float(getattr(node.get_editor_property('constant'), c)) for c in ('r', 'g', 'b', 'a')]
            if row.get('texture'):
                protect(u.load_asset(row['texture']))
            if row.get('function'):
                protect(u.load_asset(row['function']))
        report['master_graphs'][name] = graph
    report['api_preflight'] = native_api_preflight(u)
    bulk_name = report['api_preflight']['all_triangle_material_ids']['python_name']
    bulk_material_ids = getattr(u.GeometryScript_Materials, bulk_name)
    triangle_budget = 0
    for name, mesh in meshes.items():
        protect(mesh)
        bounds = mesh.get_bounds()
        if name == P4:
            data = previous['native_mesh']['geometry']; ids = previous['native_mesh']['triangle_material_ids']
        else:
            dynamic, data = _geometry(mesh, False, u)
            _, material_list, valid = bulk_material_ids(dynamic)
            require(valid, 'Native floor source has no triangle material IDs '+name)
            ids = list(u.GeometryScript_List.convert_index_list_to_array(material_list))
        require(len(ids) == len(data['triangles']) and len(ids) <= 2500000 and
                all(0 <= n < len(mesh.get_editor_property('static_materials')) for n in ids),
                'Invalid/sparse actual native material triangles '+name)
        triangle_budget += len(ids)
        require(triangle_budget <= 10000000, 'Native floor survey triangle budget exceeded')
        slots = {str(i): {'total_area_cm2': 0., 'upward_area_cm2': 0., 'all_triangles': 0,
                         'upward_triangles': 0, 'upward_z_bands_cm': {}}
                 for i in range(len(mesh.get_editor_property('static_materials')))}
        for face, slot in zip(data['triangles'], ids):
            points = [data['vertices'][i] for i in face]
            a = [points[1][i]-points[0][i] for i in range(3)]
            b = [points[2][i]-points[0][i] for i in range(3)]
            cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
            length = math.sqrt(sum(v*v for v in cross)); info = slots[str(slot)]
            info['all_triangles'] += 1; info['total_area_cm2'] += length*.5
            if length > 1.e-8 and cross[2]/length > .9:
                info['upward_triangles'] += 1; info['upward_area_cm2'] += length*.5
                band = str(round(sum(p[2] for p in points)/3./5.)*5)
                info['upward_z_bands_cm'][band] = info['upward_z_bands_cm'].get(band, 0.)+length*.5
        report['meshes'][name] = {'native_origin_cm': list(bounds.origin.to_tuple()),
            'native_extent_cm': list(bounds.box_extent.to_tuple()), 'triangle_count': len(ids),
            'native_materials': [path(s.material_interface) for s in mesh.get_editor_property('static_materials')],
            'slot_geometry': slots, 'geometry_sha256': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()}
    require(before == {a.get_path_name(): _state(a, u) for a in eas.get_all_level_actors()},
            'Read-only floor inventory altered station actor state')
    report['scene_unchanged'] = True
    report['success'] = True
    report['source_sha256'] = protected
    require(all(sha(p) == digest for p, digest in protected.items()), 'Native survey changed a protected floor source')
    return report
