import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""CPU-only whole-clip visible-surface chamber bounds and distal pose extrema.

The envelope covers this private body/garment proof at 60fps, not future hair,
physics or unsampled interpolation. Angular extrema nominate inspection views;
they do not certify human range of motion.
"""
import bpy,json,math,hashlib,numpy as np
from pathlib import Path
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
source=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');pairs=json.loads(s['zero_g_curve_pairs'])
meshes=[o for o in s.objects if o.type=='MESH' and not o.hide_render];assert meshes
report={'source_sha256':digest,'fps':60,'scope':'Sampled private visible surfaces; not future hair/cloth or anatomical acceptance','chamber':{'inner_radius_m':3.48,'z_min_m':6.15,'z_max_m':17.75,'base_height_m':10.8,'duet_x_m':[-1.7,1.7]},'clips':[]}
names=['hand_l','hand_r','foot_l','foot_r','lowerarm_l','lowerarm_r','calf_l','calf_r']
global_min=np.full(3,np.inf);global_max=-global_min
for name,pa in pairs.items():
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for n,a in pa.items():
  keys=bpy.data.objects[n].data.shape_keys;keys.animation_data_create();keys.animation_data.action=bpy.data.actions[a];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 first,last=map(round,act.frame_range);bounds_min=np.full(3,np.inf);bounds_max=-bounds_min;radial=0.;pole=np.inf;previous={};stats={n:{'max_angle_deg':-1,'max_step_deg':-1} for n in names}
 for f in range(first,last+1):
  s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
  for ob in meshes:
   ev=ob.evaluated_get(dg);data=np.empty(len(ev.data.vertices)*3,dtype=np.float64);ev.data.vertices.foreach_get('co',data);m=np.array(ob.matrix_world);v=data.reshape(-1,3)@m[:3,:3].T+m[:3,3]
   bounds_min=np.minimum(bounds_min,v.min(0));bounds_max=np.maximum(bounds_max,v.max(0))
   for offset in (-1.7,1.7):
    r=np.sqrt((v[:,0]+offset)**2+v[:,1]**2);radial=max(radial,float(r.max()));pole=min(pole,float(r.min())-.025)
  for n in names:
   q=rig.pose.bones[n].matrix_basis.to_quaternion().normalized();angle=math.degrees(2*math.acos(min(1,abs(q.w))));step=0
   if n in previous:step=math.degrees(previous[n].rotation_difference(q).angle);step=min(step,360-step)
   if angle>stats[n]['max_angle_deg']:stats[n].update(max_angle_deg=angle,angle_frame=f)
   if step>stats[n]['max_step_deg']:stats[n].update(max_step_deg=step,step_frame=f)
   previous[n]=q.copy()
  if f%240==0:print('SURFACE_AUDIT',name,f,flush=True)
 global_min=np.minimum(global_min,bounds_min);global_max=np.maximum(global_max,bounds_max)
 report['clips'].append({'action':name,'frames':last-first+1,'min_m':bounds_min.tolist(),'max_m':bounds_max.tolist(),'glass_margin_m':3.48-radial,'pole_margin_m':pole,'floor_margin_m':bounds_min[2]+10.8-6.15,'ceiling_margin_m':17.75-(bounds_max[2]+10.8),'distal_extrema':stats})
report['all_orders_duet_x_slab_margin_m']=3.4+float(global_min[0]-global_max[0])
report['visible_objects']=[o.name for o in meshes]
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
report['sampling_finished']=True
(R/'ZeroGSharedHip/FullSurfaceEnvelope.json').write_text(json.dumps(report,indent=2));print('SURFACE_AUDIT_DONE',report['all_orders_duet_x_slab_margin_m'],flush=True)
