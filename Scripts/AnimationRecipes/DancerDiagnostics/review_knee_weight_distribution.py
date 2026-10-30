import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Matched contour test of circumferentially consistent knee skin weights.

The source assigns very different thigh/calf mixtures around the same height.
Test a smooth longitudinal mixture only within a protected knee region. Bone
transforms, rest geometry, UVs and unrelated influences remain unchanged.
"""
import bpy,json,math,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
O=R/'ZeroGSharedHip/KneeWeightDistribution';O.mkdir(exist_ok=True)
src=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');legs=bpy.data.objects['Vexa_Continuous_Feet'];pairs=json.loads(s['zero_g_curve_pairs'])
rest=np.array([tuple(legs.matrix_world@v.co) for v in legs.data.vertices]);before=[{g.group:g.weight for g in v.groups} for v in legs.data.vertices]
names={g.index:g.name for g in legs.vertex_groups};joint={side:np.array(rig.matrix_world@rig.data.bones['calf_'+side].head_local) for side in ['l','r']}
mesh=bpy.data.meshes.new('KneeWeightSnapshot');mesh.from_pydata(rest,[],[list(p.vertices) for p in legs.data.polygons]);mesh.update()
snapshot=bpy.data.objects.new('KneeWeightSnapshot',mesh);s.collection.objects.link(snapshot)
for p in mesh.polygons:p.use_smooth=True
for ob in s.objects:
 if ob.type=='MESH' and ob!=snapshot:ob.hide_render=True
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.52
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=False;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('KneeWeightWorld');s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=600;s.render.resolution_percentage=100
def set_weights(width=None):
 changed=0;maxdelta=0
 for i,weights in enumerate(before):
  side='l' if rest[i,0]>0 else 'r';c=joint[side];z=rest[i,2]-c[2]
  if abs(z)>.16:continue
  tf=[g for g in weights if names[g].startswith('thigh_') and names[g].endswith('_'+side)];cf=[g for g in weights if names[g].startswith('calf_') and names[g].endswith('_'+side)]
  wt=sum(weights[g] for g in tf);wc=sum(weights[g] for g in cf)
  if wt+wc<.99:continue
  new=weights.copy()
  if width is not None:
   alpha=np.clip((.16-abs(z))/.06,0,1);alpha=alpha*alpha*(3-2*alpha)
   desired=np.clip(.5-z/width,0,1);desired=desired*desired*(3-2*desired)
   newcf=wc*(1-alpha)+desired*(wt+wc)*alpha;newtf=wt+wc-newcf
   # Existing family ratios stay unchanged; introduce only the primary joint
   # if its family was absent at a boundary (currently not expected).
   if not cf:cf=[legs.vertex_groups['calf_'+side].index]
   if not tf:tf=[legs.vertex_groups['thigh_'+side].index]
   for g in cf:new[g]=newcf*(weights.get(g,0)/wc if wc else 1/len(cf))
   for g in tf:new[g]=newtf*(weights.get(g,0)/wt if wt else 1/len(tf))
  for g in set(new)|{g.group for g in legs.data.vertices[i].groups}:
   value=new.get(g,0);legs.vertex_groups[g].add([i],float(value),'REPLACE')
   delta=abs(value-weights.get(g,0));maxdelta=max(maxdelta,delta)
  changed+=int(any(abs(new.get(g,0)-weights.get(g,0))>1e-6 for g in set(new)|set(weights)))
 return {'changed_vertices':changed,'maximum_weight_delta':maxdelta}
report={'source_sha256':digest,'scope':'knee weights only, no saved mesh, no acceptance','controls':[]}
for label,width in [('baseline',None),('width16',.16),('width22',.22)]:
 change=set_weights(width)
 for suffix,frame in [('01_Drift',563.5),('02_Spiral',481),('03_Butterfly',474)]:
  name='A_F3_Coordinated_ZeroG_'+suffix;act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
  for on,an in pairs[name].items():
   keys=bpy.data.objects[on].data.shape_keys;keys.animation_data.action=bpy.data.actions[an];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
  s.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update();ev=legs.evaluated_get(bpy.context.evaluated_depsgraph_get());points=np.array([tuple(legs.matrix_world@v.co) for v in ev.data.vertices]);mesh.vertices.foreach_set('co',points.ravel());mesh.update();bpy.context.view_layer.update()
  h,k,a=[(rig.matrix_world@rig.pose.bones[n+'_r'].matrix).translation for n in ['thigh','calf','foot']];normal=(h-k).cross(a-k).normalized();up=(h-k).normalized();front=normal.cross(up).normalized()
  for view,offset in [('hinge',normal*3),('oblique',(normal*.65+front*.76)*3),('front',front*3)]:
   cam.location=k+offset;cam.rotation_euler=(k-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{suffix}_{view}_{label}.png');bpy.ops.render.render(write_still=True)
  report['controls'].append({'label':label,'width_m':width,'action':suffix,'frame':frame,**change})
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
(O/'Report.json').write_text(json.dumps(report,indent=2));print('KNEE_WEIGHT_CONTROL_DONE',flush=True)
