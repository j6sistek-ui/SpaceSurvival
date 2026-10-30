import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import bpy,json
from pathlib import Path
from mathutils import Vector
P=R.parents[2];OUT=R/'HipReview';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/CharacterWorkshop_20261021/Roxie_Character_Options.blend'),load_ui=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
with bpy.data.libraries.load(str(P/'SourceAssets/DanceRefinement_20261025/Refined_ActionLibrary.blend'),link=False) as (a,b):b.actions=['A_F3_Refined_ZeroG_02_Spiral']
rig.animation_data_create();rig.animation_data.action=b.actions[0];rig.animation_data.action_slot=b.actions[0].slots[0]
scene=bpy.context.scene;scene.render.fps=60;scene.frame_set(481)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('HipReview');scene.world.color=(.035,.045,.055)
scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100
center=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.95
for mode in ('linear','volume'):
 for ob in scene.objects:
  if ob.type=='MESH' and ob.visible_get() and not ob.hide_render:
   for mod in ob.modifiers:
    if mod.type=='ARMATURE':mod.use_deform_preserve_volume=(mode=='volume')
 for angle,delta in [('front',Vector((0,-6,1))),('back',Vector((0,6,1))),('side',Vector((6,0,1)))]:
  cam.location=center+delta;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  scene.render.filepath=str(OUT/f'{mode}_{angle}.png');bpy.ops.render.render(write_still=True)
print('HIP_COMPARE_DONE',flush=True)
