import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'HipCurveProof';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(D/'Roxie_HipCurve_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('HipCurves');s.world.color=(.035,.045,.055)
s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.15
for t in (0,4,6,8,10,12,16):
 s.frame_set(t*60+1);center=(rig.matrix_world@rig.pose.bones['pelvis'].matrix).translation
 for angle,d in [('front',Vector((0,-6,1))),('back',Vector((0,6,1)))]:
  cam.location=center+d;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(O/f'{t}_{angle}.png');bpy.ops.render.render(write_still=True)
print('HIP_CURVE_REVIEW_DONE',flush=True)
