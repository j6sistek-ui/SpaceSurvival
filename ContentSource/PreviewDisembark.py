"""Fresh-import pose/deformation checks and source previews for Disembark.glb.

Run in Blender background. Writes only DisembarkPreview images and receipts.
These are source-rig diagnostics, not Unreal integration or art acceptance.
"""
import hashlib
import json
from pathlib import Path
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
WALK = "--walk" in sys.argv
CANDIDATE = "--candidate" in sys.argv
DERIVATIVE = "--pilot-mesh" in sys.argv or CANDIDATE
SOURCE = ROOT / ("model-rigged.glb" if WALK else "ContentSource/Animation/Disembark.glb")
OUT = ROOT / "ContentSource/DisembarkPreview"
if DERIVATIVE:
    OUT = (ROOT / "ContentSource/TailCandidatePreview" / ("Walk" if WALK else "Exit")) if CANDIDATE else OUT / ("PilotMeshWalk" if WALK else "PilotMeshExit")
TIMES = (0, .4, .8, 1.2, 1.6, 2, 74 / 30) if WALK else (0, .4, .8, 1.1, 1.6, 1.8, 2.4)


def sample(scene, seconds):
    frame = seconds * scene.render.fps
    scene.frame_set(int(frame), subframe=frame - int(frame))
    bpy.context.view_layer.update()


def mesh_coordinates(mesh):
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = evaluated.to_mesh()
    coords = np.empty(len(data.vertices) * 3, dtype=np.float32)
    data.vertices.foreach_get("co", coords)
    evaluated.to_mesh_clear()
    return coords.reshape((-1, 3))


def tail_mask(mesh):
    coords = np.array([v.co[:] for v in mesh.data.vertices], dtype=np.float32)
    selected = np.zeros(len(coords), dtype=bool)
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
        points = coords[island]
        if points[:, 1].min() > -.04 and points[:, 1].max() > .10 and (points[:, 2].max() > -.10 or (CANDIDATE and points[:, 2].min() > -.18)):
            selected[island] = True
    bm.free()
    if CANDIDATE:
        selection = json.loads((ROOT / "ContentSource/TailCandidatePreview/Selection.json").read_text())
        for island in selection["additional_islands"]:
            selected[island["indices"]] = True
    assert selected.sum() == (144133 if CANDIDATE else 140186), "Tail selection differs from previously inspected whole-fur islands"
    return selected


