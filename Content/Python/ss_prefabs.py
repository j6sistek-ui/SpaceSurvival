"""SpaceSurvival prefab library and Blender live link, editor side.

Loaded automatically by Content/Python/init_unreal.py when the editor starts. Four jobs:

  1. The catalogue. Every static mesh the project owns, classified into categories (Doors, Walls,
     Floors, Pipes & Cables, Consoles & Screens, ...), with bounds and a glTF proxy for Blender.
     Written to Artifacts/PrefabLibrary/catalog.json by build_catalog().
  2. Prefabs. A prefab is a JSON recipe in Prefabs/<Category>/<Name>.json: parts (asset, transform
     relative to the prefab origin, optional material overrides) and point lights. save_prefab()
     writes one from selected actors; place_prefab() spawns one into whatever level is open.
     The schema is the interior recipe schema the station already uses, so the same file can feed
     either path.
  3. The live link. Blender (Tools/SSLiveLink) talks to this module over the engine's own Python
     remote execution. apply_link() creates or moves actors keyed by a link id; pull_selection()
     hands the selected actors back so Blender can mirror them.
  4. The visual browser. Artifacts/PrefabLibrary/index.html is the catalogue and the prefabs as one
     offline page of thumbnails; build_gallery() writes it with Tools/SSLiveLink/build_gallery.py and
     open_gallery() shows it in the web browser. The thumbnails themselves come from Blender
     (Tools/SSLiveLink/render_thumbnails.py); build_catalog() keeps the ones already on disk.

Everything is plain Python over the unreal module; no C++ and no UMG, so it works in a commandlet
as well as in the open editor. Menus are registered under "SS Prefabs" in the main menu bar.
"""
from pathlib import Path
import importlib.util
import json
import math
import os
import re
import time
import uuid
import webbrowser

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
PREFABS = ROOT / 'Prefabs'
LIBRARY = ROOT / 'Artifacts' / 'PrefabLibrary'
CATALOG = LIBRARY / 'catalog.json'
PROXIES = LIBRARY / 'proxies'
GALLERY = LIBRARY / 'index.html'                                  # the visual browser page
GALLERY_TOOL = ROOT / 'Tools' / 'SSLiveLink' / 'build_gallery.py'   # stdlib only; writes GALLERY
TAG_LINK = 'SSLink:'       # actor tag carrying the Blender link id
TAG_PREFAB = 'SSPrefab:'   # actor tag carrying the prefab it was placed from
OWNER = 'SSPrefabs'        # tool-menu owner name, so the menus can be rebuilt

# ---------------------------------------------------------------- classification
CATEGORIES = [
    ('Doors', ('door', 'gate', 'hatch', 'airlock', 'portal')),
    ('Walls', ('wall', 'bulkhead', 'partition', 'groove', 'pannel', 'window', 'divider')),
    ('Floors', ('floor', 'deck', 'grate', 'catwalk', 'walkway', 'platform', 'tile')),
    ('Ceilings', ('ceil', 'celling', 'roof')),
    ('Stairs & Rails', ('stair', 'ladder', 'rail', 'ramp')),
    ('Pillars & Frames', ('pilar', 'pillar', 'column', 'beam', 'frame', 'truss', 'girder', 'support', 'arch', 'arco')),
    ('Pipes & Cables', ('pipe', 'tube', 'cable', 'wire', 'hose', 'vent', 'duct', 'conduit')),
    ('Consoles & Screens', ('console', 'terminal', 'monitor', 'screen', 'computer', 'keyboard', 'holo', 'display', 'kiosk', 'panel',
                            'laptop', 'keypad', 'scanner', 'remotecontrol')),
    ('Planets & Sky', ('planet', 'skysphere', 'skybox', 'starfield', 'nebula')),
    ('Characters & Robots', ('robot', 'drone', 'companion', 'mech', 'trooper')),
    ('Game Objects', ('pickup', 'candidate', 'field', 'gravityring', 'stormring', 'servicearm', 'overdrive')),
    ('Lights', ('light', 'lamp', 'neon', 'led')),
    ('Furniture', ('chair', 'table', 'bed', 'bench', 'desk', 'sofa', 'seat', 'locker', 'cabinet', 'shelf', 'rack')),
    ('Containers', ('crate', 'box', 'container', 'barrel', 'canister', 'tank', 'cargo', 'case', 'pallet')),
    ('Machines', ('generator', 'engine', 'machine', 'reactor', 'server', 'turbine', 'pump', 'fan', 'battery', 'device')),
    ('Signs & Banners', ('sign', 'flag', 'banner', 'poster', 'decal', 'logo')),
    ('Ship Parts', ('ship', 'spacecraft', 'wing', 'thruster', 'cockpit', 'fuselage', 'acorn', 'havolk', 'upgrade', 'utility',
                    'swift', 'flanker', 'pursuer', 'ludo')),
    ('Station Exterior', ('station', 'solar', 'antenna', 'dish', 'hangar', 'dock', 'exterior', 'the_corner')),
    ('Asteroids & Debris', ('asteroid', 'rock', 'debris', 'fragment', 'mineral')),
    ('Wreckage', ('broken', 'chunk', 'wreck', 'spine', 'buttress', 'kitbeam', 'ringfragment', 'arc')),
    ('Props', ('prop', 'bottle', 'card', 'tool', 'gun', 'weapon', 'grenade', 'gradnade', 'helmet', 'book', 'cup', 'hook')),
]
# The types above the categories, which is how the owner reaches for things: "all building materials",
# "all decorations". Every category belongs to exactly one; anything unlisted is Misc.
GROUPS = [
    ('Building', ('Walls', 'Floors', 'Ceilings', 'Doors', 'Stairs & Rails', 'Pillars & Frames')),
    ('Decoration', ('Props', 'Furniture', 'Containers', 'Signs & Banners', 'Pipes & Cables', 'Machines',
                    'Consoles & Screens', 'Lights')),
    ('Exterior & Space', ('Station Exterior', 'Asteroids & Debris', 'Wreckage', 'Planets & Sky')),
    ('Ships', ('Ship Parts',)),
    ('Characters & Robots', ('Characters & Robots',)),
    ('Game Objects', ('Game Objects',)),
]


