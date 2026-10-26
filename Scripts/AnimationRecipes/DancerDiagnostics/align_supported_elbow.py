import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Couple humerus roll and elbow hinge; never roll only the forearm.

The F3 left elbow's inspected source bends around positive local Z. Determine
the corresponding world axis through an actual small local rotation, retaining
the reflected/scaled rest matrices. Quaternion-only axis conversion loses that
handedness. This is one rig's diagnostic, not a universal limb solver.
"""
import math
from mathutils import Vector,Quaternion,Matrix

def align_elbow(p,rest,rel,desc,frame):
 if not 934<frame<962:return {'active':False}
 t=min((frame-934)/7,(962-frame)/8,1);t=max(0,t);blend=t*t*t*(10-15*t+6*t*t)
 upper,lower,hand='upperarm_l','lowerarm_l','hand_l'
 h,k,a=[p[n].translation.copy() for n in [upper,lower,hand]]
 u=(k-h).normalized();v=(a-k).normalized();plane=u.cross(v)
 if plane.length<.015:raise ValueError('Detour requires an explicit non-straight elbow plane')
 plane.normalize()
 base=p[upper]@rel[lower];endpoint=rest[lower].inverted()@rest[hand].translation
 neutral=base.to_3x3()@endpoint
 advanced=base.to_3x3()@(Quaternion(Vector((0,0,1)),.01)@endpoint)
 axis=neutral.cross(advanced).normalized();axis=(axis-u*axis.dot(u)).normalized()
 roll=math.atan2(u.dot(axis.cross(plane)),axis.dot(plane))
 q=Quaternion(u,roll*blend)
 xf=Matrix.Translation(h)@q.to_matrix().to_4x4()@Matrix.Translation(-h)
 # Shoulder center and elbow position stay fixed. The forearm is rebuilt
 # from the new parent frame, leaving the free hand's world pose unchanged.
 for n in set(desc[upper])-set(desc[lower]):p[n]=xf@p[n]
 base=p[upper]@rel[lower];neutral=(base.to_3x3()@endpoint).normalized()
 qgoal=neutral.rotation_difference(v)
 target=Matrix.Translation(k)@qgoal.to_matrix().to_4x4()@Matrix.Translation(-k)@base
 # Full alignment is used in the middle; a smooth blend reconnects the
 # existing source elbow orientation at the unchanged passage boundaries.
 original=p[lower].copy();target=original.lerp(target,blend)
 change=target@original.inverted()
 for n in set(desc[lower])-set(desc[hand]):p[n]=change@p[n]
 return {'active':True,'weight':blend,'humerus_roll_deg':math.degrees(roll)*blend}
