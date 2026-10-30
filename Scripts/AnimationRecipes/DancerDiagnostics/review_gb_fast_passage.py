import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only matched full-body frames around the fast source passage."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'GBFastPassage';O.mkdir(exist_ok=True)
sources=[D/'Vexa_HandIsolation_Proof.blend',D/'GB_ShoulderResponse_ActionLibrary.blend'];hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
bpy.ops.wm.open_mainfile(filepath=str(sources[0]),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
for ob in s.objects:
 if ob.type=='MESH' and ob.data.shape_keys:
  ob.data.shape_keys.animation_data_clear()
  for key in ob.data.shape_keys.key_blocks:
   if key.name.startswith('REVIEW_'):key.value=0
with bpy.data.libraries.load(str(sources[1]),link=False) as(a,b):b.actions=['A_F3_ShoulderResponse_g2']
rig.animation_data_create();rig.animation_data.action=b.actions[0];rig.animation_data.action_slot=b.actions[0].slots[0]
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55);s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('GBFastPassage');s.world.color=(.035,.045,.055)
s.render.resolution_x=s.render.resolution_y=650;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.1
rows=[]
for f in (50,65,75,80,83,90,100,115):
 s.frame_set(f);bpy.context.view_layer.update();center=rig.matrix_world@rig.pose.bones['pelvis'].head+Vector((0,0,.2))
 for view,off in [('front',Vector((0,-4,.3))),('side',Vector((4,0,.3)))]:
  cam.location=center+off;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();path=O/f'g2_{f}_{view}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'frame':f,'view':view,'path':str(path)})
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items())
(O/'Report.json').write_text(json.dumps({'sources':hashes,'cases':rows},indent=2));print('FAST_PASSAGE_DONE',flush=True)
