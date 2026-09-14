"""Separate tail-base repair candidate. Original hero and existing pilot derivative stay unchanged.

Run with the owner's existing Blender background Python. --mask-only renders
an unposed selection review without writing a derived GLB. Default writes a
separate GLB, preserving the supplied topology, UVs, materials and skeleton.
"""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "model-rigged.glb"
PILOT = ROOT / "ContentSource/Animation/Pilot.glb"
OUT = ROOT / "ContentSource/Animation"
EXPECTED = "c106b51d3463130be49e80f7e738f52be931f80dd73e15f1cfa53b07d99bfc91"
CONVERSION = Matrix.Rotation(math.pi / 2, 4, "X")


def read_glb(path):
    raw = path.read_bytes()
    size = struct.unpack_from("<I", raw, 12)[0]
    return json.loads(raw[20:20 + size]), bytearray(raw[28 + size:])


def accessor(document, binary, index):
    entry = document["accessors"][index]
    view = document["bufferViews"][entry["bufferView"]]
    size = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[entry["type"]]
    dtype = {5126: np.dtype("<f4"), 5125: np.dtype("<u4"), 5123: np.dtype("<u2"), 5121: np.dtype("u1")}[entry["componentType"]]
    assert not entry.get("sparse"), "Sparse accessors need explicit handling"
    offset = view.get("byteOffset", 0) + entry.get("byteOffset", 0)
    stride = view.get("byteStride", size * dtype.itemsize)
    return np.ndarray((entry["count"], size), dtype=dtype, buffer=binary, offset=offset, strides=(stride, dtype.itemsize))


def append_accessor(document, binary, values, component_type, kind, bounds=False):
    values = np.ascontiguousarray(values)
    while len(binary) % 4:
        binary.append(0)
    offset = len(binary)
    payload = values.tobytes()
    binary.extend(payload)
    view = len(document["bufferViews"])
    document["bufferViews"].append({"buffer": 0, "byteOffset": offset, "byteLength": len(payload)})
    entry = {"bufferView": view, "componentType": component_type, "count": len(values), "type": kind}
    if bounds:
        entry["min"], entry["max"] = values.min(axis=0).tolist(), values.max(axis=0).tolist()
    index = len(document["accessors"])
    document["accessors"].append(entry)
    return index


