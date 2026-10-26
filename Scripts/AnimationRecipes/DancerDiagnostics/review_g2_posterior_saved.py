import os, sys
from pathlib import Path
_recipe_dir=Path(__file__).resolve().parent
sys.path.insert(0,str(_recipe_dir))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Same-pose, three-angle saved-asset comparison with correction off/on."""
import bpy,json,hashlib,math,numpy as np
from pathlib import Path
from mathutils import Vector
O=R/'G2PosteriorHip';D=R.parents[2]/'SourceAssets/DanceRefinement_20261025'
source=D/'Vexa_G2_PosteriorHip_Candidate.blend';bake=json.loads((O/'BakeReport.json').read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==bake['sha256']
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
keys=[k for ob in s.objects if ob.type=='MESH' and ob.data.shape_keys for k in ob.data.shape_keys.key_blocks if k.name.startswith('REVIEW_G2_')]
rest=(rig.matrix_world@rig.data.bones['pelvis'].matrix_local).to_quaternion()
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='OBJECT';s.display.shading.show_cavity=False;s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('SavedHipReview');s.world.color=(.035,.045,.055)
for ob in s.objects:
 if ob.type=='MESH':ob.color=(.55,.55,.55,1)
s.render.resolution_x=s.render.resolution_y=900;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.15
rows=[]
for t in (7.1,10.6,12.4,14.5):
 frame=1+t*60;s.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
 pelvis=rig.matrix_world@rig.pose.bones['pelvis'].matrix;body=pelvis.to_quaternion()@rest.inverted();center=pelvis.translation
 for mode in ('weights_only','posterior_correction'):
  for key in keys:key.mute=mode=='weights_only'
  bpy.context.view_layer.update()
  for name,direction in [('posterior',Vector((0,5,.25))),('posterior_quarter',Vector((3,5,.25))),('side',Vector((5,0,.25)))]:
   offset=body@direction;cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
   path=O/f'{t:05.2f}_{mode}_{name}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   rows.append({'time':t,'mode':mode,'view':name,'path':str(path)})
(O/'SavedReview.json').write_text(json.dumps({'source_sha256':bake['sha256'],'views':rows,'scope':'Identical bone motion and four-vertex weight repair in both modes; local posterior correction toggled only.'},indent=2))
assert hashlib.sha256(source.read_bytes()).hexdigest()==bake['sha256'];print('SAVED_HIP_REVIEW_DONE',flush=True)