def group_of(category):
    for group, categories in GROUPS:
        if category in categories:
            return group
    return 'Misc'


# Packs that are effects demos or engine samples, not set dressing.
EXCLUDED_PACKS = ('NiagaraExamples', 'RPGEnvironmentVFX', 'PyroVFX', 'Sci_Fi_Weapons_VFX_AIO', 'Vefects', 'CosmicMaterial',
                  'Defect', 'SciFITrooper_Man_03')


def _log(msg):
    u.log(f'SSPrefabs: {msg}')


def pack_of(asset_path):
    parts = asset_path.split('/')
    if len(parts) > 3 and parts[2] in ('StarterBundle', 'SpaceSurvival'):
        return parts[2] + '/' + parts[3]
    return parts[2] if len(parts) > 2 else 'Game'


def classify(asset_path):
    name = asset_path.split('/')[-1].split('.')[0].lower()
    pack = pack_of(asset_path).lower()
    words = re.sub(r'[^a-z0-9]+', ' ', name).split()
    for category, keys in CATEGORIES:
        for key in keys:
            if any(w.startswith(key) or w.endswith(key) for w in words) or key in name:
                return category
    if 'asteroid' in pack:
        return 'Asteroids & Debris'
    if 'spacecraft' in pack or 'ship' in pack:
        return 'Ship Parts'
    return 'Misc'


# ---------------------------------------------------------------- catalogue
def _static_meshes():
    ar = u.AssetRegistryHelpers.get_asset_registry()
    flt = u.ARFilter(class_paths=[u.TopLevelAssetPath('/Script/Engine', 'StaticMesh')], package_paths=['/Game'],
                     recursive_paths=True)
    rows = []
    for data in ar.get_assets(flt):
        path = str(data.package_name) + '.' + str(data.asset_name)
        pack = pack_of(path)
        if any(pack.startswith(x) for x in EXCLUDED_PACKS):
            continue
        rows.append(path)
    return sorted(rows)


def _gltf_options():
    opts = u.GLTFExportOptions()
    for k, v in {'export_uniform_scale': 0.01, 'bake_material_inputs': u.GLTFMaterialBakeMode.DISABLED,
                 'export_proxy_materials': False, 'export_vertex_colors': False, 'default_level_of_detail': 0,
                 'export_source_model': False, 'texture_image_format': u.GLTFTextureImageFormat.NONE,
                 'export_lightmaps': False, 'export_material_variants': u.GLTFMaterialVariantMode.NONE}.items():
        try:
            opts.set_editor_property(k, v)
        except Exception as e:  # an option missing in this engine version is not fatal
            _log(f'glTF option {k} skipped: {e}')
    return opts


def export_proxy(mesh, out_path):
    """Write a glTF proxy of one mesh; returns True on success. Needs the GLTFExporter plugin."""
    if not hasattr(u, 'GLTFExporter'):
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = u.GLTFExporter.export_to_gltf(mesh, str(out_path), _gltf_options(), set())
    ok = result[0] if isinstance(result, tuple) else bool(result)
    return bool(ok) and out_path.exists()


def thumb_rel(proxy_rel):
    """The thumbnail contract shared with Tools/SSLiveLink/render_thumbnails.py: thumbs/<proxy path, .png for .glb>."""
    return 'thumbs/' + proxy_rel[:-4] + '.png' if proxy_rel.endswith('.glb') else None


