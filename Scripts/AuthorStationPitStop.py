"""Compose the station exterior as a body the hangar is cut into, from the owned kitbash.

Blender --background --factory-startup --python Scripts/AuthorStationPitStop.py [-- --station 3 --scale 6.5]

The target (docs/KNOWN_ISSUES.md, "the station target"): one silhouette, not two objects. A dark
mass with a single lit slot cut into it, the mouth exactly the collision gap, a lane of approach
lights, beacons on the extremities, and a body four to six times the hangar in every dimension.

Frame: station-local centimetres, +X into the hangar, mouth plane at X=-1700, deck at Z=-10, bay
beams at Z=967.5, corridor |Y|<=700. The interior shell occupies X -1700..1700, Y +-1400, Z -60..1000.
Everything here is measured against those numbers, and the receipt records the checks.

Vendor geometry is read from the kitbash .blend and never written back.
"""
import bpy, bmesh, json, math, sys, hashlib, traceback
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / 'User downloaded assets' / 'VaultCache' / 'FabLibrary'
SRC = next((VAULT / 'Sci_Fi_SPACE_STATION_Kitbash___3D_Kitbash_Asset_Pack___Blender-9af3878b' / 'blender').rglob('*.blend'))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default):
    return type(default)(argv[argv.index(name) + 1]) if name in argv else default
TAG = arg('--tag', 'default')
OUT = ROOT / 'Artifacts' / 'StationPitStop' / TAG
OUT.mkdir(parents=True, exist_ok=True)
STATION = arg('--station', '3')
SCALE = arg('--scale', 6.5)
MOUTH_AZIMUTH = arg('--azimuth', 999.0)   # degrees around the ring axis; 999 = 45 degrees off the tower
OVERHANG = arg('--overhang', 1800.0)   # cm the disc rim reaches forward of the mouth plane
DISC_BOTTOM = arg('--discbottom', 1600.0)  # cm, underside of the disc above the deck; 6 m clear of the bay beams
RENDER = '--norender' not in argv

# The hangar the body must wrap. All cm.
THROAT = dict(x=(-1900.0, 1900.0), y=(-1450.0, 1450.0), z=(-80.0, 1030.0))
MOUTH_X, MOUTH_Y, MOUTH_Z = -1700.0, 700.0, (-10.0, 967.5)
CORRIDOR_START_X = -17150.0

M2CM = 100.0


def log(*a):
    print('PITSTOP', *a)


# ---------------------------------------------------------------- load only the chosen station
bpy.ops.wm.open_mainfile(filepath=str(SRC), load_ui=False)
digest = hashlib.sha256(SRC.read_bytes()).hexdigest()
body = bpy.data.objects.get(STATION)
assert body and body.type == 'MESH', f'station object {STATION!r} not found'
# The kitbash keeps its part library in excluded 'station N' collections. Take the candidates now, while the
# file is open, and set them aside; loading them back from the same file later is not possible.
import random
random.seed(20260917)
pool_protos = [o for o in bpy.data.objects
               if o.type == 'MESH' and o.data and o is not body
               and any(c.name.lower().startswith('station ') for c in o.users_collection)
               and 0.4 <= max(o.dimensions) <= 6.0 and 40 <= len(o.data.polygons) < 20000]
random.shuffle(pool_protos)
pool_protos = pool_protos[:160]
keep = set(pool_protos) | {body}
for o in list(bpy.data.objects):
    if o not in keep:
        bpy.data.objects.remove(o, do_unlink=True)
for o in pool_protos:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    o.hide_render = True
    o.hide_viewport = True
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
sc = bpy.context.scene
if body.name not in sc.collection.objects:
    sc.collection.objects.link(body)
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
tris_source = sum(max(0, len(p.vertices) - 2) for p in body.data.polygons)
log('source', STATION, 'tris', tris_source, 'materials', [m.name for m in body.data.materials if m])

# ---------------------------------------------------------------- measure the ring and the tower
verts = [v.co.copy() for v in body.data.vertices]
lo = Vector([min(v[i] for v in verts) for i in range(3)])
hi = Vector([max(v[i] for v in verts) for i in range(3)])
log('native bounds m', [round(v, 2) for v in lo], [round(v, 2) for v in hi])
# The ring is the widest horizontal structure: take the Z band holding the most XY-spread vertices.
zs = sorted(v.z for v in verts)
bins = 40
zmin, zmax = zs[0], zs[-1]
band = (zmax - zmin) / bins
spread = []
for b in range(bins):
    z0, z1 = zmin + b * band, zmin + (b + 1) * band
    sel = [v for v in verts if z0 <= v.z < z1]
    if len(sel) < 50:
        spread.append((0, b, sel))
        continue
    cx = sum(v.x for v in sel) / len(sel); cy = sum(v.y for v in sel) / len(sel)
    r = sorted(math.hypot(v.x - cx, v.y - cy) for v in sel)
    spread.append((r[int(len(r) * .9)], b, sel))
