import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Separate knee targets after verified hinge reconstruction, before any bake.

Earlier DQ trials used the uncorrected leg plane. This control keeps the new
plane and shared hip target fixed, comparing only a small knee neighborhood.
"""
import bpy,json,math,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'ZeroGSharedHip/AlignedKneeTargets';O.mkdir(exist_ok=True)
src=D/'Vexa_ZeroG_SharedHip_Proof.blend';digest=hashlib.sha256(src.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');pairs=json.loads(s['zero_g_curve_pairs'])
legs=bpy.data.objects['Vexa_Continuous_Feet'];mod=next(m for m in legs.modifiers if m.type=='ARMATURE');rest=np.array([tuple(legs.matrix_world@v.co) for v in legs.data.vertices]);centers=np.array([tuple(rig.matrix_world@rig.data.bones['calf_'+side].head_local) for side in ('l','r')])
distance=np.linalg.norm(rest[:,None,:]-centers[None,:,:],axis=2);nearest=distance.argmin(axis=1);mask=np.clip((.16-distance.min(axis=1))/.10,0,1);mask=mask*mask*(3-2*mask)
faces=[list(p.vertices) for p in legs.data.polygons]
mesh=bpy.data.meshes.new('AlignedKneeSnapshot');mesh.from_pydata(rest,[],faces);mesh.update();ob=bpy.data.objects.new('AlignedKneeSnapshot',mesh);s.collection.objects.link(ob)
for p in mesh.polygons:p.use_smooth=True
for x in s.objects:
 if x.type=='MESH' and x!=ob:x.hide_render=True
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.52
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=False;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('AlignedKneeWorld');s.world.color=(.035,.045,.055);s.render.resolution_x=s.render.resolution_y=600;s.render.resolution_percentage=100
def evaluate():
 bpy.context.view_layer.update();ev=legs.evaluated_get(bpy.context.evaluated_depsgraph_get());return np.array([tuple(legs.matrix_world@v.co) for v in ev.data.vertices])
report={'source_sha256':digest,'scope':'evaluated snapshots only, no saved mesh edits','poses':[]}
for suffix,frame in [('01_Drift',563.5),('02_Spiral',481),('03_Butterfly',474)]:
 name='A_F3_Coordinated_ZeroG_'+suffix;act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 for on,an in pairs[name].items():
  keys=bpy.data.objects[on].data.shape_keys;keys.animation_data.action=bpy.data.actions[an];keys.animation_data.action_slot=keys.animation_data.action.slots[0]
 s.frame_set(math.floor(frame),subframe=frame%1);mod.use_deform_preserve_volume=False;linear=evaluate();mod.use_deform_preserve_volume=True;dq=evaluate();mod.use_deform_preserve_volume=False;bpy.context.view_layer.update()
 # Bisector helper target keeps the knee ring rotating at half the bend,
 # instead of linearly averaging matrices. It is a diagnostic, not anatomy.
 target=linear.copy()
 for i,side in enumerate(('l','r')):
  thigh=rig.pose.bones['thigh_'+side].matrix@rig.data.bones['thigh_'+side].matrix_local.inverted()
  calf=rig.pose.bones['calf_'+side].matrix@rig.data.bones['calf_'+side].matrix_local.inverted()
  q=thigh.to_quaternion().slerp(calf.to_quaternion(),.5);worldq=rig.matrix_world.to_quaternion()@q@rig.matrix_world.to_quaternion().inverted()
  k=np.array((rig.matrix_world@rig.pose.bones['calf_'+side].matrix).translation);ids=np.flatnonzero((nearest==i)&(mask>0))
  target[ids]=(rest[ids]-centers[i])@np.array(worldq.to_matrix()).T+k
 modes={'baseline':linear,'localized_dq':linear+(dq-linear)*mask[:,None],'half_bend':linear+(target-linear)*mask[:,None]}
 side='r';h,k,a=[(rig.matrix_world@rig.pose.bones[n+'_'+side].matrix).translation for n in ('thigh','calf','foot')];normal=(h-k).cross(a-k).normalized();up=(h-k).normalized();front=normal.cross(up).normalized()
 row={'action':suffix,'frame':frame,'flexion_deg':180-math.degrees((h-k).angle(a-k)),'max_displacement_mm':{n:float(np.linalg.norm(v-linear,axis=1).max()*1000) for n,v in modes.items()}}
 report['poses'].append(row)
 for view,delta in [('hinge',normal*3),('oblique',(normal*.65+front*.76)*3)]:
  cam.location=k+delta;cam.rotation_euler=(k-cam.location).to_track_quat('-Z','Y').to_euler()
  for mode,points in modes.items():
   mesh.vertices.foreach_set('co',points.ravel());mesh.update();bpy.context.view_layer.update();s.render.filepath=str(O/f'{suffix}_{view}_{mode}.png');bpy.ops.render.render(write_still=True)
assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
(O/'Report.json').write_text(json.dumps(report,indent=2));print('ALIGNED_KNEE_TARGETS_DONE',flush=True)