def export_thumbnail(asset, out_path, size=256):
    """Write the engine's own textured preview of an asset; False when the editor module is not loaded.

    The Blender renderer can only draw a proxy, and proxies carry no textures: a white wall panel looks like
    every other white wall panel. USSThumbnailLibrary (SpaceSurvivalEditor) draws what the Content Browser
    shows, so a part can be recognised.
    """
    library = getattr(u, 'SSThumbnailLibrary', None)
    if library is None:
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(library.export_asset_thumbnail(asset, str(out_path), size)) and out_path.exists()


def build_catalog(export_proxies=True, limit=0, engine_thumbnails=True, force_thumbnails=False):
    """Scan every owned static mesh, classify it, measure it and (optionally) export a proxy and a thumbnail.

    Returns the catalogue dict. Proxies already on disk are kept, so reruns are cheap. The catalogue is
    written from scratch, so whatever sits on disk is put back on every row: "proxy" whenever the GLB
    exists, whether or not this run exports any, and "thumb" whenever a thumbnail exists. Thumbnails the
    engine has drawn are kept ("thumb_source": "unreal"); a clay one from Blender is replaced the first time
    the engine can draw the real thing.
    """
    LIBRARY.mkdir(parents=True, exist_ok=True)
    previous = {m['asset']: m for m in (load_catalog() or {}).get('meshes', [])}
    paths = _static_meshes()
    if limit:
        paths = paths[:limit]
    meshes, failed = [], []
    t0 = time.time()
    for i, path in enumerate(paths):
        mesh = u.load_asset(path)
        if not isinstance(mesh, u.StaticMesh):
            continue
        b = mesh.get_bounds()
        name = path.split('.')[-1]
        pack = pack_of(path)
        category = classify(path)
        row = {'asset': path, 'name': name, 'pack': pack, 'group': group_of(category), 'category': category,
               'origin': [b.origin.x, b.origin.y, b.origin.z], 'extent': [b.box_extent.x, b.box_extent.y, b.box_extent.z],
               'radius': b.sphere_radius, 'triangles': mesh.get_num_triangles(0),
               'materials': [s.material_interface.get_path_name() if s.material_interface else '' for s in mesh.static_materials]}
        # Mirror the package path under the pack, so two meshes with one name in different folders
        # (the scenery meshes and their solid derivatives, for one) do not share a proxy.
        rel = path.split('.')[0][len('/Game/' + pack) + 1:]
        proxy = PROXIES / pack.replace('/', '_') / (rel + '.glb')
        if export_proxies and not proxy.exists():
            try:
                if not export_proxy(mesh, proxy):
                    failed.append(path)
            except Exception as e:
                failed.append(path)
                _log(f'proxy failed for {path}: {e}')
        # The row says what is on disk, not what this run did: a rebuild without proxies still lists the
        # GLBs an earlier run exported, and every rebuild keeps the thumbnails the renderer has written.
        # Same rule as the renderer's own pass, so the two writers agree: no proxy, no thumb.
        if proxy.exists():
            row['proxy'] = str(proxy.relative_to(LIBRARY)).replace('\\', '/')
            thumb = thumb_rel(row['proxy'])
            source = previous.get(path, {}).get('thumb_source', 'blender')
            if thumb and engine_thumbnails and (force_thumbnails or source != 'unreal' or not (LIBRARY / thumb).exists()):
                try:
                    if export_thumbnail(mesh, LIBRARY / thumb):
                        source = 'unreal'
                except Exception as e:  # a part without a picture is still a part
                    _log(f'thumbnail failed for {path}: {e}')
            if thumb and (LIBRARY / thumb).exists():
                row['thumb'] = thumb
                row['thumb_source'] = source
        meshes.append(row)
        if i % 50 == 0:
            _log(f'catalogued {i + 1}/{len(paths)} ({time.time() - t0:.0f}s)')
    categories, groups = {}, {}
    for m in meshes:
        categories[m['category']] = categories.get(m['category'], 0) + 1
        groups[m['group']] = groups.get(m['group'], 0) + 1
    catalog = {'schema_version': 1, 'generated': time.strftime('%Y-%m-%d %H:%M:%S'), 'engine': u.SystemLibrary.get_engine_version(),
               'units': 'cm; proxies are glTF in metres', 'groups': dict(sorted(groups.items())),
               'group_categories': {g: list(c) for g, c in GROUPS}, 'categories': dict(sorted(categories.items())),
               'proxies_failed': failed, 'meshes': meshes}
    CATALOG.write_text(json.dumps(catalog, indent=1), encoding='utf-8')
    _log(f'catalogue: {len(meshes)} meshes, {len(categories)} categories, {sum(1 for m in meshes if "proxy" in m)} proxies, '
         f'{sum(1 for m in meshes if "thumb" in m)} thumbnails, {len(failed)} proxies failed -> {CATALOG}')
    return catalog