spread.sort(reverse=True)
_, ring_bin, ring_sel = spread[0]
ring_cx = sum(v.x for v in ring_sel) / len(ring_sel)
ring_cy = sum(v.y for v in ring_sel) / len(ring_sel)
radii = sorted(math.hypot(v.x - ring_cx, v.y - ring_cy) for v in ring_sel)
ring_ro = radii[int(len(radii) * .97)]
ring_ri = radii[int(len(radii) * .10)]
# The disc proper, not the trusses above it: within the outer annulus, take the densest contiguous Z band.
annulus = [v for v in verts if ring_ro * .6 <= math.hypot(v.x - ring_cx, v.y - ring_cy) <= ring_ro]
zs_a = sorted(v.z for v in annulus)
nb = 60
za0, za1 = zs_a[0], zs_a[-1]
bw = (za1 - za0) / nb
hist = [0] * nb
for v in annulus:
    hist[min(nb - 1, int((v.z - za0) / bw))] += 1
peak = max(range(nb), key=lambda i: hist[i])
lo_b = peak
while lo_b > 0 and hist[lo_b - 1] > hist[peak] * .12:
    lo_b -= 1
hi_b = peak
while hi_b < nb - 1 and hist[hi_b + 1] > hist[peak] * .12:
    hi_b += 1
rim_zlo, rim_zhi = za0 + lo_b * bw, za0 + (hi_b + 1) * bw
log('ring centre', round(ring_cx, 2), round(ring_cy, 2), 'Ro', round(ring_ro, 2), 'Ri', round(ring_ri, 2),
    'disc z', round(rim_zlo, 2), round(rim_zhi, 2), 'disc thickness', round(rim_zhi - rim_zlo, 2))
tower = [v for v in verts if v.z > rim_zhi + (rim_zhi - rim_zlo)]
if tower:
    tcx = sum(v.x for v in tower) / len(tower); tcy = sum(v.y for v in tower) / len(tower)
    tower_az = math.degrees(math.atan2(tcy - ring_cy, tcx - ring_cx))
    log('tower centroid', round(tcx, 2), round(tcy, 2), 'azimuth from ring', round(tower_az, 1), 'top z', round(max(v.z for v in tower), 2))
else:
    tower_az = 0.0

# ---------------------------------------------------------------- place: mouth on the outer face, facing -X
# Rotate so the chosen azimuth points along -X, then translate so that face sits on the mouth plane.
if MOUTH_AZIMUTH == 999.0:
    MOUTH_AZIMUTH = tower_az - 45.0
    log('mouth azimuth auto', round(MOUTH_AZIMUTH, 1))
az = math.radians(MOUTH_AZIMUTH)
rot = Matrix.Rotation(math.radians(180.0) - az, 4, 'Z')   # azimuth direction -> -X
S = SCALE * M2CM
xf = Matrix.Scale(S, 4) @ rot @ Matrix.Translation(Vector((-ring_cx, -ring_cy, 0)))
body.matrix_world = xf
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
verts = [v.co.copy() for v in body.data.vertices]
# The outer face along -X at Y~0 is at x = -Ro*S; shift it to the mouth plane. Vertical: rim bottom at deck - RIM_DROP.
face_x = min(v.x for v in verts if abs(v.y) < ring_ro * S * .08 and rim_zlo * S <= v.z <= rim_zhi * S)
dz = DISC_BOTTOM - rim_zlo * S
body.matrix_world = Matrix.Translation(Vector((MOUTH_X - OVERHANG - face_x, 0.0, dz)))
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
verts = [v.co.copy() for v in body.data.vertices]
lo = Vector([min(v[i] for v in verts) for i in range(3)]); hi = Vector([max(v[i] for v in verts) for i in range(3)])
log('placed bounds cm', [round(v) for v in lo], [round(v) for v in hi], 'size m', [round((hi[i] - lo[i]) / 100, 1) for i in range(3)])
rim_depth = (ring_ro - ring_ri) * S
log('rim radial depth cm', round(rim_depth), 'disc thickness cm', round((rim_zhi - rim_zlo) * S), 'disc bottom z', round(rim_zlo * S + dz))

