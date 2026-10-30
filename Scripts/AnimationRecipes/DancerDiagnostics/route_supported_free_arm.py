import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""One explicit G1 free-arm detour; not a general contact/IK system.

The source forearm crosses the pole at944â€“947.5. Temporarily fold the free
arm toward a clear overhead waypoint instead. Preserve lengths and the
source elbow bend side, never move the supporting arm or the root.
"""
import math
from mathutils import Vector

def route_free_arm(p,frame,rotate):
 if not 934<frame<962:return {'active':False}
 controls=route_free_arm.controls
 left=next(i for i in range(len(controls)-1) if controls[i][0]<=frame<=controls[i+1][0])
 f0,d0=controls[left];f1,d1=controls[left+1];t=(frame-f0)/(f1-f0)
 weight=t*t*t*(10-15*t+6*t*t)
 displacement=d0.lerp(d1,weight)
 shoulder=p['upperarm_l'].translation.copy();elbow=p['lowerarm_l'].translation.copy();hand=p['hand_l'].translation.copy()
 goal=hand+displacement
 l1=(elbow-shoulder).length;l2=(hand-elbow).length
 d=goal-shoulder;distance=d.length;direction=d.normalized()
 reach=max(abs(l1-l2)+.005,min(l1+l2-.002,distance));goal=shoulder+direction*reach
 hint=elbow-shoulder-direction*(elbow-shoulder).dot(direction)
 if hint.length<.0001:raise ValueError('Free-arm bend side is undefined')
 hint.normalize();x=(l1*l1-l2*l2+reach*reach)/(2*reach);y=math.sqrt(max(0,l1*l1-x*x))
 new_elbow=shoulder+direction*x+hint*y
 rotate(p,'upperarm_l',(elbow-shoulder).rotation_difference(new_elbow-shoulder))
 current_hand=p['hand_l'].translation.copy();current_elbow=p['lowerarm_l'].translation.copy()
 rotate(p,'lowerarm_l',(current_hand-current_elbow).rotation_difference(goal-current_elbow))
 assert (p['hand_l'].translation-goal).length<.00002
 return {'active':True,'blend':weight,'hand_displacement_m':(goal-hand).length,'elbow_displacement_m':(new_elbow-elbow).length,'reach_clamped_m':abs(reach-distance)}