def load_catalog():
    if not CATALOG.exists():
        return None
    return json.loads(CATALOG.read_text(encoding='utf-8'))


# ---------------------------------------------------------------- visual browser
def build_gallery():
    """Write Artifacts/PrefabLibrary/index.html from the catalogue, the thumbnails and the prefabs.

    The page builder is Tools/SSLiveLink/build_gallery.py, shared with the Blender add-on. It is loaded
    from its file on every call (Tools/ is not on the editor's script path, and an edit to the tool
    should not need an editor restart) and returns the counts it wrote: cards, categories, prefabs, path.
    """
    if not GALLERY_TOOL.exists():
        raise RuntimeError(f'missing {GALLERY_TOOL}')
    spec = importlib.util.spec_from_file_location('ss_build_gallery', str(GALLERY_TOOL))
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    result = tool.build(ROOT)
    _log(f'visual browser: {result}')
    return result


def open_gallery():
    """Show the visual browser in the web browser, rebuilt first so it matches the catalogue and prefabs.

    Building takes a fraction of a second. If it fails and an older page exists, that page still opens
    and the failure is logged; with no page at all the error reaches the caller.
    """
    try:
        build_gallery()
    except Exception as e:
        if not GALLERY.exists():
            raise
        u.log_warning(f'SSPrefabs: visual browser not rebuilt, showing the last page ({e})')
    if not webbrowser.open(GALLERY.resolve().as_uri()):
        os.startfile(str(GALLERY))
    return GALLERY


def _rebuild_catalog(export_proxies):
    """Menu action: rebuild the catalogue, then everything that reads it (the visual browser page, the menus)."""
    build_catalog(export_proxies)
    try:
        build_gallery()
    except Exception as e:  # the catalogue is what was asked for; a stale page is a warning, not a failure
        u.log_warning(f'SSPrefabs: visual browser not rebuilt ({e})')
    register_menus()


# ---------------------------------------------------------------- transforms
def matrix_rows(transform):
    """A transform as four rows (UE row-vector convention), JSON-friendly."""
    m = u.MathLibrary.conv_transform_to_matrix(transform)
    rows = []
    for plane in (m.x_plane, m.y_plane, m.z_plane, m.w_plane):
        rows.append([plane.x, plane.y, plane.z, plane.w])
    return rows


def transform_from_rows(rows):
    planes = [u.Plane(*[float(v) for v in r]) for r in rows]
    return u.MathLibrary.conv_matrix_to_transform(u.Matrix(*planes))


def compose(local, parent):
    """local then parent: the world transform of something authored relative to parent."""
    return u.MathLibrary.compose_transforms(local, parent)


def relative(world, parent):
    return u.MathLibrary.make_relative_transform(world, parent)


def transform_from_part(part):
    """A recipe part's transform: either location/rotation/scale or a 4x4 matrix."""
    if 'matrix' in part:
        return transform_from_rows(part['matrix'])
    loc = part.get('location', [0, 0, 0])
    rot = part.get('rotation', [0, 0, 0])   # pitch, yaw, roll as the interior recipe orders them
    scl = part.get('scale', [1, 1, 1])
    if not isinstance(scl, (list, tuple)):
        scl = [scl, scl, scl]
    # unreal.Rotator's positional order is (roll, pitch, yaw); the recipe orders pitch, yaw, roll.
    return u.Transform(u.Vector(*loc), u.Rotator(roll=rot[2], pitch=rot[0], yaw=rot[1]), u.Vector(*scl))


# ---------------------------------------------------------------- actors
def _eas():
    return u.get_editor_subsystem(u.EditorActorSubsystem)


def _world():
    return u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()


def _tag_value(actor, prefix):
    for t in actor.tags:
        s = str(t)
        if s.startswith(prefix):
            return s[len(prefix):]
    return None


def _set_tag(actor, prefix, value):
    tags = [t for t in actor.tags if not str(t).startswith(prefix)]
    tags.append(u.Name(prefix + value))
    actor.tags = tags


def spawn_mesh(asset, transform, label=None, folder=None, materials=None):
    mesh = u.load_asset(asset)
    if not isinstance(mesh, u.StaticMesh):
        raise ValueError(f'not a static mesh: {asset}')
    actor = _eas().spawn_actor_from_object(mesh, transform.translation, transform.rotation.rotator())
    actor.set_actor_scale3d(transform.scale3d)
    if label:
        actor.set_actor_label(label)
    if folder:
        actor.set_folder_path(u.Name(folder))
    if materials:
        comp = actor.static_mesh_component
        for i, path in enumerate(materials):
            if path:
                mat = u.load_asset(path)
                if mat:
                    comp.set_material(i, mat)
    return actor


