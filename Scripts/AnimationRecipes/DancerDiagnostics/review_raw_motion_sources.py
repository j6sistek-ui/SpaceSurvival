"""Read-only GLB motion inventory, fixed-camera stills and source joint samples.

Run in hidden background Blender, passing --out and one or more --source NAME=PATH.
This deliberately does not retarget, repair, save the scene or adopt motion.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--source', action='append', required=True)
    parser.add_argument('--sample-hz', type=float, default=2)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert 0 < args.sample_hz <= 10
    args.out.mkdir(parents=True, exist_ok=True)
    for specification in args.source:
        name, supplied = specification.split('=', 1)
        assert name.replace('_', '').isalnum(), 'Use a plain output label'
        source = Path(supplied).resolve(strict=True)
        before = digest(source)
        folder = args.out / name
        folder.mkdir(exist_ok=False)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        scene.render.fps = 60
        bpy.ops.import_scene.gltf(filepath=str(source))
        rigs = [o for o in scene.objects if o.type == 'ARMATURE' and o.animation_data
                and o.animation_data.action]
        assert len(rigs) == 1, [(o.name, o.animation_data.action.name) for o in rigs]
        rig = rigs[0]
        action = rig.animation_data.action
        first, last = map(float, action.frame_range)
        duration = (last-first)/60

        def pose(seconds):
            frame = first + seconds*60
            scene.frame_set(math.floor(frame), subframe=frame % 1)
            bpy.context.view_layer.update()
            return {b.name: rig.matrix_world @ b.matrix for b in rig.pose.bones}

        times = np.r_[np.arange(0, duration, 1/60), duration]
        names = [b.name for b in rig.pose.bones]
        positions, local_quats, world_quats = [], [], []
        for seconds in times:
            matrices = pose(float(seconds))
            positions.append([list(matrices[n].translation) for n in names])
            world_quats.append([list(matrices[n].to_quaternion()) for n in names])
            local_quats.append([list(rig.pose.bones[n].matrix_basis.to_quaternion()) for n in names])
        positions = np.asarray(positions)
        np.savez_compressed(folder/'Joints.npz', seconds=times, names=names,
                            positions=positions, local_quats=local_quats,
                            world_quats=world_quats)
        quats = np.asarray(local_quats)
        quats /= np.linalg.norm(quats, axis=2, keepdims=True)
        angles = np.degrees(2*np.arccos(np.clip(np.abs((quats[1:]*quats[:-1]).sum(axis=2)), 0, 1)))
        rates = angles / np.diff(times)[:, None]
        peaks = sorted([{'bone': n, 'degrees_per_second': float(rates[:, i].max()),
                         'seconds': float(times[1:][rates[:, i].argmax()])}
                        for i, n in enumerate(names)], key=lambda x: -x['degrees_per_second'])
        meshes = [o for o in scene.objects if o.type == 'MESH']
        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.color_type = 'OBJECT'
        scene.display.shading.show_cavity = False
        scene.display.shading.background_type = 'WORLD'
        scene.world = bpy.data.worlds.new('MotionReferenceReview')
        scene.world.color = (.035, .045, .055)
        scene.render.resolution_x = scene.render.resolution_y = 400
        scene.render.resolution_percentage = 100
        for obj in meshes:
            obj.color = (.55, .55, .55, 1)
        bpy.ops.object.camera_add()
        camera = bpy.context.object
        scene.camera = camera
        camera.data.type = 'ORTHO'
        still_times = np.r_[np.arange(0, duration, 1/args.sample_hz), duration]
        # Fixed framing includes every sampled skinned bounding-box corner.
        points = []
        for seconds in still_times:
            pose(float(seconds))
            deps = bpy.context.evaluated_depsgraph_get()
            for obj in meshes:
                evaluated = obj.evaluated_get(deps)
                points.extend(evaluated.matrix_world @ Vector(v) for v in evaluated.bound_box)
        for view, direction in [('front', Vector((0, -1, 0))), ('side', Vector((1, 0, 0)))]:
            view_dir = direction.normalized()
            rotation = (-view_dir).to_track_quat('-Z', 'Y')
            right, up = rotation @ Vector((1, 0, 0)), rotation @ Vector((0, 1, 0))
            projected = np.array([[p.dot(right), p.dot(up), p.dot(view_dir)] for p in points])
            low, high = projected.min(axis=0), projected.max(axis=0)
            mid = (low+high)/2
            center = right*mid[0] + up*mid[1] + view_dir*mid[2]
            extent = float(max(high[:2]-low[:2]))
            camera.location = center + view_dir*max(10, extent*3)
            camera.rotation_euler = rotation.to_euler()
            camera.data.ortho_scale = extent*1.16
            camera.data.clip_end = max(1000, extent*10)
            target = folder/view
            target.mkdir()
            for i, seconds in enumerate(still_times):
                pose(float(seconds))
                scene.render.filepath = str(target/f'{i:04d}.png')
                bpy.ops.render.render(write_still=True)
        assert digest(source) == before
        report = {'source': str(source), 'sha256': before, 'duration_seconds': duration,
                  'action': action.name, 'frames': [first, last], 'rig': rig.name,
                  'mesh_count': len(meshes), 'bone_count': len(names),
                  'sample_hz': 60, 'still_seconds': still_times.tolist(),
                  'largest_local_rotation_rates': peaks[:15],
                  'scope': 'Raw source fidelity inventory only. Rates flag inspection points; they are not anatomical limits. Front/side are fixed world directions, not inferred character-facing labels.'}
        (folder/'Inventory.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('RAW_SOURCE_REVIEW', name, duration, before, flush=True)


if __name__ == '__main__':
    main()
