"""Render a 256x256 thumbnail of every catalogued proxy, for the add-on's part list and the editor menu.

  blender --background --factory-startup --python Tools/SSLiveLink/render_thumbnails.py --
      [--project <root>] [--limit N] [--force] [--only <substring of name>]

One Blender session renders the whole library in turn: import the glTF proxy, frame it, render it,
delete it, purge what it brought in. Memory stays flat across the 400-odd renders instead of growing
with every import. A thumbnail that already exists is kept unless --force. --limit N stops after N
attempts (0 = all), and because existing thumbnails do not count, repeated runs walk the library in
batches. --only keeps the meshes whose name contains the text.

The contract, shared with the catalogue exporter and the editor menu: thumbs/<proxy path, .png for
.glb> under Artifacts/PrefabLibrary, 256x256 PNG, opaque #1b1d22 background, the object filling about
80% of the frame, seen from front-left-above. When the run ends every catalogue entry whose thumbnail
exists gets "thumb": "thumbs/..." and catalog.json is rewritten in place with nothing else changed.

One proxy failing to import or render is recorded and the run goes on. The last line printed is
THUMBNAILS_OK {"rendered": n, "skipped": n, "failed": [names], "catalog": path}. Nothing outside
Artifacts/PrefabLibrary is ever written.
"""
from pathlib import Path
import json
import math
import sys
import time
import traceback

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(name, default):
    return type(default)(argv[argv.index(name) + 1]) if name in argv else default


ROOT = Path(arg('--project', str(Path(__file__).resolve().parents[2])))
LIBRARY = ROOT / 'Artifacts' / 'PrefabLibrary'
CATALOG = LIBRARY / 'catalog.json'
LIMIT = arg('--limit', 0)
FORCE = '--force' in argv
ONLY = arg('--only', '').lower()

SIZE = 256
SAMPLES = 16
BACKGROUND = (0x1b, 0x1d, 0x22)
FILL = 0.8                                        # the fraction of the frame the object's bounds may span
SPECK = 0.005                                     # a picture with less of it off the backdrop gets a warning
VIEW = Vector((1.0, -1.15, 0.8)).normalized()     # from the object toward the camera: front-left-above
LENS, SENSOR = 50.0, 36.0
CLAY = ((0.62, 0.63, 0.66), 0.5, 0.1)             # base colour, roughness, metallic for unassigned slots
AMBIENT = ((0.55, 0.57, 0.62), 0.4)               # world colour and strength the object is lit by
# Sun strengths are irradiance, so a white face square to the key lands at energy/pi plus the ambient:
# about 0.8 linear here, bright without clipping, since many proxies carry a flat white material. That
# only holds for a surface the lights are all that reaches, which is why tame() switches emission off.
SUNS = (                                          # name, energy, colour, the direction the light comes from
    ('SSThumb Key', 1.8, (1.0, 0.97, 0.92), (0.45, -0.85, 1.1)),
    ('SSThumb Fill', 0.6, (0.85, 0.9, 1.0), (-1.0, 0.55, 0.35)),
)
# The datablock pools an import can populate, in the order they must be emptied.
POOLS = ('objects', 'collections', 'meshes', 'materials', 'images', 'node_groups', 'lights', 'cameras', 'actions')


def log(*a):
    print('THUMB', *a)


def srgb_to_linear(rgb):
    """The world colour is scene linear, the contract names a display value; this keeps them the same pixel."""
    out = []
    for c in rgb:
        c /= 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# ---------------------------------------------------------------- the fixed scene: camera, suns, world, clay
def build_scene():
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = SIZE
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.dither_intensity = 0.0     # the background has to be the exact flat colour, not a noisy one
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '8'
    sc.render.image_settings.compression = 30
    sc.eevee.taa_render_samples = SAMPLES
    # AgX or Filmic would remap the background away from #1b1d22 and desaturate the proxies' flat colours.
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0

    # The world does two jobs at once: what the camera sees is the contract colour, what lights the
    # object is a brighter neutral, so shadow sides read as shape instead of vanishing into the backdrop.
    world = bpy.data.worlds.new('SSThumb World')
    if not world.node_tree:   # Blender 5 makes the tree itself and deprecates the switch; 4.x still needs it
        world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputWorld')
    seen = nodes.new('ShaderNodeBackground')
    seen.inputs['Color'].default_value = (*srgb_to_linear(BACKGROUND), 1.0)
    seen.inputs['Strength'].default_value = 1.0
    ambient = nodes.new('ShaderNodeBackground')
    ambient.inputs['Color'].default_value = (*AMBIENT[0], 1.0)
    ambient.inputs['Strength'].default_value = AMBIENT[1]
    path = nodes.new('ShaderNodeLightPath')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(path.outputs['Is Camera Ray'], mix.inputs[0])
    links.new(ambient.outputs['Background'], mix.inputs[1])
    links.new(seen.outputs['Background'], mix.inputs[2])
    links.new(mix.outputs['Shader'], out.inputs['Surface'])
    sc.world = world

    for name, energy, colour, from_dir in SUNS:
        light = bpy.data.lights.new(name, 'SUN')
        light.energy = energy
        light.color = colour
        light.angle = math.radians(3.0)
        o = bpy.data.objects.new(name, light)
        o.rotation_euler = (-Vector(from_dir)).normalized().to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(o)

    cam = bpy.data.objects.new('SSThumb Camera', bpy.data.cameras.new('SSThumb Camera'))
    cam.data.lens = LENS
    cam.data.sensor_width = SENSOR
    cam.data.sensor_fit = 'HORIZONTAL'   # the frame is square, so this fixes the field of view on both axes
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