# ---------------------------------------------------------------- cut the throat
# Faces whose centre lies inside the throat are removed. The interior shell lines that volume, so the cut edge
# is never seen from inside, and the mouth frame below covers it from outside. This is chosen over a boolean
# because kitbash geometry is many overlapping shells and an exact boolean is fragile on it.
bm = bmesh.new(); bm.from_mesh(body.data)
def inside(p):
    return THROAT['x'][0] <= p.x <= THROAT['x'][1] and THROAT['y'][0] <= p.y <= THROAT['y'][1] and THROAT['z'][0] <= p.z <= THROAT['z'][1]
cut = [f for f in bm.faces if inside(f.calc_center_median()) or any(inside(v.co) for v in f.verts)]
bmesh.ops.delete(bm, geom=cut, context='FACES')
# Also open the approach: nothing of the body may sit in the corridor in front of the mouth.
def in_lane(p):
    return p.x < MOUTH_X + 200 and abs(p.y) <= 900 and -200 <= p.z <= 1100
lane = [f for f in bm.faces if in_lane(f.calc_center_median()) or any(in_lane(v.co) for v in f.verts)]
bmesh.ops.delete(bm, geom=lane, context='FACES')
bm.to_mesh(body.data); bm.free()
log('faces removed: throat', len(cut), 'lane', len(lane))
tris_after = sum(max(0, len(p.vertices) - 2) for p in body.data.polygons)

