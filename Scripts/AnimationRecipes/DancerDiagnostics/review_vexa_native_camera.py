import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Exact native camera on the saved Blender proof; no source writes."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=R.parents[2]
live=json.loads((R/'NativeVexaRuntimeSkin.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'SourceAssets/DanceRefinement_20261025/Vexa_Shoulder_Proof.blend'),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');s.frame_set(1);bpy.context.view_layer.update();bone_lookup={b.name.casefold():b for b in rig.pose.bones}
names=sorted(set(live['shots'][0]['bones']) & set(bone_lookup));a=np.array([live['shots'][0]['bones'][n]['translation'] for n in names])*.01;b=np.array([tuple((rig.matrix_world@bone_lookup[n].matrix).translation) for n in names]);u,_,vt=np.linalg.svd((a-a.mean(0)).T@(b-b.mean(0)));rot=u@vt;offset=b.mean(0)-a.mean(0)@rot
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.4,.4,.4);s.display.shading.show_cavity=False;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('NativeCameraWorld');s.world.color=(0,0,0)
s.render.resolution_x=700;s.render.resolution_y=700;s.render.resolution_percentage=100
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='PERSP';cam.data.angle=np.radians(60)
for row in live['shots'][1:3]:
 sec=row['seconds'];frame=1+sec*60;s.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
 target=np.array(row['bones']['spine_05']['translation'])*.01;pos=target+np.array((0,1.3,.25));cam.location=Vector(pos@rot+offset);cam.rotation_euler=(Vector(target@rot+offset)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(R/f'VexaNativeCamera_{sec}.png');bpy.ops.render.render(write_still=True)
print('NATIVE_CAMERA_DONE',flush=True)
