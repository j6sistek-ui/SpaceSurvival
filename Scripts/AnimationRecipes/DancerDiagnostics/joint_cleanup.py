import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Source-preserving joint corrections for the reviewed F3 rig.

This is an animation repair, not a mesh smoothing filter. Callers must confirm
rest-pose identity and inspect continuous motion/feet before using another rig.
"""
import math
from mathutils import Matrix,Quaternion,Vector

def remove_calf_axial_roll(pose,rest,parent,descendants,side):
    """Keep thigh/knee/ankle centers; remove calf roll around its length.

    Align the rest lower-leg direction (carried by the posed thigh) to the
    source ankle direction with the shortest swing. This retains the bend and
    travel but avoids the large axial rotation that pinches the knee skin.
    Descendants follow the correction, including the twist bones and toes.
    """
    calf,foot='calf_'+side,'foot_'+side
    if calf not in pose or foot not in pose:
        raise ValueError('Expected verified calf/foot mapping')
    par=parent[calf]
    base=pose[par]@rest[par].inverted()@rest[calf]
    endpoint=rest[calf].inverted()@rest[foot].translation
    neutral=(base.to_quaternion()@endpoint).normalized()
    actual=(pose[foot].translation-pose[calf].translation).normalized()
    if neutral.dot(actual)<-.98:
        raise ValueError('Near-folded singularity requires authored inspection')
    goal=(neutral.rotation_difference(actual)@base.to_quaternion()).normalized()
    correction=(goal@pose[calf].to_quaternion().inverted()).normalized()
    if correction.w<0:correction.negate()
    # Project onto the actual calf axis. Float error in near-identity matrix
    # decompositions otherwise introduces an unwanted tiny swing component.
    along=Vector((correction.x,correction.y,correction.z)).dot(actual)
    v=actual*along
    correction=Quaternion((correction.w,v.x,v.y,v.z)).normalized()
    pivot=pose[calf].translation.copy();ankle=pose[foot].translation.copy()
    for name in descendants[calf]:
        transform=pose[name]
        pose[name]=Matrix.LocRotScale(pivot+correction@(transform.translation-pivot),correction@transform.to_quaternion(),transform.to_scale())
    shift=(pose[foot].translation-ankle).length
    # 0.1mm is a numerical reconstruction guard for Blender float matrices,
    # not an artistic pass. Preserve and report the actual measured drift.
    if shift>.0001:raise ValueError(f'Correction changed {calf} ankle trajectory by {shift:.9f}m; axis={tuple(correction.axis)}, leg={tuple(actual)}')
    return {'removed_roll_degrees':math.degrees(correction.angle),'ankle_shift_m':shift}
