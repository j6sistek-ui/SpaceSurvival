import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Coordinate free-floating arm phrasing with its clavicles; no contact authority."""
import math
from mathutils import Matrix,Quaternion,Vector

def coordinate(pose,rest,parent,descendants,neck=False):
    chest=pose['spine_05']@rest['spine_05'].inverted()
    up=chest.to_quaternion()@Vector((0,0,1));rows={}
    for side in ('l','r'):
        clav,upper,lower=['clavicle_'+side,'upperarm_'+side,'lowerarm_'+side]
        direction=(pose[lower].translation-pose[upper].translation).normalized()
        elev=math.asin(max(-1.,min(1.,direction.dot(up))))
        t=max(0.,min(1.,(elev+math.radians(10))/math.radians(90)))
        lift=math.radians(20)*t*t*(3-2*t)
        base=chest@rest[clav]
        shoulder=(base@rest[clav].inverted()@rest[upper]).translation
        axis=(shoulder-base.translation).normalized().cross(up).normalized()
        q=Quaternion(axis,lift)
        new=Matrix.LocRotScale(base.translation,q@base.to_quaternion(),base.to_scale())
        new_shoulder=(new@rest[clav].inverted()@rest[upper]).translation
        shift=new_shoulder-pose[upper].translation
        pose[clav]=new
        for n in descendants[upper]:pose[n].translation+=shift
        rows[side]={'elevation_deg':math.degrees(elev),'clavicle_lift_deg':math.degrees(lift),'arm_root_shift_m':shift.length}
    if neck:
        # Share the lower-neck rotation across both neck joints, preserving the
        # original upper-neck/head orientations instead of making the head rigid.
        a,b='neck_01','neck_02';base=pose[parent[a]]@rest[parent[a]].inverted()@rest[a]
        local=base.inverted()@pose[a];q=local.to_quaternion()
        if q.w<0:q.negate()
        pose[a]=base@Matrix.LocRotScale(local.translation,Quaternion().slerp(q,.5),local.to_scale())
        new_b=(pose[a]@rest[a].inverted()@rest[b]).translation
        shift=new_b-pose[b].translation
        for n in descendants[b]:pose[n].translation+=shift
        rows['neck']={'head_translation_m':shift.length,'lower_neck_rotation_deg':math.degrees(q.angle)}
    return rows