def clay_material():
    (r, g, b), rough, metal = CLAY
    m = bpy.data.materials.new('SSThumb Clay')
    if not m.node_tree:
        m.use_nodes = True
    n = m.node_tree.nodes['Principled BSDF']
    n.inputs['Base Color'].default_value = (r, g, b, 1.0)
    n.inputs['Roughness'].default_value = rough
    n.inputs['Metallic'].default_value = metal
    m.use_fake_user = True   # so the orphan sweep after every mesh leaves it alone
    return m


# ---------------------------------------------------------------- per mesh: import, clothe, frame, render, discard
def snapshot():
    return {pool: {block.name for block in getattr(bpy.data, pool)} for pool in POOLS}


def discard_since(before):
    """Remove every datablock the import added, then sweep whatever that orphaned."""
    for pool in POOLS:
        coll = getattr(bpy.data, pool)
        for block in [b for b in coll if b.name not in before[pool]]:
            coll.remove(block, do_unlink=True)
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)


def tame(mat, clay):
    """What a slot is drawn with: the proxy's own material made to answer to the lights, or the clay.

    The export strips textures, and two kinds of material are left that ignore the lights and come out
    as a flat white cut-out. Emissive ones (emissiveFactor 1,1,1 at a strength of up to 10) keep their
    Principled BSDF and have the emission switched off. Unlit ones are imported as a bare emission
    shader with no Principled BSDF at all; nothing of them is worth keeping, so the slot gets the clay.

    The importer also turns backface culling on for every material that is not doubleSided, and the
    fixed camera sees ceilings, wall panels and door frames from behind: culled, they draw as an
    outline or as nothing. A thumbnail shows the part from wherever the camera is, so culling goes off.
    """
    if mat is None or not mat.node_tree:
        return clay
    shaders = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED']
    if not shaders:
        return clay
    mat.use_backface_culling = False
    black = (0.0, 0.0, 0.0, 1.0)
    for node in shaders:
        # 'Emission' is the colour socket's name before Blender 4.0.
        for key, off in (('Emission Strength', 0.0), ('Emission Color', black), ('Emission', black)):
            socket = node.inputs.get(key)
            if socket is None:
                continue
            for link in list(socket.links):
                mat.node_tree.links.remove(link)
            socket.default_value = off
    return mat


def clothe(objects, clay):
    """Every slot ends up lit and two-sided: tame() per material, the clay for empty slots and slotless meshes."""
    for o in objects:
        mats = o.data.materials
        if not len(mats):
            mats.append(clay)
            continue
        for i in range(len(mats)):
            mats[i] = tame(mats[i], clay)


def world_bounds(objects):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def place_camera(cam, lo, hi):
    """Put the camera on the fixed view axis, as close as the bounds allow within FILL of the frame.

    The bounding sphere gives R / sin(atan(k)) with k the half-angle the object may span; that is the
    distance at which a sphere of radius R fills the frame, and an upper bound for anything inside it.
    Flat pieces (floors, walls, panels) would sit small at that distance, so the eight corners of the
    bounds are projected instead: the nearest distance at which every corner stays inside the fill is
    exact for a box, never further than the sphere distance, and never cuts anything off.
    """
    centre = (lo + hi) / 2
    radius = (hi - lo).length / 2
    if radius < 1e-6:
        raise RuntimeError('empty bounds')
    forward = -VIEW
    right = forward.cross(Vector((0.0, 0.0, 1.0))).normalized()
    up = right.cross(forward)
    k = FILL * SENSOR / (2.0 * LENS)
    dist = 0.0
    for sx in (lo.x, hi.x):
        for sy in (lo.y, hi.y):
            for sz in (lo.z, hi.z):
                rel = Vector((sx, sy, sz)) - centre
                span = max(abs(rel.dot(right)), abs(rel.dot(up)))
                dist = max(dist, span / k + rel.dot(VIEW))
    cam.location = centre + VIEW * dist
    cam.rotation_euler = forward.to_track_quat('-Z', 'Y').to_euler()
    cam.data.clip_start = dist * 0.01
    cam.data.clip_end = dist + radius * 4.0
    return dist