def spawn_light(light, origin, folder=None):
    t = compose(u.Transform(u.Vector(*light['location']), u.Rotator(0, 0, 0), u.Vector(1, 1, 1)), origin)
    actor = _eas().spawn_actor_from_class(u.PointLight, t.translation, u.Rotator(0, 0, 0))
    comp = actor.point_light_component
    c = light.get('color', [1, 1, 1])
    comp.set_light_color(u.LinearColor(c[0], c[1], c[2], 1.0))
    comp.set_intensity(float(light.get('intensity', 5000)))
    comp.set_attenuation_radius(float(light.get('attenuation_radius', 1000)))
    comp.set_cast_shadows(bool(light.get('cast_shadows', False)))
    actor.set_actor_label(light.get('name', 'Light'))
    if folder:
        actor.set_folder_path(u.Name(folder))
    return actor


def prefab_path(ref):
    """'Doors/Airlock_A' or a file path -> the recipe file."""
    p = Path(ref)
    if p.suffix.lower() == '.json' and p.exists():
        return p
    return PREFABS / (ref if ref.endswith('.json') else ref + '.json')


def list_prefabs():
    """{category: [name, ...]} from the Prefabs directory tree."""
    out = {}
    if not PREFABS.exists():
        return out
    for f in sorted(PREFABS.rglob('*.json')):
        rel = f.relative_to(PREFABS)
        category = str(rel.parent).replace('\\', '/') if str(rel.parent) != '.' else 'Unsorted'
        out.setdefault(category, []).append(rel.stem)
    return out


def place_prefab(ref, location=None, yaw=0.0, folder=None):
    """Spawn a prefab recipe into the open level at location (cm) with a yaw; returns the actors."""
    path = prefab_path(ref)
    recipe = json.loads(path.read_text(encoding='utf-8'))
    name = path.stem
    if location is None:
        location = placement_point()
    origin = u.Transform(u.Vector(*location), u.Rotator(roll=0.0, pitch=0.0, yaw=yaw), u.Vector(1, 1, 1))
    folder = folder or f'Prefabs/{name}'
    actors = []
    for part in recipe.get('static_meshes', []):
        t = compose(transform_from_part(part), origin)
        a = spawn_mesh(part['asset'], t, label=part.get('name'), folder=folder, materials=part.get('materials'))
        a.set_is_temporarily_hidden_in_editor(False)
        if 'cast_shadows' in part:
            a.static_mesh_component.set_cast_shadow(bool(part['cast_shadows']))
        _set_tag(a, TAG_PREFAB, name)
        actors.append(a)
    for light in recipe.get('point_lights', []):
        a = spawn_light(light, origin, folder)
        _set_tag(a, TAG_PREFAB, name)
        actors.append(a)
    _eas().set_selected_level_actors(actors)
    _log(f'placed {name}: {len(actors)} actors at {location}')
    return actors


def place_part(asset, location=None, yaw=0.0):
    if location is None:
        location = placement_point()
    t = u.Transform(u.Vector(*location), u.Rotator(roll=0.0, pitch=0.0, yaw=yaw), u.Vector(1, 1, 1))
    a = spawn_mesh(asset, t, label=asset.split('.')[-1], folder='Prefabs/Parts')
    _eas().set_selected_level_actors([a])
    return a


def placement_point(reach=6000.0, fallback=1500.0):
    """Where the viewport is looking: the first surface hit ahead of the camera, else a point in front of it."""
    ues = u.get_editor_subsystem(u.UnrealEditorSubsystem)
    info = ues.get_level_viewport_camera_info()
    if not info or not info[0]:
        return [0.0, 0.0, 0.0]
    loc, rot = info[1], info[2]
    fwd = rot.get_forward_vector()
    end = loc + fwd * reach
    hit = u.SystemLibrary.line_trace_single(_world(), loc, end, u.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
                                            u.DrawDebugTrace.NONE, True)
    if hit and hit[0]:
        fields = u.GameplayStatics.break_hit_result(hit[1])
        p = fields[4]
        return [p.x, p.y, p.z]
    p = loc + fwd * fallback
    return [p.x, p.y, p.z]


def selection_origin(actors):
    """The prefab origin for a set of actors: bounds centre in XY, bounds bottom in Z, no rotation."""
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for a in actors:
        o, e = a.get_actor_bounds(False)
        for i, k in enumerate('xyz'):
            lo[i] = min(lo[i], getattr(o, k) - getattr(e, k))
            hi[i] = max(hi[i], getattr(o, k) + getattr(e, k))
    if lo[0] is math.inf:
        return u.Transform()
    return u.Transform(u.Vector((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]), u.Rotator(0, 0, 0), u.Vector(1, 1, 1))


