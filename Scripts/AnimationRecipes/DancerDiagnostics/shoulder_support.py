import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Vexa free-floating shoulder proof; no fixed-contact or production claim."""
import math
import numpy as np
from mathutils import Vector, Matrix, Quaternion

def support_clavicles(pose, rest, descendants):
    chest = pose['spine_05'].to_quaternion() @ rest['spine_05'].to_quaternion().inverted()
    up = chest @ Vector((0, 0, 1))
    result = {}
    for side in ('l', 'r'):
        clav, upper, lower = ('clavicle_'+side, 'upperarm_'+side, 'lowerarm_'+side)
        direction = (pose[lower].translation-pose[upper].translation).normalized()
        elevation = math.asin(max(-1., min(1., direction.dot(up))))
        lift = math.radians(25)*max(0., min(1., (elevation+math.radians(10))/math.radians(90)))
        pivot = pose[clav].translation.copy()
        shoulder = pose[upper].translation.copy()
        axis = (shoulder-pivot).normalized().cross(up).normalized()
        q = Quaternion(axis, lift)
        pose[clav] = Matrix.LocRotScale(pivot, q@pose[clav].to_quaternion(), pose[clav].to_scale())
        shift = pivot+q@(shoulder-pivot)-shoulder
        for name in descendants[upper]:
            pose[name].translation += shift
        result[side] = {'elevation_deg': math.degrees(elevation), 'lift_deg': math.degrees(lift),
                        'arm_translation_m': shift.length}
    return result

def shoulder_mask(mesh, centers):
    """Spatial falloff with three-ring boundary protection for modular seams."""
    coords = np.array([tuple(mesh.matrix_world@v.co) for v in mesh.data.vertices])
    distance = np.linalg.norm(coords[:, None, :]-np.array(centers)[None, :, :], axis=2).min(axis=1)
    mask = np.clip((.22-distance)/.14, 0, 1)
    mask = mask*mask*(3-2*mask)
    edges = {}
    adjacency = [set() for _ in mesh.data.vertices]
    for polygon in mesh.data.polygons:
        for a, b in polygon.edge_keys:
            key = tuple(sorted((a, b)))
            edges[key] = edges.get(key, 0)+1
            adjacency[a].add(b); adjacency[b].add(a)
    boundary = {v for edge, count in edges.items() if count == 1 for v in edge}
    frontier = boundary.copy(); visited = boundary.copy()
    for ring, factor in enumerate((0., .25, .65)):
        for v in frontier: mask[v] *= factor
        frontier = {n for v in frontier for n in adjacency[v]}-visited
        visited |= frontier
    return mask, boundary
