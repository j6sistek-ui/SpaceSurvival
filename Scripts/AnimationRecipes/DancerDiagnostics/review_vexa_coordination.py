import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Compare source, coordinated clavicles, then distributed neck independently."""
import bpy,json,math,sys,os
from pathlib import Path
from mathutils import Matrix,Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaCoordination';O.mkdir(exist_ok=True)
from coordinated_girdle import coordinate
SYMMETRY=os.environ.get('SS_REVIEW_SYMMETRY')=='1'
if SYMMETRY:
 from mirror_vexa_shoulder_weights import apply
 O=R/'VexaCoordinatedSymmetry';O.mkdir(exist_ok=True)
NORMALS=os.environ.get('SS_REVIEW_NORMALS')=='1'
if NORMALS:O=R/'VexaCoordinatedNormals';O.mkdir(exist_ok=True)
report=[]
for sec in (4,9.033333,12.2):
 for mode in ('clavicle','clavicle_neck'):
  bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend'),load_ui=False)
  s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');rig.animation_data_clear()
  with bpy.data.libraries.load(str(D/'Vexa_LegPlane_Proof.blend'),link=False) as (a,b):b.actions=['A_F3_LegPlane_ZeroG_02_Spiral']
  rig.animation_data_create();rig.animation_data.action=b.actions[0];rig.animation_data.action_slot=b.actions[0].slots[0]
  s.frame_set(round(1+sec*60));bpy.context.view_layer.update()
  rest={b.name:(rig.matrix_world@b.matrix_local).copy() for b in rig.data.bones};pose={pb.name:(rig.matrix_world@pb.matrix).copy() for pb in rig.pose.bones};ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive))
  parent={b.name:b.parent.name if b.parent else None for b in rig.pose.bones};desc={b.name:[b.name]+[c.name for c in b.children_recursive] for b in rig.pose.bones}
  rig.animation_data_clear();row={'seconds':sec,'mode':mode,'changes':coordinate(pose,rest,parent,desc,mode=='clavicle_neck')}
  inv=rig.matrix_world.inverted();local={n:inv@m for n,m in pose.items()}
  for pb in ordered:
   base=local[pb.parent.name]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local
   pb.matrix_basis=base.inverted()@local[pb.name]
  bpy.context.view_layer.update()
  if SYMMETRY:
   row['weights']=apply(bpy.data.objects['Vexa_Nude_Torso']);bpy.context.view_layer.update()
  if NORMALS:
   row['normal_controls']=[]
   for name in ('Vexa_Nude_Torso','Eden_Pink_CharacterMesh0.001'):
    ob=bpy.data.objects[name];before=ob.data.has_custom_normals
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    if before:bpy.ops.mesh.customdata_custom_splitnormals_clear()
    row['normal_controls'].append({'name':name,'before':before,'after':ob.data.has_custom_normals})
   bpy.context.view_layer.update()
  for o in s.objects:
   if o.type=='MESH' and 'hair' in o.name.lower():o.hide_render=True
  s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.65,.65,.65);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('Coordination');s.world.color=(.035,.045,.055)
  s.render.resolution_x=800;s.render.resolution_y=800;s.render.resolution_percentage=100
  bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.9
  chest=pose['spine_05'].to_quaternion()@rest['spine_05'].to_quaternion().inverted();center=(pose['upperarm_l'].translation+pose['upperarm_r'].translation)*.5
  for view,offset in [('front',Vector((0,-3,.15))),('back',Vector((0,3,.15))),('side',Vector((3,-1,.15)))]:
   cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{sec:g}_{mode}_{view}.png');bpy.ops.render.render(write_still=True)
   error=max(abs(rig.pose.bones[n].matrix[i][j]-m[i][j]) for n,m in local.items() for i in range(4) for j in range(4));assert error<.001,error
  report.append(row)
(O/'Report.json').write_text(json.dumps(report,indent=2));print('COORDINATION_REVIEW_DONE',flush=True)
