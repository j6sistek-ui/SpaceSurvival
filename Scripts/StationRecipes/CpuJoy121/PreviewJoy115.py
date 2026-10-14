"""CPU-only head framing of the saved color derivative; geometry is unchanged."""
import bpy
import json
import hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[3] / '.agent/local/StationRefinement/CpuJoy121/JoyBlue114'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'Joy_LightBlue_HairFitted.blend'), load_ui=False, use_scripts=False)
scene=bpy.context.scene
rig=bpy.data.objects['Armature']
head=rig.matrix_world @ rig.pose.bones['CC_Base_Head'].head
target=head+Vector((0,0,.075))
data=bpy.data.cameras.new('JoyBlueHeadReviewCamera')
camera=bpy.data.objects.new('JoyBlueHeadReviewCamera',data)
scene.collection.objects.link(camera)
camera.location=target+Vector((0,-2.5,0))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
data.type='ORTHO'
data.ortho_scale=.40
scene.camera=camera
scene.cycles.device='CPU'
scene.cycles.samples=48
scene.render.resolution_x=768
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.filepath=str(OUT/'Joy-light-blue-head115.png')
scene.render.threads_mode='FIXED'
scene.render.threads=4
bpy.ops.render.render(write_still=True)
report={'source_derivative':str(OUT/'Joy_LightBlue_HairFitted.blend'),'engine':'Cycles CPU','gpu_rendering':False,
        'head':list(head),'target':list(target),'camera':list(camera.location),'ortho_scale':data.ortho_scale,
        'preview':scene.render.filepath,'sha256':hashlib.sha256(Path(scene.render.filepath).read_bytes()).hexdigest()}
(OUT/'Head115.json').write_text(json.dumps(report,indent=2)+'\n')
print('JOY_BLUE_HEAD115_FINISHED',flush=True)