def describe_actor(actor, origin=None):
    """A recipe row for an actor, relative to origin (world if None). None for actors the recipe cannot hold."""
    t = actor.get_actor_transform()
    rel = relative(t, origin) if origin else t
    if isinstance(actor, u.StaticMeshActor):
        comp = actor.static_mesh_component
        mesh = comp.static_mesh
        if not mesh:
            return None
        row = {'name': actor.get_actor_label(), 'asset': mesh.get_path_name(), 'matrix': matrix_rows(rel)}
        overrides = []
        changed = False
        for i, slot in enumerate(mesh.static_materials):
            m = comp.get_material(i)
            path = m.get_path_name() if m else ''
            default = slot.material_interface.get_path_name() if slot.material_interface else ''
            overrides.append(path)
            changed = changed or path != default
        if changed:
            row['materials'] = overrides
        if not comp.cast_shadow:
            row['cast_shadows'] = False
        return row
    if isinstance(actor, u.PointLight):
        comp = actor.point_light_component
        c = comp.light_color
        return {'light': True, 'name': actor.get_actor_label(), 'location': [rel.translation.x, rel.translation.y, rel.translation.z],
                'color': [c.r / 255.0, c.g / 255.0, c.b / 255.0], 'intensity': comp.intensity,
                'attenuation_radius': comp.attenuation_radius, 'cast_shadows': bool(comp.cast_shadows)}
    return None


def save_prefab(category, name, actors=None, purpose=''):
    """Write the selected actors (or the given ones) as Prefabs/<category>/<name>.json."""
    actors = list(actors) if actors is not None else list(_eas().get_selected_level_actors())
    assert actors, 'nothing selected'
    origin = selection_origin(actors)
    meshes, lights, skipped = [], [], []
    for a in actors:
        row = describe_actor(a, origin)
        if row is None:
            skipped.append(a.get_actor_label())
        elif row.pop('light', False):
            lights.append(row)
        else:
            meshes.append(row)
    recipe = {'schema_version': 1, 'purpose': purpose or f'{name}: {len(meshes)} parts, {len(lights)} lights',
              'origin': 'bounds centre XY, bounds bottom Z of the parts when saved; place_prefab puts this point at the requested location',
              'static_meshes': meshes, 'point_lights': lights, 'notes': []}
    if skipped:
        recipe['notes'].append('skipped (not a static mesh or point light): ' + ', '.join(skipped))
    path = PREFABS / category / f'{name}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(recipe, indent=1), encoding='utf-8')
    for a in actors:
        _set_tag(a, TAG_PREFAB, name)
    _log(f'saved {path.relative_to(ROOT)}: {len(meshes)} parts, {len(lights)} lights, skipped {skipped}')
    return path


def save_selection_by_folder():
    """Menu action: the selection's outliner folder names the prefab, Prefabs/<Category>/<Name>."""
    actors = list(_eas().get_selected_level_actors())
    assert actors, 'select the actors of the prefab first'
    folder = str(actors[0].get_folder_path())
    parts = [p for p in folder.replace('\\', '/').split('/') if p and p.lower() != 'prefabs']
    if len(parts) >= 2:
        category, name = parts[-2], parts[-1]
    elif len(parts) == 1:
        category, name = 'Unsorted', parts[0]
    else:
        category, name = 'Unsorted', re.sub(r'[^A-Za-z0-9_]+', '_', actors[0].get_actor_label())
    return save_prefab(category, name, actors)


# ---------------------------------------------------------------- live link
def _linked_actors():
    out = {}
    for a in _eas().get_all_level_actors():
        link = _tag_value(a, TAG_LINK)
        if link:
            out[link] = a
    return out


def apply_link(payload):
    """Create, move or remove actors from Blender's description. payload is a dict or its JSON.

    objects: [{link, asset, name, matrix (UE rows), materials?}], remove: [link, ...]
    Returns a summary dict.
    """
    if isinstance(payload, str):
        payload = json.loads(payload)
    existing = _linked_actors()
    created = moved = removed = 0
    errors = []
    for obj in payload.get('objects', []):
        link = obj['link']
        try:
            t = transform_from_rows(obj['matrix'])
            a = existing.get(link)
            if a and isinstance(a, u.StaticMeshActor) and a.static_mesh_component.static_mesh and \
                    a.static_mesh_component.static_mesh.get_path_name() == obj['asset']:
                a.set_actor_transform(t, False, False)
                moved += 1
            else:
                if a:
                    _eas().destroy_actor(a)
                a = spawn_mesh(obj['asset'], t, label=obj.get('name'), folder=obj.get('folder', 'LiveLink'),
                               materials=obj.get('materials'))
                _set_tag(a, TAG_LINK, link)
                existing[link] = a
                created += 1
            if obj.get('name') and a.get_actor_label() != obj['name']:
                a.set_actor_label(obj['name'])
        except Exception as e:
            errors.append(f'{link}: {e}')
    for link in payload.get('remove', []):
        a = existing.pop(link, None)
        if a:
            _eas().destroy_actor(a)
            removed += 1
    summary = {'created': created, 'moved': moved, 'removed': removed, 'errors': errors, 'linked': len(existing)}
    _log(f'live link: {summary}')
    return summary


