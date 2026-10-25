import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/Cryo_Comparison'
manifest=json.loads((OUT/'assembly_fit_v4_2.json').read_text())
target=OUT/'previews/FitAfter_v4_2'
target.mkdir(exist_ok=True)
angles={'front':(0,-6,1.6),'front_left':(-4.2,-5.2,2.2),'left':(-6,0,1.6),'back_left':(-4.2,5.2,2.2),'back':(0,6,1.6),'back_right':(4.2,5.2,2.2),'right':(6,0,1.6),'front_right':(4.2,-5.2,2.2),'top':(0,0,8)}
for model in manifest['models']:
    bpy.ops.wm.open_mainfile(filepath=model['editable_blend'],load_ui=False)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=3.85
    for view,location in angles.items():
        cam.location=location;cam.rotation_euler=(Vector((0,0,1.6))-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(target/(model['id']+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
    print('FIT_AFTER_DONE',model['id'],flush=True)