def coverage(thumb):
    """The fraction of the written picture that is not the backdrop colour, read back from the file."""
    img = bpy.data.images.load(str(thumb), check_existing=False)
    try:
        px = np.empty(len(img.pixels), dtype=np.float32)
        img.pixels.foreach_get(px)
        rgb = px.reshape(-1, img.channels)[:, :3]   # an 8-bit file comes back as its bytes over 255
        backdrop = np.array(BACKGROUND, dtype=np.float32) / 255.0
        return float((np.abs(rgb - backdrop).max(axis=1) > 1.5 / 255.0).mean())
    finally:
        bpy.data.images.remove(img)


def render_entry(sc, cam, clay, glb, thumb):
    """Returns the fraction of the frame the object covers; a picture of nothing is a failure, not a thumbnail."""
    before = snapshot()
    try:
        bpy.ops.import_scene.gltf(filepath=str(glb))
        # A proxy is a static mesh; any light or camera that rode along would change the picture.
        for o in [o for o in bpy.data.objects if o.name not in before['objects'] and o.type in ('LIGHT', 'CAMERA')]:
            bpy.data.objects.remove(o, do_unlink=True)
        meshes = [o for o in bpy.data.objects
                  if o.name not in before['objects'] and o.type == 'MESH' and len(o.data.vertices)]
        if not meshes:
            raise RuntimeError('proxy holds no geometry')
        clothe(meshes, clay)
        place_camera(cam, *world_bounds(meshes))
        thumb.parent.mkdir(parents=True, exist_ok=True)
        sc.render.filepath = str(thumb)
        bpy.ops.render.render(write_still=True)
        if not thumb.exists():
            raise RuntimeError('render wrote nothing')
        covered = coverage(thumb)
        if covered <= 0.0:
            thumb.unlink()   # or the catalogue pass below would hand the part an empty dark square
            raise RuntimeError('render shows nothing but the background')
        return covered
    finally:
        discard_since(before)


# ---------------------------------------------------------------- the run
def thumb_rel(entry):
    proxy = entry.get('proxy') or ''
    return 'thumbs/' + proxy[:-4] + '.png' if proxy.endswith('.glb') else None


def main():
    raw = CATALOG.read_bytes()
    catalog = json.loads(raw.decode('utf-8'))
    library = LIBRARY.resolve()
    sc, cam = build_scene()
    clay = clay_material()
    rendered, skipped, failed = 0, 0, []
    for entry in catalog['meshes']:
        name = entry.get('name', entry.get('asset', '?'))
        if ONLY and ONLY not in name.lower():
            continue
        rel = thumb_rel(entry)
        thumb = (LIBRARY / rel).resolve() if rel else None
        if thumb and thumb.exists() and not FORCE:
            skipped += 1
            continue
        if LIMIT and rendered + len(failed) >= LIMIT:
            break
        t0 = time.perf_counter()
        try:
            if not thumb:
                raise RuntimeError('no proxy in the catalogue')
            if library not in thumb.parents:
                raise RuntimeError(f'thumbnail path {rel} leaves the library')
            glb = LIBRARY / entry['proxy']
            if not glb.exists():
                raise FileNotFoundError(glb)
            covered = render_entry(sc, cam, clay, glb, thumb)
            rendered += 1
            log('ok', name, f'{time.perf_counter() - t0:.2f}s', f'covers {covered:.1%}')
            if covered < SPECK:
                log('warn', name, f'only {covered:.2%} of the frame is not background')
        except Exception as e:
            failed.append(name)
            log('fail', name, f'{type(e).__name__}: {e}')
            traceback.print_exc()

    # Every entry whose thumbnail is on disk points at it, whether this run drew it or an earlier one did;
    # an entry whose thumbnail is gone loses the key rather than point at nothing.
    for entry in catalog['meshes']:
        rel = thumb_rel(entry)
        if rel and (LIBRARY / rel).exists():
            entry['thumb'] = rel
        else:
            entry.pop('thumb', None)
    # Same encoder and the same line endings the file already has, so the diff is the thumb lines alone.
    CATALOG.write_text(json.dumps(catalog, indent=1), encoding='utf-8', newline='\r\n' if b'\r\n' in raw else '\n')
    print('THUMBNAILS_OK ' + json.dumps({'rendered': rendered, 'skipped': skipped, 'failed': failed,
                                         'catalog': CATALOG.as_posix()}))


main()
