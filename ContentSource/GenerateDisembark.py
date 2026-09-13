"""Author A_Disembark on the preserved glTF skeleton using existing Blender.

Only writes Animation/Disembark.glb and Disembark.json. The original hero,
walking/pilot animations, mesh skinning and Unreal assets are never modified.
No actor travel/root-motion extraction is authored: C++ owns the world route.
"""
import bisect
import hashlib
import json
import math
from pathlib import Path
import struct

import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "model-rigged.glb"
PILOT = ROOT / "ContentSource/Animation/Pilot.glb"
OUT = ROOT / "ContentSource/Animation"
HERO_HASH = "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91"
DURATION, FPS, WALK_TIME = 2.4, 30, 0.30833333333333335
CONVERSION = Matrix.Rotation(math.pi / 2, 4, "X")


def read_glb(path):
    raw = path.read_bytes()
    size = struct.unpack_from("<I", raw, 12)[0]
    return json.loads(raw[20:20 + size]), bytearray(raw[28 + size:])


def accessor(document, binary, index):
    entry = document["accessors"][index]
    view = document["bufferViews"][entry["bufferView"]]
    assert entry["componentType"] == 5126 and not entry.get("sparse"), "Expected float animation accessor"
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[entry["type"]]
    offset = view.get("byteOffset", 0) + entry.get("byteOffset", 0)
    stride = view.get("byteStride", width * 4)
    return [struct.unpack_from("<" + "f" * width, binary, offset + i * stride) for i in range(entry["count"])]


def apply_animation(rig, document, binary, seconds):
    channels = {}
    animation = document["animations"][0]
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        mode = sampler.get("interpolation", "LINEAR")
        assert mode in ("LINEAR", "STEP"), "Unsupported source animation interpolation"
        times = [row[0] for row in accessor(document, binary, sampler["input"])]
        values = accessor(document, binary, sampler["output"])
        index = max(0, min(len(times) - 2, bisect.bisect_right(times, seconds) - 1))
        alpha = max(0.0, min(1.0, (seconds - times[index]) / max(1e-8, times[index + 1] - times[index])))
        if mode == "STEP":
            alpha = 0.0
        path = channel["target"]["path"]
        a, b = values[index], values[index + 1]
        if path == "rotation":
            rotation = Quaternion((a[3], a[0], a[1], a[2])).slerp(Quaternion((b[3], b[0], b[1], b[2])), alpha)
            value = (rotation.x, rotation.y, rotation.z, rotation.w)
        else:
            value = tuple(x + (y - x) * alpha for x, y in zip(a, b))
        channels.setdefault(channel["target"]["node"], {})[path] = value
    parents = {child: index for index, node in enumerate(document["nodes"]) for child in node.get("children", [])}
    world = {}
    def evaluate(index):
        if index in world:
            return world[index]
        node, values = document["nodes"][index], channels.get(index, {})
        assert "matrix" not in node, "Source node matrices require explicit decomposition"
        location = values.get("translation", node.get("translation", (0, 0, 0)))
        q = values.get("rotation", node.get("rotation", (0, 0, 0, 1)))
        scale = values.get("scale", node.get("scale", (1, 1, 1)))
        local = Matrix.LocRotScale(Vector(location), Quaternion((q[3], q[0], q[1], q[2])), Vector(scale))
        world[index] = evaluate(parents[index]) @ local if index in parents else local
        return world[index]
    names = {node.get("name"): index for index, node in enumerate(document["nodes"])}
    inverse = CONVERSION.inverted()
    for bone in rig.pose.bones:
        joint = CONVERSION @ evaluate(names[bone.name]) @ inverse
        bone.matrix = joint @ Matrix.Translation(-bone.bone.head_local) @ bone.bone.matrix_local
        bpy.context.view_layer.update()


def capture(rig):
    return {bone.name: (bone.location.copy(), bone.rotation_quaternion.copy(), bone.scale.copy()) for bone in rig.pose.bones}