def bounds(coords):
    return {"min_m": coords.min(axis=0).tolist(), "max_m": coords.max(axis=0).tolist()}


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    authored = json.loads((ROOT / "ContentSource/Animation/Disembark.json").read_text())
    if not WALK:
        assert authored["animation_sha256"] == source_hash
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    rig = next(obj for obj in scene.objects if obj.type == "ARMATURE")
    mesh = next(obj for obj in scene.objects if obj.type == "MESH")
    mask = tail_mask(mesh)
    original_mesh = mesh
    derivative_hash = None
    if DERIVATIVE:
        derivative = ROOT / ("ContentSource/Animation/TailCandidate.glb" if CANDIDATE else "ContentSource/Animation/PilotMesh.glb")
        derivative_hash = hashlib.sha256(derivative.read_bytes()).hexdigest()
        prior_objects = set(scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(derivative))
        added = [obj for obj in scene.objects if obj not in prior_objects]
        mesh = next(obj for obj in added if obj.type == "MESH")
        derivative_rig = next(obj for obj in added if obj.type == "ARMATURE")
        assert set(b.name for b in derivative_rig.data.bones) == set(b.name for b in rig.data.bones)
        assert max(abs(derivative_rig.data.bones[b.name].matrix_local[r][c] - b.matrix_local[r][c]) for b in rig.data.bones for r in range(4) for c in range(4)) < 1e-6
        world_matrix = mesh.matrix_world.copy()
        mesh.parent = rig
        mesh.matrix_world = world_matrix
        for modifier in mesh.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = rig
        bpy.data.objects.remove(derivative_rig, do_unlink=True)
        original_mesh.hide_render = True
    body_error, tail_rigidity_error = 0.0, 0.0
    tail_rest = np.array([v.co[:] for v in mesh.data.vertices], dtype=np.float32)[mask]
    records, previous = [], None
    max_roundtrip_error, max_step = 0.0, {"body_cm": 0.0, "tail_cm": 0.0, "frame": 0}
    end_targets = authored["pose_measurements"][-1]["sockets_blender_m"]
    max_ankle_drift = 0.0
    for frame in range(75 if WALK else 73):
        seconds = frame / 30
        sample(scene, seconds)
        positions = mesh_coordinates(mesh)
        errors = [0.0] if WALK else [(Vector(point) - rig.pose.bones[name].head).length * 100 for name, point in authored["pose_measurements"][frame]["sockets_blender_m"].items()]
        max_roundtrip_error = max(max_roundtrip_error, max(errors))
        sockets = {name: list(rig.pose.bones[name].head) for name in end_targets}
        ankle_drift = max((Vector(end_targets[side + "_Ankle"]) - rig.pose.bones[side + "_Ankle"].head).length * 100 for side in ("L", "R"))
        if not WALK and seconds >= 1.6:
            max_ankle_drift = max(max_ankle_drift, ankle_drift)
        row = {"frame": frame, "seconds": seconds, "all_vertices": bounds(positions), "tail_vertices": bounds(positions[mask]), "body_vertices": bounds(positions[~mask]), "sockets_blender_m": sockets, "contact_ankle_drift_cm": ankle_drift if not WALK and seconds >= 1.6 else None}
        if DERIVATIVE:
            original_positions = mesh_coordinates(original_mesh)
            skin = np.array(rig.pose.bones["Pelvis"].matrix @ rig.data.bones["Pelvis"].matrix_local.inverted())
            expected_rigid = tail_rest @ skin[:3, :3].T + skin[:3, 3]
            rigidity_error = float(np.linalg.norm(positions[mask] - expected_rigid, axis=1).max() * 100)
            tail_rigidity_error = max(tail_rigidity_error, rigidity_error)
            row["tail_vs_rigid_pelvis_max_vertex_error_cm"] = rigidity_error
            error = float(np.linalg.norm(positions[~mask] - original_positions[~mask], axis=1).max() * 100)
            body_error = max(body_error, error)
            row["body_vs_original_max_vertex_error_cm"] = error
            row["original_tail_bounds"] = bounds(original_positions[mask])
            # Joint-axis proximity is a diagnostic, not mesh intersection proof.
            distances = []
            tail = positions[mask]
            for side in ("L", "R"):
                for first, second in (("Hip", "Knee"), ("Knee", "Ankle")):
                    a = np.array(rig.pose.bones[side + "_" + first].head)
                    b = np.array(rig.pose.bones[side + "_" + second].head)
                    direction = b - a
                    alpha = np.clip(((tail - a) @ direction) / (direction @ direction), 0, 1)
                    closest = a + alpha[:, None] * direction
                    distances.append(np.linalg.norm(tail - closest, axis=1))
            row["tail_min_distance_to_leg_joint_axis_cm"] = float(np.min(distances) * 100)
        if previous is not None:
            delta = np.linalg.norm(positions - previous, axis=1) * 100
            row["max_vertex_step_cm"] = {"body": float(delta[~mask].max()), "tail": float(delta[mask].max())}
            if float(delta[mask].max()) > max_step["tail_cm"]:
                max_step = {"body_cm": float(delta[~mask].max()), "tail_cm": float(delta[mask].max()), "frame": frame}
        records.append(row)
        previous = positions
    assert max_roundtrip_error < .01, "Fresh GLB import changed authored joint transforms"
    images = [str(path.relative_to(ROOT)) for path in sorted(OUT.glob("*.png"))]
    if "--measure-only" not in sys.argv:
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = 480, 600
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.world = bpy.data.worlds.new("DisembarkDiagnosticWorld")
        scene.world.color = (.06, .06, .06)
        for location, energy, size in [((2, -2, 3), 400, 4), ((-2, 1, 2), 450, 3), ((1, 3, 2), 350, 3)]:
            data = bpy.data.lights.new("DiagnosticArea", "AREA")
            data.energy, data.shape, data.size = energy, "DISK", size
            light = bpy.data.objects.new("DiagnosticArea", data)
            scene.collection.objects.link(light)
            light.location = location
            light.rotation_euler = (Vector((0, 0, 0)) - light.location).to_track_quat("-Z", "Y").to_euler()
        data = bpy.data.cameras.new("DiagnosticCamera")
        camera = bpy.data.objects.new("DiagnosticCamera", data)
        scene.collection.objects.link(camera)
        scene.camera = camera
        data.type, data.ortho_scale = "ORTHO", 1.95
        curve = bpy.data.curves.new("TimeLabel", "FONT")
        curve.size, curve.align_x = .055, "CENTER"
        label = bpy.data.objects.new("TimeLabel", curve)
        scene.collection.objects.link(label)
        mat = bpy.data.materials.new("DiagnosticLabel")
        mat.diffuse_color = (.85, .85, .85, 1)
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.85, .85, .85, 1)
        curve.materials.append(mat)
        images = []
        for name, location in (("Front", (0, -3, .0)), ("Side", (3, 0, .0)), ("Rear", (0, 3, .0))):
            camera.location = location
            target = Vector((0, 0, -.10))
            camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
            label.rotation_euler = camera.rotation_euler
            label.location = target + camera.rotation_euler.to_quaternion() @ Vector((0, -.89, .1))
            tiles = []
            for seconds in TIMES:
                sample(scene, seconds)
                curve.body = name + " " + format(seconds, ".2f") + " s"
                output = OUT / (name + "_" + str(round(seconds * 100)).zfill(3) + ".png")
                scene.render.filepath = str(output)
                bpy.ops.render.render(write_still=True)
                img = bpy.data.images.load(str(output), check_existing=False)
                pixels = np.empty(480 * 600 * 4, dtype=np.float32)
                img.pixels.foreach_get(pixels)
                tiles.append(pixels.reshape((600, 480, 4)))
                bpy.data.images.remove(img)
                images.append(str(output.relative_to(ROOT)))
            sheet = bpy.data.images.new("Disembark" + name + "ContactSheet", width=480 * len(TIMES), height=600, alpha=True)
            sheet.pixels.foreach_set(np.concatenate(tiles, axis=1).reshape(-1))
            sheet.filepath_raw = str(OUT / (name + ".png"))
            sheet.file_format = "PNG"
            sheet.save()
            bpy.data.images.remove(sheet)
            images.append(str((OUT / (name + ".png")).relative_to(ROOT)))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
    receipt = {"status": "BLENDER_SOURCE_PREVIEW_NOT_UNREAL_OR_QUALITY_ACCEPTANCE", "animation_sha256": source_hash,
               "clip": "A_Walk" if WALK else "A_Disembark", "derivative_sha256": derivative_hash, "body_vs_original_max_vertex_error_cm": body_error if DERIVATIVE else None, "mesh_scale": 1.0, "tail_vs_rigid_pelvis_max_vertex_error_cm": tail_rigidity_error if DERIVATIVE else None,
               "blender_version": bpy.app.version_string, "frames_checked": 75 if WALK else 73, "vertices": len(mask), "tail_vertices": int(mask.sum()),
               "source_roundtrip_max_socket_error_cm": None if WALK else max_roundtrip_error, "contact_1_6_to_2_4_max_ankle_drift_cm": None if WALK else max_ankle_drift,
               "peak_tail_frame_step": max_step, "preview_seconds": TIMES, "images": images, "samples": records,
               "limitations": [("Separate refined tail candidate under source-only evaluation" if CANDIDATE else "Existing pilot-only mesh is being evaluated beyond its previous usage; no original asset is altered") if DERIVATIVE else "Original tail/limb weights retained; malformed tail is not repaired by this animation", "Stationary source-space render excludes actor travel, cockpit/deck geometry, scale handoff and collision", "Ankle lock measurements do not prove sole/deck contact", "No Unreal import or runtime presentation acceptance"]}
    (OUT / "Measurements.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("DISembark source preview complete", json.dumps({key: receipt[key] for key in ("animation_sha256", "source_roundtrip_max_socket_error_cm", "contact_1_6_to_2_4_max_ankle_drift_cm", "peak_tail_frame_step")}))


if __name__ == "__main__":
    main()