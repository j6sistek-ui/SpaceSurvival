"""CPU-only saved v4_4 rear service monitor previews; no blend saves."""
import json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/Cryo_Comparison'
manifest=json.loads((OUT/'assembly_fit_v4_4.json').read_text())
model=next(m for m in manifest['models'] if m['id']=='D')
bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False)
scene=bpy.context.scene;scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_percentage=100
target=OUT/'previews/RearConsole_v4_4';target.mkdir(exist_ok=False)
camera=scene.camera;camera.data.type='ORTHO'
views=[('D_back',(0,6,1.6),(0,0,1.6),3.85,640,800),
       ('D_rear_console_left',(-2.4,4.8,1.6),(0,1.03,.30),1.05,800,600),
       ('D_rear_console_right',(2.4,4.8,1.6),(0,1.03,.30),1.05,800,600)]
for name,position,aim,scale,width,height in views:
    camera.location=position;camera.rotation_euler=(Vector(aim)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale=scale;scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.filepath=str(target/(name+'.png'));bpy.ops.render.render(write_still=True)
    print('REAR_CONSOLE_PREVIEW',scene.render.filepath,flush=True)
