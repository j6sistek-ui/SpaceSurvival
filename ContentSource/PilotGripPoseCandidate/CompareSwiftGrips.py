"""Compare candidate animations against original Swift and fitted grip surfaces.
No scene, source asset, rig, clip or runtime asset is saved or changed.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
import AuthorPair as pair


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = [
        ROOT / 'ContentSource/SwiftCandidate/SwiftCandidate.blend',
        ROOT / 'ContentSource/AcornShipGripFit/AcornShipGripFit.blend',
        ROOT / 'ContentSource/Animation/TailCandidateV2.glb',
        OUT / 'PilotGripFit.glb',
        OUT / 'DisembarkGripFit.glb',
    ]
    protected = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    grips = {}
    for family, path in zip(('SwiftOriginal', 'Fitted'), paths[:2]):
        bpy.ops.wm.open_mainfile(filepath=str(path))
        for side, sign in (('L', '1'), ('R', '-1')):
            grips[family + side] = pair.hand.world_bvh(
                bpy.data.objects['Pilot control grip ' + sign]
            )
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(paths[2]))
    added = [o for o in bpy.context.scene.objects if o not in before]
    rig = next(o for o in added if o.type == 'ARMATURE')
    hero = next(o for o in added if o.type == 'MESH')
    rig.animation_data_clear()
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
    rig.rotation_mode = 'XYZ'
    rig.rotation_euler = (0, 0, math.pi / 2)
    rig.scale = (1.5,) * 3
    rig.location = (-.15, 0, .72)
    bpy.context.view_layer.update()
    rows = []
    for kind, path, times in (
        ('Pilot', paths[3], [0, 1, 2, 3, 4]),
        ('Exit', paths[4], [i / 60 for i in range(27)]),
    ):
        doc, raw = pair.anim.read_glb(path)
        for seconds in times:
            pair.anim.apply_animation(rig, doc, raw, seconds)
            checks = pair.overlap_evidence(hero, grips)
            rows.append({'clip': kind, 'seconds': seconds, 'grips': checks})
            print('GRIP_COMPARE_SAMPLE', kind, seconds, flush=True)
    assert all(sha(ROOT / p) == digest for p, digest in protected.items())
    record = {
        'status': 'SOURCE_SWIFT_AND_FITTED_GRIP_COMPARISON',
        'protected_sha256': protected,
        'blender': bpy.app.version_string,
        'generator_sha256': sha(Path(__file__)),
        'pilot_transform': {'position_cm': [-15, 0, 72], 'scale': 1.5, 'blender_z_degrees': 90},
        'method': 'Exact exported GLB playback; full evaluated TailV2 skin and evaluated grip surface triangles. BVH candidates filtered with bidirectional triangle-edge intersection.',
        'samples': rows,
        'limits': [
            'Counts are crossing triangle pairs, not penetration depth or grasp proximity.',
            'No continuous collision, body self-contact, main hull, or native live-phase blend validation.',
            'No asset, scene, source clip or runtime mutation; this does not authorize a Swift cockpit transplant.',
        ],
    }
    (OUT / 'SwiftGripClearance.json').write_text(
        json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n'
    )
    print('SWIFT_GRIP_CLEARANCE_FINISHED', flush=True)


if __name__ == '__main__':
    main()
