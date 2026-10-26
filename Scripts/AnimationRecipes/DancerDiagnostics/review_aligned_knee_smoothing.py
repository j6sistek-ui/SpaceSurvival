import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Matched knee-only Corrective Smooth control after verified leg-plane repair.

No input writes. Keep the paired hip curves fixed; compare only the final
surface operation, against the same isolated camera and light.
"""
import bpy, json, math, hashlib, numpy as np
from pathlib import Path
from mathutils import Matrix
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
O=R/'ZeroGSharedHip/AlignedKneeSmoothing'; O.mkdir(exist_ok=True)
src=D/'Vexa_ZeroG_SharedHip_Proof.blend'
digest=hashlib.sha256(src.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene; rig=next(o for o in s.objects if o.type=='ARMATURE')
pairs=json.loads(s['zero_g_curve_pairs']); legs=bpy.data.objects['Vexa_Continuous_Feet']
rest=np.array([tuple(legs.matrix_world@v.co) for v in legs.data.vertices])
centers=np.array([tuple(rig.matrix_world@rig.data.bones['calf_'+side].head_local) for side in ('l','r')])
dist=np.linalg.norm(rest[:,None,:]-centers[None,:,:],axis=2).min(axis=1)
mask=np.clip((.14-dist)/.09,0,1); mask=mask*mask*(3-2*mask)
vg=legs.vertex_groups.new(name='DIAGNOSTIC_KneeOnly')
for i in np.flatnonzero(mask>0): vg.add([int(i)],float(mask[i]),'REPLACE')
smooth=legs.modifiers.new('DIAGNOSTIC_KneeCorrectiveSmooth','CORRECTIVE_SMOOTH')
smooth.vertex_group=vg.name; smooth.factor=.5; smooth.iterations=10
smooth.smooth_type='LENGTH_WEIGHTED'; smooth.use_pin_boundary=True
smooth.rest_source='BIND'
# Bind the unposed character and zero only generated correction coefficients.
rig.animation_data_clear()
for b in rig.pose.bones: b.matrix_basis=Matrix.Identity(4)
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'): key.value=0
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active=legs
with bpy.context.temp_override(object=legs,active_object=legs):
 bpy.ops.object.correctivesmooth_bind(modifier=smooth.name)
assert smooth.is_bind
mesh=bpy.data.meshes.new('SmoothedKneeSnapshot')
mesh.from_pydata(rest,[],[list(p.vertices) for p in legs.data.polygons]); mesh.update()
ob=bpy.data.objects.new('SmoothedKneeSnapshot',mesh); s.collection.objects.link(ob)
for p in mesh.polygons: p.use_smooth=True
for x in s.objects:
 if x.type=='MESH' and x!=ob: x.hide_render=True
bpy.ops.object.camera_add(); cam=bpy.context.object; s.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=.52
s.render.engine='BLENDER_WORKBENCH'; s.display.shading.light='STUDIO'
s.display.shading.color_type='SINGLE'; s.display.shading.single_color=(.55,.55,.55)
s.display.shading.show_cavity=False; s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('KneeSmoothWorld'); s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=600; s.render.resolution_percentage=100
def evaluate(enabled):
 smooth.show_viewport=enabled; bpy.context.view_layer.update()
 ev=legs.evaluated_get(bpy.context.evaluated_depsgraph_get())
 return np.array([tuple(legs.matrix_world@v.co) for v in ev.data.vertices])
report={'source_sha256':digest,'parameters':{'factor':.5,'iterations':10,'radius_m':.14,'fade_m':.09,'rest':'BIND','smooth_type':'LENGTH_WEIGHTED'},'poses':[]}
rig.animation_data_create()
for suffix,frame in [('01_Drift',563.5),('02_Spiral',481),('03_Butterfly',474)]:
 name='A_F3_Coordinated_ZeroG_'+suffix; act=bpy.data.actions[name]
 rig.animation_data.action=act; rig.animation_data.action_slot=act.slots[0]
 for on,an in pairs[name].items():
  keys=bpy.data.objects[on].data.shape_keys; keys.animation_data_create()
  keys.animation_data.action=bpy.data.actions[an]; keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 s.frame_set(math.floor(frame),subframe=frame%1)
 baseline=evaluate(False); corrected=evaluate(True)
 delta=np.linalg.norm(corrected-baseline,axis=1)*1000
 assert delta[mask==0].max(initial=0)<.001
 report['poses'].append({'action':suffix,'frame':frame,'max_change_mm':float(delta.max()),'p95_change_mm':float(np.percentile(delta[mask>0],95)),'outside_mask_mm':float(delta[mask==0].max(initial=0))})
 h,k,a=[(rig.matrix_world@rig.pose.bones[n+'_r'].matrix).translation for n in ('thigh','calf','foot')]
 normal=(h-k).cross(a-k).normalized(); up=(h-k).normalized(); front=normal.cross(up).normalized()
 for view,offset in [('hinge',normal*3),('oblique',(normal*.65+front*.76)*3)]:
  cam.location=k+offset; cam.rotation_euler=(k-cam.location).to_track_quat('-Z','Y').to_euler()
  for label,points in [('baseline',baseline),('smooth',corrected)]:
   mesh.vertices.foreach_set('co',points.ravel()); mesh.update(); bpy.context.view_layer.update()
   s.render.filepath=str(O/f'{suffix}_{view}_{label}.png'); bpy.ops.render.render(write_still=True)
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
(O/'Report.json').write_text(json.dumps(report,indent=2))
print('ALIGNED_KNEE_SMOOTH_DONE',flush=True)
