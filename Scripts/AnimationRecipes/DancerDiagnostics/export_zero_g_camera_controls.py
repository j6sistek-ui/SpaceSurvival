import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Exact source camera and critical posed vertices for native visual controls."""
import bpy,json,numpy as np,hashlib,math
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip'
source=D/'Vexa_ZeroG_SharedHip_Proof.blend';before=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');pairs=json.loads(s['zero_g_curve_pairs'])
rest=rig.matrix_world@rig.data.bones['spine_05'].matrix_local;basis=json.loads((O/'NativeParity.json').read_text());rot=np.array(basis['basis']);trans=np.array(basis['translation_cm']);rows=[];surfaces={}
for a,pa in pairs.items():
 action=bpy.data.actions[a];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 for n,k in pa.items():
  keys=bpy.data.objects[n].data.shape_keys;keys.animation_data.action=bpy.data.actions[k];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 frames=[1,1+(action.frame_range[1]-1)*.5]
 if 'Drift' in a:frames+=[563.5]
 for f in frames:
  s.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update();p={b.name:rig.matrix_world@b.matrix for b in rig.pose.bones};q=p['spine_05'].to_quaternion()@rest.to_quaternion().inverted();center=p['pelvis'].translation+q@Vector((0,0,.15));label=a.split('ZeroG_')[1]+'_'+str(float(f)).replace('.','p')
  for view,offset in [('front',Vector((0,-3,.2))),('back',Vector((0,3,.2)))]:
   loc=center+q@offset;up=q@Vector((0,0,1));convert=lambda v:list(np.array(v)*100@rot+trans)
   rows.append({'action':a.split('ZeroG_')[1],'frame':f,'seconds':(f-1)/60,'label':label,'view':view,'loc':convert(loc),'center':convert(center),'up':list(np.array(up)@rot),'ortho_width_cm':235})
  if 'Drift' in a and f==563.5:
   for ob in s.objects:
    if ob.type=='MESH' and not ob.hide_render:
     ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());surfaces[label+'__'+ob.name]=np.array([tuple(ob.matrix_world@v.co) for v in ev.data.vertices],dtype=np.float32)
(O/'MatchedCameras.json').write_text(json.dumps(rows,indent=2));np.savez_compressed(O/'CriticalSurface.npz',**surfaces)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
print('MATCHED_CAMERAS',len(rows),flush=True)
