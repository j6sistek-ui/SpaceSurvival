import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[2] / ".agent/local/ReplacementHero"
OUT.mkdir(parents=True, exist_ok=True)
soft='--soft-fur' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(OUT/('SquirrelHero_SoftFur.blend' if soft else 'SquirrelHero_Rigged.blend')))
rig=bpy.data.objects['Armature'];scene=bpy.context.scene
scene.render.resolution_x=480;scene.render.resolution_y=480;scene.cycles.samples=6
scene.camera.location=(-1,2,.85);scene.camera.rotation_euler=(Vector((0,0,.45))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
manifest=OUT/('fur_preview_frames.json' if soft else 'tail_preview_frames.json')
frames=json.loads(manifest.read_text()) if '--jump-only' in sys.argv and manifest.exists() else []
if '--jump-only' in sys.argv:frames=[f for f in frames if not f['clip'].startswith('Jump')]
def capture(kind,frame,index,ms):
    rig.animation_data.action=bpy.data.actions['Tail_'+kind];scene.frame_set(frame);scene.render.filepath=str(OUT/('FurPreview' if soft else 'TailPreview')/('%s-%03d.png'%(kind,index)));bpy.ops.render.render(write_still=True);frames.append({'file':scene.render.filepath,'clip':kind,'duration_ms':ms})
for kind,count,total in [('Idle',36,360),('Walk',12,30),('Run',12,18)]:
    if '--jump-only' not in sys.argv:
        for i in range(count):capture(kind,1+round(total*i/count),i,round(total/30/count*1000))
for kind,count,total in [('JumpStart',5,9),('JumpAir',10,24),('JumpLand',12,26)]:
    scene.camera.data.ortho_scale=1.52
    scene.camera.rotation_euler=(Vector((0,0,.30))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    for i in range(count):capture(kind,1+round(total*i/count),i,round(total/30/count*1000))
manifest.write_text(json.dumps(frames))
print('TAIL_PREVIEW_OK')