def restore(rig, pose):
    for bone in rig.pose.bones:
        location, rotation, scale = pose[bone.name]
        bone.location, bone.rotation_quaternion, bone.scale = location.copy(), rotation.copy(), scale.copy()
    bpy.context.view_layer.update()


def aim(rig, name, child, direction):
    bone = rig.pose.bones[name]
    delta = (rig.pose.bones[child].head - bone.head).normalized().rotation_difference(Vector(direction).normalized())
    matrix = delta.to_matrix().to_4x4() @ bone.matrix
    matrix.translation = bone.head
    bone.matrix = matrix
    bpy.context.view_layer.update()


def move_pelvis(rig, position):
    bone = rig.pose.bones["Pelvis"]
    matrix = bone.matrix.copy()
    matrix.translation = Vector(position)
    bone.matrix = matrix
    bpy.context.view_layer.update()


def two_bone(rig, root, middle, end, target, pole):
    origin = rig.pose.bones[root].head.copy()
    first = (rig.pose.bones[middle].head - origin).length
    second = (rig.pose.bones[end].head - rig.pose.bones[middle].head).length
    vector = Vector(target) - origin
    distance = max(abs(first - second) + 1e-5, min(vector.length, (first + second) * .999))
    direction = vector.normalized()
    bend = Vector(pole) - direction * Vector(pole).dot(direction)
    if bend.length < 1e-6:
        bend = direction.cross(Vector((1, 0, 0)))
    bend.normalize()
    along = (first * first + distance * distance - second * second) / (2 * distance)
    elbow = origin + direction * along + bend * math.sqrt(max(0, first * first - along * along))
    aim(rig, root, middle, elbow - origin)
    aim(rig, middle, end, origin + direction * distance - rig.pose.bones[middle].head)
    return (rig.pose.bones[end].head - Vector(target)).length * 100


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == HERO_HASH
    protected = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in [SOURCE, PILOT, ROOT / "ContentSource/Animation/PilotMesh.glb"]}
    original, original_binary = read_glb(SOURCE)
    pilot, pilot_binary = read_glb(PILOT)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    rig = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    rig.animation_data_clear()
    for bone in rig.pose.bones:
        bone.rotation_mode = "QUATERNION"
    apply_animation(rig, pilot, pilot_binary, 0.0)
    seated = capture(rig)
    apply_animation(rig, original, original_binary, WALK_TIME)
    walking = capture(rig)
    ankle_targets = {side: rig.pose.bones[side + "_Ankle"].head.copy() for side in ("L", "R")}
    ankle_rotations = {side: rig.pose.bones[side + "_Ankle"].matrix.to_quaternion() for side in ("L", "R")}
    walk_pelvis = rig.pose.bones["Pelvis"].head.copy()
    poses = [(0.0, seated)]
    reach_errors = []

    restore(rig, seated)
    for side, sign in (("L", 1), ("R", -1)):
        aim(rig, side + "_Shoulder", side + "_Elbow", (sign * .25, -.25, -1))
        aim(rig, side + "_Elbow", side + "_Wrist", (sign * .15, -.5, .2))
    rig.pose.bones["Head"].rotation_quaternion.rotate(Quaternion((0, 1, 0), -.10))
    poses.append((.18, capture(rig)))

    restore(rig, seated)
    move_pelvis(rig, (0, -.015, .005))
    for side, sign in (("L", 1), ("R", -1)):
        target = (sign * .16, -.005, .065)
        error = two_bone(rig, side + "_Shoulder", side + "_Elbow", side + "_Wrist", target, (sign, .25, 0))
        reach_errors.append({"side": side, "nominal_brace_reach_error_cm": error})
    poses.append((.42, capture(rig)))

    restore(rig, walking)
    move_pelvis(rig, (walk_pelvis.x, walk_pelvis.y - .025, walk_pelvis.z + .15))
    for side, sign in (("L", 1), ("R", -1)):
        aim(rig, side + "_Shoulder", side + "_Elbow", (sign * .2, .1, -1))
        aim(rig, side + "_Elbow", side + "_Wrist", (0, -.3, -1))
    poses.append((.82, capture(rig)))

    restore(rig, walking)
    move_pelvis(rig, (walk_pelvis.x, walk_pelvis.y, walk_pelvis.z + .10))
    for side, sign in (("L", 1), ("R", -1)):
        aim(rig, side + "_Hip", side + "_Knee", (sign * .12, -.65, -.8))
        aim(rig, side + "_Knee", side + "_Ankle", (0, .8, -.6))
        aim(rig, side + "_Shoulder", side + "_Elbow", (sign * .9, -.2, -.6))
        aim(rig, side + "_Elbow", side + "_Wrist", (sign * .25, -.9, -.2))
    poses.append((1.12, capture(rig)))

    restore(rig, walking)
    for side, sign in (("L", 1), ("R", -1)):
        aim(rig, side + "_Shoulder", side + "_Elbow", (sign * .65, -.35, -.8))
        aim(rig, side + "_Elbow", side + "_Wrist", (sign * .15, -.8, -.4))
    poses.append((1.60, capture(rig)))

    restore(rig, walking)
    move_pelvis(rig, (walk_pelvis.x, walk_pelvis.y - .035, walk_pelvis.z - .105))
    for side, sign in (("L", 1), ("R", -1)):
        two_bone(rig, side + "_Hip", side + "_Knee", side + "_Ankle", ankle_targets[side], (sign * .2, -1, .1))
        ankle = rig.pose.bones[side + "_Ankle"]
        ankle.matrix = Matrix.LocRotScale(ankle.head, ankle_rotations[side], Vector((1, 1, 1)))
        aim(rig, side + "_Shoulder", side + "_Elbow", (sign * .35, -.5, -.9))
        aim(rig, side + "_Elbow", side + "_Wrist", (0, -.8, -.4))
    poses.append((1.82, capture(rig)))
    poses.append((2.4, walking))

    count = round(DURATION * FPS) + 1
    samples = {bone.name: {"translation": [], "rotation": [], "scale": []} for bone in rig.pose.bones}
    inverse = CONVERSION.inverted()
    measurements = []
    for frame in range(count):
        seconds = frame / FPS
        index = min(len(poses) - 2, max(0, bisect.bisect_right([p[0] for p in poses], seconds) - 1))
        t0, a = poses[index]
        t1, b = poses[index + 1]
        alpha = max(0, min(1, (seconds - t0) / (t1 - t0)))
        alpha = alpha * alpha * (3 - 2 * alpha)
        mixed = {name: (a[name][0].lerp(b[name][0], alpha), a[name][1].slerp(b[name][1], alpha), a[name][2].lerp(b[name][2], alpha)) for name in a}
        restore(rig, mixed)
        if 1.60 <= seconds <= 2.4:
            for side, sign in (("L", 1), ("R", -1)):
                two_bone(rig, side + "_Hip", side + "_Knee", side + "_Ankle", ankle_targets[side], (sign * .2, -1, .1))
                ankle = rig.pose.bones[side + "_Ankle"]
                ankle.matrix = Matrix.LocRotScale(ankle.head, ankle_rotations[side], Vector((1, 1, 1)))
                bpy.context.view_layer.update()
        if frame == count - 1:
            restore(rig, walking)
        joints = {bone.name: bone.matrix @ bone.bone.matrix_local.inverted() @ Matrix.Translation(bone.bone.head_local) for bone in rig.pose.bones}
        for bone in rig.pose.bones:
            local = joints[bone.parent.name].inverted() @ joints[bone.name] if bone.parent else joints[bone.name]
            location, rotation, scale = (inverse @ local @ CONVERSION).decompose()
            samples[bone.name]["translation"].extend(location)
            samples[bone.name]["rotation"].extend((rotation.x, rotation.y, rotation.z, rotation.w))
            samples[bone.name]["scale"].extend(scale)
        measurements.append({"seconds": seconds, "sockets_blender_m": {name: list(rig.pose.bones[name].head) for name in ("Pelvis", "Head", "L_Wrist", "R_Wrist", "L_Ankle", "R_Ankle", "L_Foot", "R_Foot")}})

    document, binary = original, original_binary
    original_length = len(binary)
    def append(values, kind, limits=False):
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        payload = struct.pack("<" + "f" * len(values), *values)
        binary.extend(payload)
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": offset, "byteLength": len(payload)})
        entry = {"bufferView": view, "componentType": 5126, "count": count, "type": kind}
        if limits:
            entry["min"], entry["max"] = [0], [DURATION]
        result = len(document["accessors"])
        document["accessors"].append(entry)
        return result
    times = append([i / FPS for i in range(count)], "SCALAR", True)
    clip = {"name": "A_Disembark", "channels": [], "samplers": []}
    names = {node.get("name"): i for i, node in enumerate(document["nodes"])}
    for name, tracks in samples.items():
        for path, values in tracks.items():
            output = append(values, "VEC4" if path == "rotation" else "VEC3")
            index = len(clip["samplers"])
            clip["samplers"].append({"input": times, "output": output, "interpolation": "LINEAR"})
            clip["channels"].append({"sampler": index, "target": {"node": names[name], "path": path}})
    document["animations"] = [clip]
    document["buffers"][0]["byteLength"] = len(binary)
    encoded = json.dumps(document, separators=(",", ":")).encode("utf-8")
    encoded += b" " * ((-len(encoded)) % 4)
    binary.extend(b"\0" * ((-len(binary)) % 4))
    output = OUT / "Disembark.glb"
    output.write_bytes(struct.pack("<III", 0x46546C67, 2, 28 + len(encoded) + len(binary)) + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded + struct.pack("<II", len(binary), 0x004E4942) + binary)
    for path, digest in protected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    original_check, original_check_binary = read_glb(SOURCE)
    for field in ("nodes", "skins", "meshes", "materials", "images"):
        assert document[field] == original_check[field], field
    assert binary[:original_length] == original_check_binary
    record = {"status": "AUTHORED_SOURCE_NOT_UNREAL_OR_VISUAL_ACCEPTANCE", "seconds": DURATION, "fps": FPS, "frames": count, "loop": False,
              "clip": "A_Disembark", "animation_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "protected_source_hashes": protected,
              "bones": len(rig.pose.bones), "channels": len(clip["channels"]), "original_geometry_skin_materials_unchanged": True,
              "coordinates": "glTF metres/Y-up, converted from Blender Z-up using original joint basis; Unreal supplies centimetre conversion",
              "start_matches": "A_Pilot at0.0s on shared skeleton; pilot-only tail mesh compatibility NOT established",
              "end_matches": {"animation": "A_Walk", "seconds": WALK_TIME, "original_walker_mesh": True},
              "root_motion_extraction": False, "actor_world_travel": "Runtime-owned; clip contains local pelvis compression, not the bay-to-floor trajectory",
              "markers_seconds": {"controls_release": .18, "brace": .42, "rise": .82, "hop_tuck": 1.12, "deck_contact": 1.60, "compression": 1.82, "locomotion_handoff": 2.4},
              "nominal_brace_measurements": reach_errors, "pose_measurements": measurements,
              "pelvis_gltf_start_end": {path: {"start": values[:4 if path == "rotation" else 3], "end": values[-4 if path == "rotation" else -3:]} for path, values in samples["Pelvis"].items()},
              "mesh_scale": 1.0, "armature_object_matrix_identity": all(abs(rig.matrix_world[row][column] - (1 if row == column else 0)) < 1e-6 for row in range(4) for column in range(4)), "pelvis_rotation_order": "glTF quaternion x,y,z,w",
              "limitations": ["Original tail has known limb-weight deformation during seated/exit poses", "Pilot scale1.5 versus walker scale1.0 requires occluded handoff or reviewed scale resolution", "Contact targets are source-space authoring guides, not verified ship/deck contacts", "No Unreal import, actor route, collision, camera, root-motion setting or gameplay validation"]}
    (OUT / "Disembark.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("Authored", output, "SHA256", record["animation_sha256"])


if __name__ == "__main__":
    main()