def render_review(mesh, rig, selected, mask):
    scene = bpy.context.scene
    if mask:
        rig.data.pose_position = "REST"
        neutral = bpy.data.materials.new("MaskReviewNeutral")
        neutral.diffuse_color = (.16, .22, .26, 1)
        neutral.use_nodes = True
        neutral.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = neutral.diffuse_color
        highlight = bpy.data.materials.new("MaskReviewTail")
        highlight.diffuse_color = (.95, .06, .5, 1)
        highlight.use_nodes = True
        highlight.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = highlight.diffuse_color
        mesh.data.materials.clear()
        mesh.data.materials.append(neutral)
        mesh.data.materials.append(highlight)
        for polygon in mesh.data.polygons:
            polygon.material_index = int(any(selected[i] for i in polygon.vertices))
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1200, 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("PreviewWorld")
    scene.world.color = (.08, .08, .08)
    for location, energy, size in [((2, -2, 3), 450, 4), ((-2, 1, 2), 500, 3), ((1, 3, 2), 400, 3)]:
        data = bpy.data.lights.new("PreviewArea", "AREA")
        data.energy, data.shape, data.size = energy, "DISK", size
        light = bpy.data.objects.new("PreviewArea", data)
        scene.collection.objects.link(light)
        light.location = location
        light.rotation_euler = (Vector((0, 0, 0)) - light.location).to_track_quat("-Z", "Y").to_euler()
    data = bpy.data.cameras.new("PreviewCamera")
    camera = bpy.data.objects.new("PreviewCamera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    data.type, data.ortho_scale = "ORTHO", 1.5
    for name, location in (("Rear", (1.3, 2.2, .8)), ("Front", (1.3, -2.2, .8))):
        camera.location = location
        camera.rotation_euler = (Vector((0, .02, .03)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(ROOT / "ContentSource/TailCandidatePreview" / ("CandidateTail" + ("Mask" if mask else "Proposal") + name + ".png"))
        bpy.ops.render.render(write_still=True)


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    protected_paths = [SOURCE, PILOT, OUT / "PilotMesh.glb"]
    protected = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in protected_paths}
    document, binary = read_glb(PILOT)
    source_document, source_binary = read_glb(SOURCE)
    primitive = document["meshes"][0]["primitives"][0]
    source_primitive = source_document["meshes"][0]["primitives"][0]
    attrs = primitive["attributes"]
    positions = accessor(document, binary, attrs["POSITION"]).copy()
    original_positions = accessor(source_document, source_binary, source_primitive["attributes"]["POSITION"])
    assert np.array_equal(positions, original_positions)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(PILOT))
    mesh = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH")
    rig = next(obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE")
    rest_positions = np.array([vertex.co[:] for vertex in mesh.data.vertices], dtype=np.float32)
    converted = np.stack((positions[:, 0], -positions[:, 2], positions[:, 1]), axis=1)
    assert len(rest_positions) == len(positions) and np.max(np.abs(rest_positions - converted)) < 2e-6, "Importer changed vertex order"
    # Select whole connected fur islands so a geometric cutoff cannot stretch
    # individual triangles between repaired curl and unrepaired skin.
    selected = np.zeros(len(rest_positions), dtype=bool)
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.verts.ensure_lookup_table()
    for seed in bm.verts:
        if seed.tag:
            continue
        seed.tag = True
        stack, island = [seed], []
        while stack:
            vertex = stack.pop()
            island.append(vertex.index)
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if not other.tag:
                    other.tag = True
                    stack.append(other)
        coords = rest_positions[island]
        if coords[:, 1].min() > -.04 and coords[:, 1].max() > .10 and (coords[:, 2].max() > -.10 or coords[:, 2].min() > -.18):
            selected[island] = True
    bm.free()
    selection = json.loads((ROOT / "ContentSource/TailCandidatePreview/Selection.json").read_text())
    assert selection["source_sha256"] == EXPECTED and selection["candidate_vertices"] == 144133
    for island in selection["additional_islands"]:
        selected[island["indices"]] = True
    indices = np.flatnonzero(selected).tolist()
    assert len(indices) == 144133, "Tail candidate selection changed from inspected overlay"
    if "--mask-only" in sys.argv:
        render_review(mesh, rig, selected, True)
        return
    scene = bpy.context.scene
    scene.frame_set(scene.render.fps)
    skin = rig.pose.bones["Pelvis"].matrix @ rig.data.bones["Pelvis"].matrix_local.inverted()
    # Keep the original curl rigid and upright just behind the seated pelvis.
    # Compensate only this pilot-specific mesh for the seated pelvis basis.
    desired = Matrix.Translation((0, .00, .12))
    repair = skin.inverted() @ desired
    normal_repair = repair.to_3x3().inverted().transposed()
    for index in indices:
        mesh.data.vertices[index].co = repair @ mesh.data.vertices[index].co
    for group in mesh.vertex_groups:
        group.remove(indices)
    mesh.vertex_groups["Pelvis"].add(indices, 1.0, "REPLACE")
    bpy.context.view_layer.update()
    reference = np.array([list((skin @ mesh.data.vertices[index].co)) for index in indices], dtype=np.float64)
    max_tail_drift_cm = 0.0
    for seconds in np.linspace(0, 4, 17):
        frame = float(seconds * scene.render.fps)
        scene.frame_set(int(frame), subframe=frame - int(frame))
        matrix = rig.pose.bones["Pelvis"].matrix @ rig.data.bones["Pelvis"].matrix_local.inverted()
        actual = np.array([list((matrix @ mesh.data.vertices[index].co)) for index in indices], dtype=np.float64)
        max_tail_drift_cm = max(max_tail_drift_cm, float(np.linalg.norm(actual - reference, axis=1).max() * 100))
    scene.frame_set(scene.render.fps)
    normals = accessor(document, binary, attrs["NORMAL"]).copy()
    joints = accessor(document, binary, attrs["JOINTS_0"]).copy()
    weights = accessor(document, binary, attrs["WEIGHTS_0"]).copy()
    pelvis_node = next(i for i, node in enumerate(document["nodes"]) if node.get("name") == "Pelvis")
    pelvis_index = document["skins"][0]["joints"].index(pelvis_node)
    for index in indices:
        v = mesh.data.vertices[index].co
        positions[index] = (v.x, v.z, -v.y)
        n = normal_repair @ Vector((float(normals[index, 0]), -float(normals[index, 2]), float(normals[index, 1])))
        n.normalize()
        normals[index] = (n.x, n.z, -n.y)
    joints[selected] = (pelvis_index, 0, 0, 0)
    weights[selected] = (1, 0, 0, 0)
    attrs["POSITION"] = append_accessor(document, binary, positions, 5126, "VEC3", True)
    attrs["NORMAL"] = append_accessor(document, binary, normals, 5126, "VEC3")
    attrs["JOINTS_0"] = append_accessor(document, binary, joints.astype("<u2"), 5123, "VEC4")
    attrs["WEIGHTS_0"] = append_accessor(document, binary, weights.astype("<f4"), 5126, "VEC4")
    # Retain no animation import side effects. Runtime reuses existing A_Pilot.
    document.pop("animations", None)
    if "TANGENT" in attrs:
        raise AssertionError("Source has tangent accessor; explicitly rotate it before exporting")
    assert document["nodes"] == source_document["nodes"] and document["skins"] == source_document["skins"]
    unchanged = {}
    for key in ("TEXCOORD_0",):
        assert np.array_equal(accessor(document, binary, attrs[key]), accessor(source_document, source_binary, source_primitive["attributes"][key]))
        unchanged[key] = hashlib.sha256(accessor(document, binary, attrs[key]).tobytes()).hexdigest()
    assert primitive["indices"] == source_primitive["indices"]
    assert np.array_equal(accessor(document, binary, primitive["indices"]), accessor(source_document, source_binary, source_primitive["indices"]))
    unchanged["indices"] = hashlib.sha256(accessor(document, binary, primitive["indices"]).tobytes()).hexdigest()
    assert np.array_equal(positions[~selected], original_positions[~selected])
    for attribute, actual in (("NORMAL", normals), ("JOINTS_0", joints), ("WEIGHTS_0", weights)):
        assert np.array_equal(actual[~selected], accessor(source_document, source_binary, source_primitive["attributes"][attribute])[~selected]), "Changed body " + attribute
    assert document["materials"] == source_document["materials"] and document["images"] == source_document["images"]
    document["buffers"][0]["byteLength"] = len(binary)
    encoded = json.dumps(document, separators=(",", ":")).encode("utf-8")
    encoded += b" " * ((-len(encoded)) % 4)
    binary.extend(b"\0" * ((-len(binary)) % 4))
    output = OUT / "TailCandidate.glb"
    output.write_bytes(struct.pack("<III", 0x46546C67, 2, 28 + len(encoded) + len(binary)) + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded + struct.pack("<II", len(binary), 0x004E4942) + binary)
    record = {"status": "SEPARATE_TAIL_CANDIDATE_REQUIRES_DEFORMATION_AND_UNREAL_REVIEW", "source_glb_sha256": EXPECTED,
              "derivative_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "vertices": len(positions),
              "tail_vertices_changed": len(indices), "tail_max_vertex_drift_cm_17_samples": round(max_tail_drift_cm, 8), "mask_blender_m": {"whole_connected_fur_islands": True, "min_y_greater_than": -.04, "max_y_greater_than": .10, "old_max_z_greater_than": -.10, "or_island_min_z_greater_than": -.18, "reviewed_root_bridge_vertices": 303, "selection_receipt": "ContentSource/TailCandidatePreview/Selection.json"},
              "target_tail_translation_m": [0, 0, .12], "joint": "Pelvis", "shared_skeleton_unchanged": True,
              "unchanged_accessor_hashes": unchanged, "body_vertices_unchanged": int(np.count_nonzero(~selected)),
              "notes": "Separate candidate extending the reviewed tail mask by3947 tail-base vertices. Source and existing PilotMesh stay unchanged. Tail curl copied rigidly from original rest shape. Only selected tail position/normal/weights/joints changed; no texture, UV, triangle or material change. Candidate for A_Pilot/A_Disembark/A_Walk pending sampled deformation and Unreal review. Preserves original tail topology and appearance; no new art."}
    (OUT / "TailCandidate.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    for path, digest in protected.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    render_review(mesh, rig, selected, False)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
