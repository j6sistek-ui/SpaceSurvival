"""Render original exported library motion, without retargeting or scene saves.

Hidden Blender: -- --out DIRECTORY --mesh FILE --clip NAME=FILE [--slow 3].
The mesh and clip must have matching rest bones; source hashes are rechecked.
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
    parser.add_argument('--mesh', type=Path, required=True)
    parser.add_argument('--clip', action='append', required=True)
    parser.add_argument('--slow', type=float, default=1.)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert 1 <= args.slow <= 4
    args.out.mkdir(parents=True, exist_ok=True)
    for specification in args.clip:
        label, file = specification.split('=', 1)
        assert label.replace('_', '').isalnum()
        source = Path(file).resolve(strict=True)
        guards = {str(p.resolve()): digest(p) for p in (source, args.mesh)}
        folder = args.out/label
        folder.mkdir(exist_ok=False)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        bpy.ops.import_scene.fbx(filepath=str(args.mesh))
        body = next(o for o in scene.objects if o.type == 'ARMATURE')
        meshes = [o for o in scene.objects if o.type == 'MESH']
        before = set(scene.objects)
        bpy.ops.import_scene.fbx(filepath=str(source))
        added = set(scene.objects)-before
        rigs = [o for o in added if o.type == 'ARMATURE' and o.animation_data and o.animation_data.action]
        assert len(rigs) == 1, [o.name for o in rigs]
        animated = rigs[0]
        names = [b.name for b in body.data.bones]
        assert all(n in animated.data.bones for n in names)
        error = max(float(np.abs(np.array(body.matrix_world@body.data.bones[n].matrix_local)-
                                  np.array(animated.matrix_world@animated.data.bones[n].matrix_local)).max()) for n in names)
        assert error < 1e-4, ('Rest skeletons differ', error)
        action = animated.animation_data.action
        slot = animated.animation_data.action_slot
        fps = scene.render.fps/scene.render.fps_base
        first, last = map(float, action.frame_range)
        duration = (last-first)/fps
        body.animation_data_create()
        body.animation_data.action = action
        body.animation_data.action_slot = slot
        for obj in added:
            bpy.data.objects.remove(obj, do_unlink=True)

        def pose(seconds):
            frame = first+min(duration, seconds)*fps
            scene.frame_set(math.floor(frame), subframe=frame % 1)
            bpy.context.view_layer.update()

        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.color_type = 'OBJECT'
        scene.display.shading.show_cavity = False
        scene.display.shading.background_type = 'WORLD'
        scene.world = bpy.data.worlds.new('LibraryMotionReview')
        scene.world.color = (.035, .045, .055)
        scene.render.resolution_x = scene.render.resolution_y = 600
        scene.render.resolution_percentage = 100
        for obj in meshes:
            obj.color = (.55, .55, .55, 1)
        bpy.ops.object.camera_add()
        camera = bpy.context.object
        scene.camera = camera
        camera.data.type = 'ORTHO'
        sample_times = np.r_[np.arange(0, duration, 1/30), duration]
        points = []
        for seconds in sample_times:
            pose(float(seconds))
            deps = bpy.context.evaluated_depsgraph_get()
            for obj in meshes:
                evaluated = obj.evaluated_get(deps)
                points.extend(evaluated.matrix_world@Vector(v) for v in evaluated.bound_box)
        count = round(duration*args.slow*24)+1
        for view, direction in [('front', Vector((0,-1,0))), ('side', Vector((1,0,0)))]:
            rotation = (-direction).to_track_quat('-Z','Y')
            right, up = rotation@Vector((1,0,0)), rotation@Vector((0,1,0))
            projected = np.array([[p.dot(right),p.dot(up),p.dot(direction)] for p in points])
            low, high = projected.min(axis=0), projected.max(axis=0)
            mid = (low+high)/2
            focus = right*mid[0]+up*mid[1]+direction*mid[2]
            extent = float(max(high[:2]-low[:2]))
            camera.location = focus+direction*max(10,extent*3)
            camera.rotation_euler = rotation.to_euler()
            camera.data.ortho_scale = extent*1.16
            camera.data.clip_end = max(1000,extent*10)
            target = folder/view
            target.mkdir()
            for i in range(count):
                pose(min(duration, i/(24*args.slow)))
                scene.render.filepath = str(target/f'{i:04d}.png')
                bpy.ops.render.render(write_still=True)
        assert all(digest(Path(p)) == h for p,h in guards.items())
        report = {'sources':guards,'source_seconds':duration,'fbx_fps':fps,'slow_factor':args.slow,
                  'fps':24,'frames_per_view':count,'views':['front','side'],
                  'rest_matrix_max_error':error,'action':action.name,
                  'scope':'Original exported motion on its matching source mesh. Timing slowed only; no retarget, repair, adoption or source scene save. World camera labels do not infer facing.'}
        (folder/'Review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('LIBRARY_REVIEW',label,duration,count,error,flush=True)


if __name__ == '__main__':
    main()