# ---------------------------------------------------------------- materials on the body
def pbr(name, color, metallic, rough, emissive=(0, 0, 0), strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n = m.node_tree.nodes['Principled BSDF']
    n.inputs['Base Color'].default_value = (*color, 1)
    n.inputs['Metallic'].default_value = metallic
    n.inputs['Roughness'].default_value = rough
    n.inputs['Emission Color'].default_value = (*emissive, 1)
    n.inputs['Emission Strength'].default_value = strength
    return m
HULL = pbr('PitStop_Hull', (0.16, 0.17, 0.19), 0.85, 0.55)
PANEL = pbr('PitStop_Panel', (0.05, 0.08, 0.12), 0.3, 0.3)
ACCENT = pbr('PitStop_Accent', (0.55, 0.24, 0.05), 0.6, 0.5, (0.9, 0.35, 0.05), 0.15)
# Emission is modest on purpose: in game these bloom, and at 12 the lane read as white blobs and the frame as a slab of glare.
LIGHT_WARM = pbr('PitStop_LightWarm', (1, 0.8, 0.6), 0.0, 0.4, (1.0, 0.62, 0.30), 4.0)
LIGHT_CYAN = pbr('PitStop_LightCyan', (0.7, 0.9, 1), 0.0, 0.4, (0.25, 0.85, 1.0), 4.0)
LIGHT_RED = pbr('PitStop_LightRed', (1, 0.6, 0.6), 0.0, 0.4, (1.0, 0.12, 0.08), 5.0)
# Map the kitbash's two material families onto the hull palette.
for i, m in enumerate(body.data.materials):
    name = (m.name if m else '').lower()
    body.data.materials[i] = PANEL if 'solar' in name else HULL
# A slot the accents can reuse: any face already coloured by an orange-ish family stays accent.
body.data.materials.append(ACCENT)

# ---------------------------------------------------------------- the dock module
# A solid keel under the disc that carries the mouth. Built as slabs around the hangar volume, so the bay is open
# by construction rather than cut, and each slab is also exactly one collision box. The top slab reaches into the
# disc so contact is by overlap, not by a picture.
GX0, GX1 = THROAT['x'][0], THROAT['x'][1] + 900.0       # 9 m of module behind the rear wall
GY = THROAT['y'][1] + 1050.0                            # 10.5 m of module beside each hangar wall
GZ0, GZ1 = THROAT['z'][0] - 620.0, DISC_BOTTOM + 200.0   # 6 m below the deck, 2 m into the disc
slabs = {
    'Keel_Floor':  ((GX0, GX1), (-GY, GY), (GZ0, THROAT['z'][0])),
    'Keel_Roof':   ((GX0, GX1), (-GY, GY), (THROAT['z'][1], GZ1)),
    'Keel_Port':   ((GX0, GX1), (THROAT['y'][1], GY), (THROAT['z'][0], THROAT['z'][1])),
    'Keel_Stbd':   ((GX0, GX1), (-GY, THROAT['y'][0]), (THROAT['z'][0], THROAT['z'][1])),
    'Keel_Stern':  ((THROAT['x'][1], GX1), THROAT['y'], THROAT['z']),
    # The bow plate, in four pieces around the exact admission gap.
    'Bow_Port':    ((GX0, MOUTH_X), (MOUTH_Y, THROAT['y'][1]), THROAT['z']),
    'Bow_Stbd':    ((GX0, MOUTH_X), (THROAT['y'][0], -MOUTH_Y), THROAT['z']),
    'Bow_Lintel':  ((GX0, MOUTH_X), (-MOUTH_Y, MOUTH_Y), (MOUTH_Z[1], THROAT['z'][1])),
    'Bow_Sill':    ((GX0, MOUTH_X), (-MOUTH_Y, MOUTH_Y), (THROAT['z'][0], MOUTH_Z[0])),
    # Outriggers on the rear half, thin and tall, with nav lights on their tips.
    'Fin_Port':    ((GX0 + 1400, GX1 - 200), (GY, GY + 1500), (GZ0 + 300, GZ1 - 500)),
    'Fin_Stbd':    ((GX0 + 1400, GX1 - 200), (-GY - 1500, -GY), (GZ0 + 300, GZ1 - 500)),
}

# ---------------------------------------------------------------- built parts: frame, lane, beacons
def box(name, center, size, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.object; o.name = name
    o.scale = Vector(size); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    return o
def sphere(name, center, radius, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=center)
    o = bpy.context.object; o.name = name; o.data.materials.append(material)
    return o
parts = []
# Mouth frame: inner opening is exactly the collision gap. Visible equals solid.
T, D = 90.0, 140.0   # frame bar thickness, depth along X
zc = (MOUTH_Z[0] + MOUTH_Z[1]) / 2; zh = MOUTH_Z[1] - MOUTH_Z[0]
parts.append(box('Frame_Left', (MOUTH_X, MOUTH_Y + T / 2, zc), (D, T, zh + 2 * T), LIGHT_WARM))
parts.append(box('Frame_Right', (MOUTH_X, -MOUTH_Y - T / 2, zc), (D, T, zh + 2 * T), LIGHT_WARM))
parts.append(box('Frame_Top', (MOUTH_X, 0, MOUTH_Z[1] + T / 2), (D, 2 * MOUTH_Y + 2 * T, T), LIGHT_WARM))
parts.append(box('Frame_Sill', (MOUTH_X, 0, MOUTH_Z[0] - T / 2), (D, 2 * MOUTH_Y + 2 * T, T), HULL))
for name, (bx, by, bz) in slabs.items():
    parts.append(box(name, ((bx[0] + bx[1]) / 2, (by[0] + by[1]) / 2, (bz[0] + bz[1]) / 2),
                     (bx[1] - bx[0], by[1] - by[0], bz[1] - bz[0]), PANEL if name.startswith(('Bow', 'Fin')) else HULL))
# Proud plates in a grid on the keel's outer faces: the panel lines the lighting needs. 25 cm proud, so they are
# visual only; the slab underneath is the collision.
PROUD, GAP, INSET = 25.0, 70.0, 120.0
def plate_grid(tag, axis, sign, plane, u_range, v_range, nu, nv):
    idx = 'xyz'.index(axis); others = [i for i in range(3) if i != idx]
    uw = (u_range[1] - u_range[0] - 2 * INSET - (nu - 1) * GAP) / nu
    vw = (v_range[1] - v_range[0] - 2 * INSET - (nv - 1) * GAP) / nv
    k = 0
    for a in range(nu):
        for b in range(nv):
            u = u_range[0] + INSET + a * (uw + GAP) + uw / 2
            v = v_range[0] + INSET + b * (vw + GAP) + vw / 2
            c = [0.0, 0.0, 0.0]; d = [0.0, 0.0, 0.0]
            c[idx] = plane + sign * PROUD / 2; d[idx] = PROUD
            c[others[0]] = u; d[others[0]] = uw
            c[others[1]] = v; d[others[1]] = vw
            parts.append(box(f'Plate_{tag}_{k:02d}', tuple(c), tuple(d), PANEL if (a + b) % 2 else HULL)); k += 1
plate_grid('Port', 'y', 1, GY, (GX0, GX1), (GZ0, GZ1), 5, 3)
plate_grid('Stbd', 'y', -1, -GY, (GX0, GX1), (GZ0, GZ1), 5, 3)
plate_grid('Floor', 'z', -1, GZ0, (GX0, GX1), (-GY, GY), 5, 4)
plate_grid('BowP', 'x', -1, GX0, (MOUTH_Y + T + 200, GY), (THROAT['z'][0], THROAT['z'][1]), 2, 2)
plate_grid('BowS', 'x', -1, GX0, (-GY, -MOUTH_Y - T - 200), (THROAT['z'][0], THROAT['z'][1]), 2, 2)
plate_grid('BowUp', 'x', -1, GX0, (-GY, GY), (THROAT['z'][1] + 40, GZ1), 4, 1)
# Light strips: cyan along the keel's front vertical edges and its bottom front edge; a warm bar over the mouth.
STRIP = 30.0
for side in (-1, 1):
    parts.append(box(f'Strip_Bow_{"P" if side > 0 else "S"}', (GX0 - STRIP / 2, side * (GY - 60), (GZ0 + GZ1) / 2),
                     (STRIP, STRIP, GZ1 - GZ0 - 400), LIGHT_CYAN))
    parts.append(box(f'Strip_Keel_{"P" if side > 0 else "S"}', ((GX0 + GX1) / 2, side * (GY + STRIP / 2), GZ0 + 60),
                     (GX1 - GX0 - 400, STRIP, STRIP), LIGHT_CYAN))
    parts.append(sphere(f'NavLight_{"P" if side > 0 else "S"}', (GX1 - 200, side * (GY + 1500), GZ1 - 500), 35.0,
                        LIGHT_RED if side > 0 else LIGHT_CYAN))
parts.append(box('Strip_MouthBar', (GX0 - PROUD - STRIP / 2 - 10, 0, MOUTH_Z[1] + T + 260), (STRIP, 2 * MOUTH_Y + 1400, 60), LIGHT_WARM))
# Windows: two warm rows along each long face and the fins, one row beside the mouth. A pit stop is inhabited,
# and from the side the module is in the disc's shadow, so this is what makes it read at all.
WIN, WIN_STEP, WIN_PROUD = 42.0, 130.0, 18.0
def window_row(tag, axis, sign, plane, u_range, v):
    idx = 'xyz'.index(axis); others = [i for i in range(3) if i != idx]
    u = u_range[0] + WIN_STEP
    k = 0
    while u < u_range[1] - WIN_STEP / 2:
        if k % 7 != 3:   # a dark one now and then: not every room is lit
            c = [0.0, 0.0, 0.0]; d = [0.0, 0.0, 0.0]
            c[idx] = plane + sign * (PROUD + WIN_PROUD / 2); d[idx] = WIN_PROUD
            c[others[0]] = u; d[others[0]] = WIN
            c[others[1]] = v; d[others[1]] = WIN * 0.6
            parts.append(box(f'Win_{tag}_{k:02d}', tuple(c), tuple(d), LIGHT_WARM))
        u += WIN_STEP; k += 1
for zrow in (THROAT['z'][0] + 300, THROAT['z'][1] + 400):
    window_row(f'Port{int(zrow)}', 'y', 1, GY, (GX0, GX1), zrow)
    window_row(f'Stbd{int(zrow)}', 'y', -1, -GY, (GX0, GX1), zrow)
    window_row(f'FinP{int(zrow)}', 'y', 1, GY + 1500, (GX0 + 1400, GX1 - 200), zrow)
    window_row(f'FinS{int(zrow)}', 'y', -1, -GY - 1500, (GX0 + 1400, GX1 - 200), zrow)
window_row('BowP', 'x', -1, GX0, (MOUTH_Y + T + 250, GY - 100), THROAT['z'][0] + 420)
window_row('BowS', 'x', -1, GX0, (-GY + 100, -MOUTH_Y - T - 250), THROAT['z'][0] + 420)
# Cyan edge strips along the fins' outer top edges, so their silhouette reads from the side.
for side in (-1, 1):
    parts.append(box(f'Strip_Fin_{"P" if side > 0 else "S"}', ((GX0 + 1400 + GX1 - 200) / 2, side * (GY + 1500 + STRIP / 2), GZ1 - 500 - 60),
                     (GX1 - 200 - GX0 - 1400 - 300, STRIP, STRIP), LIGHT_CYAN))
# Greebles: the kitbash's own part library, from the collections it keeps excluded, seated flush on the keel's
# outer faces so the module reads as built rather than boxed. Deterministic seed, so reruns match.
import random
random.seed(20260917)
pool = pool_protos
log('greeble pool', len(pool))
faces = [  # (normal axis, sign, u range, v range, plane coord)
    ('y', -1, (GX0 + 200, GX1 - 200), (GZ0 + 200, GZ1 - 300), -GY),
    ('y', 1, (GX0 + 200, GX1 - 200), (GZ0 + 200, GZ1 - 300), GY),
    ('z', -1, (GX0 + 200, GX1 - 200), (-GY + 200, GY - 200), GZ0),
    ('x', -1, (-GY + 200, -MOUTH_Y - T - 500), (THROAT['z'][1] + 100, GZ1 - 300), GX0),
    ('x', -1, (MOUTH_Y + T + 500, GY - 200), (THROAT['z'][1] + 100, GZ1 - 300), GX0),
]
GREEBLE_MAX, GREEBLE_PROUD = 650.0, 260.0   # cm: largest dimension, and how far a part may stand off its face
def in_front_of_mouth(corners):
    x0 = min(c.x for c in corners); y0 = min(c.y for c in corners); y1 = max(c.y for c in corners)
    z0 = min(c.z for c in corners); z1 = max(c.z for c in corners)
    return x0 < MOUTH_X and y0 < 950 and y1 > -950 and z0 < 1300 and z1 > -300
greebles = []
if pool:
    for k in range(int(arg('--greebles', 36))):
        axis, sign, ur, vr, plane = faces[k % len(faces)]
        proto = random.choice(pool)
        g = proto.copy(); g.data = proto.data.copy(); sc.collection.objects.link(g)
        g.hide_render = False; g.hide_viewport = False
        g.parent = None
        g.matrix_world = Matrix.Identity(4)
        gs = M2CM * random.uniform(0.9, 1.8)
        g.scale = (gs, gs, gs)
        if axis == 'x':
            g.rotation_euler = (0, math.radians(-90 * sign), 0)
        elif axis == 'y':
            g.rotation_euler = (math.radians(90 * sign), 0, 0)
        else:
            g.rotation_euler = (math.radians(180 if sign < 0 else 0), 0, random.uniform(0, 6.28))
        bpy.context.view_layer.update()
        idx = 'xyz'.index(axis)
        others = [i for i in range(3) if i != idx]
        corners = [g.matrix_world @ Vector(c) for c in g.bound_box]
        dims = [max(c[i] for c in corners) - min(c[i] for c in corners) for i in range(3)]
        # Cap the part's size and how far it stands off the face, uniformly.
        shrink = min(1.0, GREEBLE_MAX / max(dims), GREEBLE_PROUD / max(dims[idx], 1.0))
        if shrink < 1.0:
            g.scale = tuple(v * shrink for v in g.scale)
            bpy.context.view_layer.update()
            corners = [g.matrix_world @ Vector(c) for c in g.bound_box]
            dims = [max(c[i] for c in corners) - min(c[i] for c in corners) for i in range(3)]
        # Keep the whole part inside its face; skip the part if the face is too small for it.
        hu, hv = dims[others[0]] / 2, dims[others[1]] / 2
        if ur[0] + hu >= ur[1] - hu or vr[0] + hv >= vr[1] - hv:
            bpy.data.objects.remove(g, do_unlink=True); continue
        inner = min(c[idx] for c in corners) if sign > 0 else max(c[idx] for c in corners)
        u, v = random.uniform(ur[0] + hu, ur[1] - hu), random.uniform(vr[0] + hv, vr[1] - hv)
        loc = list(g.location)
        loc[idx] += plane - inner
        loc[others[0]] += u - (sum(c[others[0]] for c in corners) / 8)
        loc[others[1]] += v - (sum(c[others[1]] for c in corners) / 8)
        g.location = loc
        bpy.context.view_layer.update()
        if in_front_of_mouth([g.matrix_world @ Vector(c) for c in g.bound_box]):
            bpy.data.objects.remove(g, do_unlink=True); continue
        g.name = f'Greeble_{k:02d}'
        for i in range(len(g.data.materials)):
            g.data.materials[i] = ACCENT if k % 5 == 0 else HULL
        if not g.data.materials:
            g.data.materials.append(HULL)
        greebles.append(g)
parts.extend(greebles)
log('greebles placed', len(greebles))
for o in pool_protos:
    bpy.data.objects.remove(o, do_unlink=True)
# Approach lane: paired lights from the corridor start to the mouth, warm, plus a cyan centreline every fourth.
x = CORRIDOR_START_X + 600
i = 0
while x < MOUTH_X - 900:
    for side in (-1, 1):
        parts.append(sphere(f'Lane_{i}_{"L" if side < 0 else "R"}', (x, side * 1000.0, 220.0), 22.0, LIGHT_WARM))
    if i % 4 == 0:
        parts.append(sphere(f'LaneCentre_{i}', (x, 0.0, -140.0), 16.0, LIGHT_CYAN))
    x += 900.0; i += 1
log('lane pairs', i)
# Beacons on the body extremities, so the silhouette reads from kilometres away.
ext = [(hi.x - 150, 0, hi.z - 150), (lo.x + 900, lo.y + 150, (lo.z + hi.z) / 2), (lo.x + 900, hi.y - 150, (lo.z + hi.z) / 2),
       ((lo.x + hi.x) / 2, 0, lo.z + 150)]
for j, p in enumerate(ext):
    parts.append(sphere(f'Beacon_{j}', p, 60.0, LIGHT_RED if j % 2 else LIGHT_CYAN))

# ---------------------------------------------------------------- collision boxes for the code, from the same data
def clip(a0, a1, b0, b1):
    return (max(a0, b0), min(a1, b1))
tx, ty, tz = THROAT['x'], THROAT['y'], THROAT['z']
# Collision is the slabs themselves, plus the disc above and whatever of the body hangs below it, as bounds.
disc_z0 = rim_zlo * S + dz
body_pts = [v.co for v in body.data.vertices]
above = [p for p in body_pts if p.z >= disc_z0 - 50]
below = [p for p in body_pts if p.z < disc_z0 - 50]
def aabb(pts):
    return ((min(p.x for p in pts), max(p.x for p in pts)), (min(p.y for p in pts), max(p.y for p in pts)),
            (min(p.z for p in pts), max(p.z for p in pts)))
boxes = dict(slabs)
if above:
    bx, by, bz = aabb(above)
    boxes['Disc'] = ((bx[0], bx[1]), (by[0], by[1]), (max(bz[0], MOUTH_Z[1] + 200), bz[1]))
if below:
    bx, by, bz = aabb(below)
    boxes['Spire'] = ((max(bx[0], GX1), bx[1]), (by[0], by[1]), (bz[0], min(bz[1], disc_z0)))
collision = []
for name, (bx, by, bz) in boxes.items():
    if bx[1] - bx[0] < 40 or by[1] - by[0] < 40 or bz[1] - bz[0] < 40:   # the lintel and sill are 60-70 cm and must stay solid
        continue
    collision.append({'name': name, 'center': [round((bx[0] + bx[1]) / 2), round((by[0] + by[1]) / 2), round((bz[0] + bz[1]) / 2)],
                      'extent': [round((bx[1] - bx[0]) / 2), round((by[1] - by[0]) / 2), round((bz[1] - bz[0]) / 2)]})
# The boxes must not touch the corridor or the throat: assert it rather than trust it.
for c in collision:
    cx, cy, cz = c['center']; ex, ey, ez = c['extent']
    x0, x1, y0, y1, z0, z1 = cx - ex, cx + ex, cy - ey, cy + ey, cz - ez, cz + ez
    # The interior proper starts at the shell's front wall; the two metres ahead of it are the bow plate.
    overlaps_throat = x0 < tx[1] and x1 > MOUTH_X and y0 < ty[1] and y1 > ty[0] and z0 < tz[1] and z1 > tz[0]
    overlaps_lane = x0 < MOUTH_X and y0 < 900 and y1 > -900 and z0 < MOUTH_Z[1] and z1 > MOUTH_Z[0]
    assert not overlaps_throat, f'collision {c["name"]} intrudes on the hangar'
    # The bow plate's inner edge is the admission gap itself, so the lane margin does not apply to it.
    assert not overlaps_lane or c['name'].startswith('Bow_'), f'collision {c["name"]} intrudes on the approach lane'

# ---------------------------------------------------------------- geometric checks
inside_after = sum(1 for v in body.data.vertices if inside(v.co))
enclose = {
    'behind_margin_cm': round(hi.x - tx[1]), 'left_margin_cm': round(hi.y - ty[1]), 'right_margin_cm': round(ty[0] - lo.y),
    'above_margin_cm': round(hi.z - tz[1]), 'below_margin_cm': round(tz[0] - lo.z),
}
checks = {
    'body_vertices_inside_throat_after_cut': inside_after,
    'enclosure': enclose,
    'mouth_inner_opening': {'y': [-MOUTH_Y, MOUTH_Y], 'z': list(MOUTH_Z), 'x': MOUTH_X},
    'body_over_hangar_ratio': [round((hi[i] - lo[i]) / d, 2) for i, d in enumerate((3400, 2800, 1010))],
}
log('checks', json.dumps(checks))

# ---------------------------------------------------------------- export
for o in [body] + parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
target = OUT / 'StationPitStop.glb'
bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', use_selection=True, export_animations=False,
                          export_normals=True, export_apply=True, export_yup=True)
comp_pts = [o.matrix_world @ Vector(c) for o in [body] + parts for c in o.bound_box]
composition_bounds = [[round(min(p[i] for p in comp_pts)) for i in range(3)], [round(max(p[i] for p in comp_pts)) for i in range(3)]]
receipt = dict(source=str(SRC), source_sha256=digest, station=STATION, scale=SCALE, azimuth=MOUTH_AZIMUTH, overhang=OVERHANG,
               composition_bounds_cm=composition_bounds,
               disc_bottom=DISC_BOTTOM, keel=dict(x=[GX0, GX1], y=[-GY, GY], z=[GZ0, GZ1]),
               tower_azimuth_native=round(tower_az, 1), ring=dict(ro_native=round(ring_ro, 3), ri_native=round(ring_ri, 3),
               rim_z_native=[round(rim_zlo, 3), round(rim_zhi, 3)]), triangles=dict(source=tris_source, after_cut=tris_after),
               bounds_cm=[[round(v) for v in lo], [round(v) for v in hi]], collision_boxes_cm=collision, checks=checks,
               materials=[m.name for m in (HULL, PANEL, ACCENT, LIGHT_WARM, LIGHT_CYAN, LIGHT_RED)],
               output=str(target), output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
               frame='station-local cm, +X into the hangar, mouth plane X=-1700; place at station origin with no rotation',
               axis_note='exported Y-up glTF from Blender Z-up; verify in UE that bounds match bounds_cm before trusting placement')
(OUT / 'PitStop.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
assert hashlib.sha256(SRC.read_bytes()).hexdigest() == digest

# ---------------------------------------------------------------- renders, several angles, with the hangar ghosted
if RENDER:
    ghost = box('GHOST_Hangar', ((tx[0] + tx[1]) / 2 + 30, 0, (tz[0] + tz[1]) / 2), (tx[1] - tx[0] - 60, ty[1] - ty[0] - 60, tz[1] - tz[0] - 60),
                pbr('Ghost', (0.2, 1.0, 0.4), 0, 1, (0.2, 1.0, 0.4), 2.0))
    ghost.display_type = 'WIRE'
    ghost.hide_render = True
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1100, 700
    sc.render.image_settings.file_format = 'PNG'
    sc.world = bpy.data.worlds.new('Space'); sc.world.use_nodes = True
    bgn = sc.world.node_tree.nodes.get('Background')
    if bgn:
        bgn.inputs[0].default_value = (0.01, 0.012, 0.02, 1)
    for name, energy, r in (('Key', 3.0, (55, 15, 40)), ('Fill', 0.6, (-35, -25, -130))):
        o = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN')); o.data.energy = energy
        o.rotation_euler = tuple(math.radians(x) for x in r); sc.collection.objects.link(o)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); cam.data.lens = 32
    sc.collection.objects.link(cam); sc.camera = cam
    centre = Vector((0, 0, 500))
    R = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    views = {'approach': (Vector((CORRIDOR_START_X * .55, 0, 1800)), centre),
             'approach_close': (Vector((-9000, -2500, 1400)), Vector((MOUTH_X, 0, 480))),
             'quarter': (centre + Vector((-R * 1.1, -R * .9, R * .55)), centre),
             'side': (centre + Vector((0, -R * 1.5, R * .2)), centre),
             'top': (centre + Vector((0, 0.01, R * 1.6)), centre),
             'under': (centre + Vector((-R * .6, R * .4, -R * 1.2)), centre),
             'mouth_ghost': (Vector((-6500, -3200, 1500)), Vector((MOUTH_X, 0, 480))),
             'keel_under': (Vector((-7500, -7500, -6500)), Vector((500, 0, 300))),
             'keel_side': (Vector((-9000, -14000, 1200)), Vector((300, 0, 500))),
             'mouth_front': (Vector((-9500, 0, 480)), Vector((MOUTH_X, 0, 480)))}
    files = {}
    for tag, (pos, at) in views.items():
        ghost.hide_render = tag != 'mouth_ghost'
        cam.location = pos
        cam.rotation_euler = (at - pos).to_track_quat('-Z', 'Y').to_euler()
        cam.data.clip_start = 50; cam.data.clip_end = 200000
        f = OUT / f'render_{tag}.png'
        sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
        files[tag] = str(f)
    receipt['renders'] = files
    (OUT / 'PitStop.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
log('STATION_PITSTOP_AUTHORED', json.dumps({k: receipt[k] for k in ('station', 'scale', 'bounds_cm', 'triangles')}))
