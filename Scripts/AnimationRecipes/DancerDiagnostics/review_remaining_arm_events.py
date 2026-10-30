import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only views of selected severe source excursions before any rephrasing."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
D=R.parents[2]/'SourceAssets/DanceRefinement_20261025';O=R/'GBArmEventViews';O.mkdir(exist_ok=True)
mesh=D/'Vexa_HandIsolation_Proof.blend';library=D/'G2_ArmPassage_ActionLibrary.blend';hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (mesh,library)}
bpy.ops.wm.open_mainfile(filepath=str(mesh),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
names=['A_F3_ArmPassage_g2']+['A_F3_ShoulderResponse_'+c for c in ('g1','b1')]
with bpy.data.libraries.load(str(library),link=False) as(a,b):b.actions=names
actions={a.name:a for a in b.actions};rig.animation_data_create()
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('ArmEventViews');s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=600;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.45
events=[('g1',192,207,231),('g1',550,566,582),('g2',787,810,830),('g2',770,787,803),('b1',101,117,133),('b1',905,920,935)];rows=[]
for clip,a,peak,z in events:
 action=actions['A_F3_ArmPassage_g2' if clip=='g2' else 'A_F3_ShoulderResponse_'+clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 for f in (a,peak,z):
  s.frame_set(f);bpy.context.view_layer.update();chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted();center=rig.matrix_world@rig.pose.bones['spine_05'].head+chest@Vector((0,0,-.12))
  for view,off in [('front',Vector((0,-3,.2))),('back',Vector((0,3,.2)))]:
   cam.location=center+chest@off;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();path=O/f'{clip}_{peak}_{f}_{view}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'clip':clip,'peak':peak,'frame':f,'view':view,'path':str(path)})
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items());(O/'Report.json').write_text(json.dumps({'sources':hashes,'cases':rows},indent=2));print('ARM_EVENT_VIEWS_DONE',flush=True)
