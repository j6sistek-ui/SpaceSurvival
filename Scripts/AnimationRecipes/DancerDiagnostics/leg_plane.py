import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Experimental F3 knee-plane reconstruction, not an accepted general solver.

The native negative-Z hinge was checked on this rig. Caller supplies armature-
space matrices. Preserve hip/knee/ankle centers and foot transforms; changing
thigh roll still changes skinning, so old pose correctives must not be reused.
"""
import math
from mathutils import Vector, Matrix, Quaternion

def align_native_leg_plane(pose, rest, parent, descendants, side, continuity=None):
    thigh, calf, foot = ('thigh_'+side, 'calf_'+side, 'foot_'+side)
    h,k,a = [pose[n].translation.copy() for n in (thigh,calf,foot)]
    upper=(k-h).normalized(); lower=(a-k).normalized()
    bend=upper.cross(lower)
    flex_sine=bend.length
    if flex_sine < .05 and (continuity is None or side not in continuity):
        raise ValueError('Near-straight knee needs an established pole vector')
    if flex_sine>1e-7:bend.normalize()
    if continuity is not None and side in continuity:
        old_upper,old_plane=continuity[side]
        carried=old_upper.rotation_difference(upper)@old_plane
        carried=(carried-upper*carried.dot(upper)).normalized()
        # Near extension the joint cross product is ill-conditioned. Transport
        # the previous plane and smoothly recover the source plane as it bends.
        w=max(0.,min(1.,(flex_sine-.025)/.125));w=w*w*(3-2*w)
        angle=math.atan2(upper.dot(carried.cross(bend)),carried.dot(bend)) if flex_sine>1e-7 else 0.
        bend=Quaternion(upper,angle*w)@carried
    if continuity is not None:continuity[side]=(upper.copy(),bend.copy())
    base=pose[thigh]@rest[thigh].inverted()@rest[calf]
    axis=base.to_quaternion()@Vector((0,0,-1))
    axis=(axis-upper*axis.dot(upper)).normalized()
    angle=math.atan2(upper.dot(axis.cross(bend)),axis.dot(bend))
    q=Quaternion(upper,angle)
    for n in set(descendants[thigh])-set(descendants[calf]):
        m=pose[n]
        pose[n]=Matrix.LocRotScale(h+q@(m.translation-h),q@m.to_quaternion(),m.to_scale())
    base=pose[thigh]@rest[thigh].inverted()@rest[calf]
    endpoint=rest[calf].inverted()@rest[foot].translation
    neutral=(base.to_quaternion()@endpoint).normalized()
    goal=(neutral.rotation_difference(lower)@base.to_quaternion()).normalized()
    cq=goal@pose[calf].to_quaternion().inverted()
    for n in set(descendants[calf])-set(descendants[foot]):
        m=pose[n]
        pose[n]=Matrix.LocRotScale(k+cq@(m.translation-k),cq@m.to_quaternion(),m.to_scale())
    return {'thigh_roll_degrees':math.degrees(angle),
            'flexion_degrees':math.degrees(upper.angle(lower)),
            'near_extension_plane_transport':flex_sine<.15}
