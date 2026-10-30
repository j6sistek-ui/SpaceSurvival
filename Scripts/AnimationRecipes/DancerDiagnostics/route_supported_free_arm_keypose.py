import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Rephrase a free-arm crossing using the preserved G1 frame881 arm pose.

Blend local rotations through an already inspected pose rather than forcing
a Cartesian wrist detour. All limb lengths and the support arm stay unchanged.
The reference pose is not evidence that the complete blend clears the body.
"""
from mathutils import Vector

def route_free_arm(p,frame,rotate):
 if not 934<frame<970:return {'active':False}
 t=min((frame-934)/7,(970-frame)/14,1);t=max(0,t);blend=t*t*t*(10-15*t+6*t*t)
 parent,rel,ordered,reference=route_free_arm.rig_data
 changed={'clavicle_l','upperarm_l','lowerarm_l','hand_l'}
 old={n:m.copy() for n,m in p.items()};hand=old['hand_l'].translation.copy();elbow=old['lowerarm_l'].translation.copy()
 for n in ordered:
  if n not in route_free_arm.branch:continue
  basis=(old[parent[n]]@rel[n]).inverted()@old[n]
  if n in changed:basis=basis.lerp(reference[n],blend)
  p[n]=p[parent[n]]@rel[n]@basis
 return {'active':True,'blend':blend,'hand_displacement_m':(p['hand_l'].translation-hand).length,'elbow_displacement_m':(p['lowerarm_l'].translation-elbow).length,'reach_clamped_m':0,'source_pose':881}