def pull_selection():
    """The selected actors as link objects for Blender; untagged actors get a link id now."""
    out = []
    for a in _eas().get_selected_level_actors():
        row = describe_actor(a)
        if row is None or row.get('light'):
            continue
        link = _tag_value(a, TAG_LINK)
        if not link:
            link = uuid.uuid4().hex
            _set_tag(a, TAG_LINK, link)
        row['link'] = link
        out.append(row)
    return {'objects': out}


def pull_selection_json():
    return json.dumps(pull_selection())


def select_linked():
    actors = list(_linked_actors().values())
    _eas().set_selected_level_actors(actors)
    return len(actors)


# ---------------------------------------------------------------- menus
_entries = []   # keep the entry objects alive; the menu system holds weak references


def _menus():
    return u.ToolMenus.get()


@u.uclass()
class SSPrefabMenuEntry(u.ToolMenuEntryScript):
    @u.ufunction(override=True)
    def execute(self, context):
        action = _actions.get(str(self.data.name))
        if action is None:
            _log(f'no action for {self.data.name}')
            return
        try:
            action()
        except Exception as e:
            u.log_error(f'SSPrefabs: {e}')
            u.EditorDialog.show_message('SS Prefabs', str(e), u.AppMsgType.OK)


_actions = {}


def _entry(menu_name, section, name, label, tooltip, action):
    e = SSPrefabMenuEntry()
    e.init_entry(u.Name(OWNER), u.Name(menu_name), u.Name(section), u.Name(name), label, tooltip)
    _actions[name] = action
    e.register_menu_entry()
    _entries.append(e)


def _open_folder(path):
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(str(path))


def register_menus():
    """Build the SS Prefabs menu from the Prefabs directory and the catalogue. Safe to call again."""
    menus = _menus()
    if menus is None:
        return
    menus.unregister_owner_by_name(u.Name(OWNER))
    _entries.clear()
    _actions.clear()
    main = menus.extend_menu('LevelEditor.MainMenu')
    top = main.add_sub_menu(u.Name(OWNER), u.Name('Tools'), u.Name('SSPrefabs'), 'SS Prefabs',
                            'Prefab library, parts catalogue and the Blender live link')
    top_name = str(top.menu_name)
    # Prefabs by category
    prefabs = list_prefabs()
    place = top.add_sub_menu(u.Name(OWNER), u.Name('Place'), u.Name('SSPrefabs.Place'), 'Place Prefab',
                             'Spawn a prefab where the viewport is looking')
    if not prefabs:
        _entry(str(place.menu_name), 'Empty', 'SSPrefabs.NoPrefabs', '(no prefabs yet: save a selection first)', '', lambda: None)
    for category, names in prefabs.items():
        cat_menu = place.add_sub_menu(u.Name(OWNER), u.Name('Categories'), u.Name(f'SSPrefabs.Place.{category}'), category, '')
        for n in names:
            ref = f'{category}/{n}'
            _entry(str(cat_menu.menu_name), 'Prefabs', f'SSPrefabs.Place.{ref}', n, ref, lambda r=ref: place_prefab(r))
    # Parts by category, from the catalogue
    catalog = load_catalog()
    parts = top.add_sub_menu(u.Name(OWNER), u.Name('Place'), u.Name('SSPrefabs.Parts'), 'Place Part',
                             'Spawn one catalogued mesh where the viewport is looking')
    if not catalog:
        _entry(str(parts.menu_name), 'Empty', 'SSPrefabs.NoCatalog', '(no catalogue: run Rebuild Catalogue)', '', lambda: None)
    else:
        by_cat = {}
        for m in catalog['meshes']:
            by_cat.setdefault(m['category'], []).append(m)
        for category in sorted(by_cat):
            cat_menu = parts.add_sub_menu(u.Name(OWNER), u.Name('Categories'), u.Name(f'SSPrefabs.Parts.{category}'),
                                          f'{category} ({len(by_cat[category])})', '')
            for m in sorted(by_cat[category], key=lambda r: r['name']):
                _entry(str(cat_menu.menu_name), 'Parts', f'SSPrefabs.Part.{m["asset"]}', m['name'], m['asset'],
                       lambda a=m['asset']: place_part(a))
    _entry(top_name, 'Author', 'SSPrefabs.Save', 'Save Selection as Prefab',
           'Writes Prefabs/<Category>/<Name>.json; the selection\'s outliner folder gives the category and name',
           save_selection_by_folder)
    _entry(top_name, 'Author', 'SSPrefabs.OpenFolder', 'Open Prefabs Folder', str(PREFABS), lambda: _open_folder(PREFABS))
    _entry(top_name, 'Library', 'SSPrefabs.Rebuild', 'Rebuild Catalogue (with Blender proxies)',
           'Scans every owned static mesh; exports glTF proxies for Blender (minutes). Thumbnails already rendered are kept',
           lambda: _rebuild_catalog(True))
    _entry(top_name, 'Library', 'SSPrefabs.RebuildFast', 'Rebuild Catalogue (no proxies)',
           'Scans every owned static mesh without exporting; proxies and thumbnails already on disk are kept',
           lambda: _rebuild_catalog(False))
    _entry(top_name, 'Browser', 'SSPrefabs.OpenGallery', 'Open Visual Browser',
           f'Rebuild the thumbnail gallery page and show it in the web browser ({GALLERY})', open_gallery)
    _entry(top_name, 'Browser', 'SSPrefabs.RebuildGallery', 'Rebuild Visual Browser',
           'Write Artifacts/PrefabLibrary/index.html from the catalogue, the thumbnails Blender has rendered and the prefabs '
           '(Tools/SSLiveLink/build_gallery.py)', build_gallery)
    _entry(top_name, 'Live', 'SSPrefabs.SelectLinked', 'Select Blender-linked Actors', '', select_linked)
    _entry(top_name, 'Live', 'SSPrefabs.Refresh', 'Refresh Menus', 'Re-read the Prefabs folder and catalogue', register_menus)
    menus.refresh_all_widgets()
    _log(f'menus: {sum(len(v) for v in prefabs.values())} prefabs, {len(catalog["meshes"]) if catalog else 0} parts')


