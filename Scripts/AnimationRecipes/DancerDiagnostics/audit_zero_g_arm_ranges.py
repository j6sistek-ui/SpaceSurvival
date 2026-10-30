import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Continuous owner arm-reach screen, independent of endpoints/clearance."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
src=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
for ob in s.objects:
 if ob.type=='MESH':
  for mod in ob.modifiers:mod.show_viewport=False
  if ob.data.shape_keys:ob.data.shape_keys.animation_data_clear()
rest={b.name:rig.matrix_world@b.matrix_local for b in rig.data.bones};hinge={}
for side in ['l','r']:
 a,b,c=[rest[n+'_'+side] for n in ['upperarm','lowerarm','hand']]
 hinge[side]=a.to_quaternion().inverted()@(b.translation-a.translation).cross(c.translation-b.translation).normalized()
results=[]
for name in sorted(json.loads(s['zero_g_curve_pairs'])):
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
 for f in range(round(act.frame_range[0]),round(act.frame_range[1])+1):
  s.frame_set(f);p={n:rig.matrix_world@rig.pose.bones[n].matrix for n in ['spine_05','upperarm_l','upperarm_r','lowerarm_l','lowerarm_r','hand_l','hand_r']}
  chest=p['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();up=chest@Vector((0,0,1));forward=chest@Vector((0,-1,0))
  for side in ['l','r']:
   a,b,c=[p[n+'_'+side] for n in ['upperarm','lowerarm','hand']];upper=(b.translation-a.translation).normalized();lower=(c.translation-b.translation).normalized();h=upper.cross(lower);flex=math.degrees(upper.angle(lower));alignment=1.
   if h.length>.1:alignment=(a.to_quaternion().inverted()@h.normalized()).dot(hinge[side])
   back=math.degrees(math.asin(max(-1,min(1,-upper.dot(forward)))));limit=10 if upper.dot(up)>0 else 0
   rows.append({'frame':f,'side':side,'flexion':flex,'hinge_alignment':alignment,'rear':back,'limit':limit,'reversal':alignment<0 and flex>10,'rear_flag':back>limit+2})
 summary={'clip':name,'frame_range':list(act.frame_range),'samples':len(rows),'reversal_samples':sum(x['reversal'] for x in rows),'rear_flags':sum(x['rear_flag'] for x in rows),'max_rear':max(x['rear'] for x in rows),'worst':sorted(rows,key=lambda x:max(0,x['rear']-x['limit'])+max(0,-x['hinge_alignment'])*90,reverse=True)[:8]}
 results.append({'summary':summary,'samples':rows});print('ZERO_G_ARM_SCREEN',json.dumps(summary),flush=True)
(R/'ZeroGSharedHip/ArmRangeScreen.json').write_text(json.dumps({'source_sha256':digest,'clips':results,'scope':'Inspection screen against owner chest-relative reach/reversal preference; not clinical or complete quality acceptance.'},indent=2))
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
