"""Build feet where the model has none (Warden, 2026-10-09). Run BEFORE fix_feet.py on the normalised .blend.

  blender -b <normalised>.blend -P build_feet.py -- <out>.blend

The owner: Warden's feet are "physically missing from the 3d model" - each leg ends in a flat partial boot about
14 cm long with no foot volume, and stretching it only made a longer blade. This adds a boot per side: a rounded
armoured foot (27 cm heel to toe, flat sole on the floor, tapered toe, the instep rising into the boot shaft),
joined into the body mesh. Its UVs all sit on one texel of the existing boot plating, so it takes the boot's own
dark armour colour, and it uses the boot's material slot. The old partial boot stays inside it. fix_feet.py then
aims the foot bones along the new foot and weights it.
"""
import json
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

out = sys.argv[-1]
LENGTH, WIDTH, HEIGHT, HEEL = 0.27, 0.11, 0.10, 0.12       # metres; HEEL = how far the foot reaches behind the ankle
# HEEL 0.12 (owner 2026-10-09: "move back slightly to heel area"): the boot's back lines up with the back of the shin.
SQUARE = 0.55                                               # 1 = ellipsoid, smaller = boxier (armoured boot)
ANKLE_Z = 0.17
FWD = -1.0                                                  # the crew face -Y in these Blender sources (see fix_feet.py)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh = [o for o in bpy.data.objects if o.type == 'MESH'][0]
inv = mesh.matrix_world.inverted()
# Own material slot for the boots (owner: grey matching the plating, 100% metallic - set in Unreal on this slot).
if "WardenBoot" not in mesh.data.materials:
    mesh.data.materials.append(bpy.data.materials.new("WardenBoot"))
boot_slot = list(mesh.data.materials).index(mesh.data.materials["WardenBoot"])
bm = bmesh.new(); bm.from_mesh(mesh.data)
uv_layer = bm.loops.layers.uv.active
report = {}
for side in ("l", "r"):
    sign = 1 if side == "l" else -1
    ankle = arm.matrix_world @ arm.data.bones["foot_" + side].head_local
    old = [v for v in bm.verts if (mesh.matrix_world @ v.co).z < 0.06 and sign * (mesh.matrix_world @ v.co).x > 0.02]
    xc = sum((mesh.matrix_world @ v.co).x for v in old) / len(old)
    # the texel and material the new boot borrows: the lowest old boot vertex's first face
    low = min(old, key=lambda v: v.co.z)
    face = low.link_faces[0]
    uv = next(l[uv_layer].uv.copy() for l in face.loops if l.vert == low)
    centre = Vector((xc, ankle.y + FWD * (LENGTH / 2 - HEEL), HEIGHT / 2))
    geom = bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=14, radius=1.0)
    new_verts = geom["verts"]
    for v in new_verts:
        # unit sphere -> rounded box: the owner's concept shows blocky armoured boots with a flat toe cap and a
        # square heel, not a rounded slipper. Pushing each coordinate toward +-1 squares the shape up.
        p = Vector(math.copysign(abs(c) ** SQUARE, c) for c in v.co)
        t = (FWD * p.y + 1) / 2               # 0 heel .. 1 toe
        taper = 1.0 - 0.22 * max(0.0, t - 0.6) / 0.4        # the toe cap narrows only a little: it is a blocky boot
        q = Vector((p.x * WIDTH / 2 * taper, p.y * LENGTH / 2, p.z * HEIGHT / 2 * (1.0 - 0.35 * max(0.0, t - 0.5) / 0.5)))
        q += centre
        q.z = max(0.004, q.z)                 # flat sole on the floor
        ahead = FWD * (q.y - ankle.y)         # metres in front of the ankle
        if ahead < 0.02 and q.z > HEIGHT * 0.5:
            q.z += 0.05 * (1 - (ahead + HEEL) / (HEEL + 0.02))             # the instep rises into the shaft
        v.co = inv @ q
    new_faces = {f for v in new_verts for f in v.link_faces}
    for f in new_faces:
        f.material_index = boot_slot
        f.smooth = True
        for l in f.loops:
            l[uv_layer].uv = uv
    # Tuck the old partial boot inside the new one: lift its sole off the floor, pull it toward the foot's centre
    # line and halve its reach fore and aft (its pointed heel spur ran 14 cm behind the ankle, past the new heel),
    # so no edge of it pokes through the new boot.
    for v in old:
        p = mesh.matrix_world @ v.co
        p.z = max(p.z, 0.03); p.x = xc + (p.x - xc) * 0.75; p.y = ankle.y + (p.y - ankle.y) * 0.5
        v.co = inv @ p
    report[side] = {"ankle": [round(c, 3) for c in ankle], "centre": [round(c, 3) for c in centre], "verts": len(new_verts),
                    "material_index": face.material_index}
bm.to_mesh(mesh.data); bm.free(); mesh.data.update()
print("BUILDFEET", json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=out)