# ---------------------------------------------------------------- self test (commandlet)
def selftest(tmp_category='_SelfTest'):
    """Round trip: place parts, save them as a prefab, place the prefab, compare transforms."""
    catalog = load_catalog() or build_catalog(export_proxies=False, limit=40)
    door = next((m for m in catalog['meshes'] if m['category'] == 'Doors'), catalog['meshes'][0])
    crate = next((m for m in catalog['meshes'] if m['category'] == 'Containers'), catalog['meshes'][-1])
    # matrix round trip
    t = u.Transform(u.Vector(120, -340, 55), u.Rotator(roll=-5, pitch=10, yaw=45), u.Vector(1, 2, 0.5))
    t2 = transform_from_rows(matrix_rows(t))
    assert (t2.translation - t.translation).length() < 1e-3, 'translation round trip'
    assert abs(t2.scale3d.y - 2) < 1e-4 and abs(t2.scale3d.z - 0.5) < 1e-4, 'scale round trip'
    a1 = spawn_mesh(door['asset'], u.Transform(u.Vector(1000, 0, 0), u.Rotator(roll=0, pitch=0, yaw=90), u.Vector(1, 1, 1)), 'T_Door', 'Prefabs/_SelfTest/Pair')
    a2 = spawn_mesh(crate['asset'], u.Transform(u.Vector(1200, 300, 0), u.Rotator(), u.Vector(1, 1, 1)), 'T_Crate', 'Prefabs/_SelfTest/Pair')
    _eas().set_selected_level_actors([a1, a2])
    path = save_selection_by_folder()
    recipe = json.loads(path.read_text(encoding='utf-8'))
    assert len(recipe['static_meshes']) == 2, recipe
    d = (a2.get_actor_location() - a1.get_actor_location()).length()
    placed = place_prefab(f'{tmp_category}/Pair', [5000, 5000, 0], yaw=30)
    assert len(placed) == 2
    d2 = (placed[1].get_actor_location() - placed[0].get_actor_location()).length()
    assert abs(d - d2) < 0.5, (d, d2)
    # live link: move by matrix, then remove
    link = uuid.uuid4().hex
    rows = matrix_rows(u.Transform(u.Vector(-500, 200, 30), u.Rotator(roll=0, pitch=0, yaw=15), u.Vector(1, 1, 1)))
    s1 = apply_link({'objects': [{'link': link, 'asset': crate['asset'], 'name': 'LinkCrate', 'matrix': rows}]})
    rows[3][0] = -900.0
    s2 = apply_link({'objects': [{'link': link, 'asset': crate['asset'], 'name': 'LinkCrate', 'matrix': rows}]})
    la = _linked_actors()[link]
    assert abs(la.get_actor_location().x + 900) < 0.01, la.get_actor_location()
    _eas().set_selected_level_actors([la])
    pulled = pull_selection()
    assert pulled['objects'][0]['link'] == link
    s3 = apply_link({'remove': [link]})
    assert s1['created'] == 1 and s2['moved'] == 1 and s3['removed'] == 1, (s1, s2, s3)
    _eas().destroy_actors([a1, a2] + placed)
    path.unlink()
    try:
        path.parent.rmdir()
    except OSError:
        pass
    result = {'door': door['asset'], 'crate': crate['asset'], 'pair_distance_cm': round(d, 2), 'live': [s1, s2, s3]}
    _log('SELFTEST_OK ' + json.dumps(result))
    return result
