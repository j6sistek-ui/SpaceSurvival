import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Read-only wrist/ankle pose audit and opposing closeups of one saved proof.

Numerical extrema select inspection poses; they are not anatomical acceptance.
Run Blender background with -- --render only after other captures have ended.
"""
import bpy, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector

P=R.parents[2]
proof=P/'SourceAssets/DanceRefinement_20261025/Vexa_AxillaLocal_Proof.blend'
digest=hashlib.sha256(proof.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(proof),load_ui=False)
s=bpy.context.scene
rig=next(o for o in s.objects if o.type=='ARMATURE')
out=R/'VexaEndJoints'; out.mkdir(exist_ok=True)
names=['hand_l','hand_r','foot_l','foot_r']
assert all(n in rig.pose.bones for n in names)
stats={n:[] for n in names}
previous={}
for frame in range(1,962):
 s.frame_set(frame); bpy.context.view_layer.update()
 for name in names:
  bone=rig.pose.bones[name]; rest=bone.bone
  local=bone.parent.matrix.inverted()@bone.matrix
  restlocal=rest.parent.matrix_local.inverted()@rest.matrix_local
  q=(restlocal.inverted()@local).to_quaternion().normalized()
  angle=math.degrees(2*math.acos(min(1,abs(q.w))))
  step=math.degrees(previous[name].rotation_difference(q).angle) if name in previous else 0
  step=min(step,360-step)
  previous[name]=q.copy()
  stats[name].append({'seconds':(frame-1)/60,'angle_from_rest_deg':angle,'step_deg':step})
report={'proof':str(proof),'sha256':digest,'frames':961,'fps':60,'status':'DIAGNOSTIC ONLY; continuous anatomy and contact are not accepted','joints':{},'views':[]}
for name,rows in stats.items():
 report['joints'][name]={'maximum_rotation':max(rows,key=lambda x:x['angle_from_rest_deg']),'minimum_rotation':min(rows,key=lambda x:x['angle_from_rest_deg']),'maximum_frame_step':max(rows,key=lambda x:x['step_deg'])}
if '--render' in sys.argv:
 s.render.engine='BLENDER_WORKBENCH'
 s.display.shading.light='STUDIO'; s.display.shading.color_type='SINGLE'
 s.display.shading.single_color=(.55,.55,.55)
 s.display.shading.show_cavity=True; s.display.shading.background_type='WORLD'
 s.world=bpy.data.worlds.new('JointAuditWorld'); s.world.color=(.035,.045,.055)
 s.render.resolution_x=640; s.render.resolution_y=640; s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG'
 bpy.ops.object.camera_add(); cam=bpy.context.object; s.camera=cam; cam.data.type='ORTHO'
 for name,data in report['joints'].items():
  for sec in sorted({4.,round(data['maximum_rotation']['seconds'],6)}):
   f=1+sec*60; s.frame_set(int(f),subframe=f%1); bpy.context.view_layer.update()
   bone=rig.pose.bones[name]
   center=rig.matrix_world@bone.head
   orientation=(rig.matrix_world@bone.parent.matrix).to_quaternion()
   cam.data.ortho_scale=.40 if name.startswith('hand') else .50
   for view,direction in [('front',Vector((0,-2,.8))),('side',Vector((2,0,.8)))]:
    cam.location=center+orientation@direction
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    file=out/f'{name}_{sec:g}_{view}.png'
    s.render.filepath=str(file); bpy.ops.render.render(write_still=True)
    report['views'].append({'joint':name,'seconds':sec,'view':view,'path':str(file)})
assert hashlib.sha256(proof.read_bytes()).hexdigest()==digest
(out/('Rendered.json' if '--render' in sys.argv else 'Scan.json')).write_text(json.dumps(report,indent=2))
print('END_JOINTS',json.dumps(report['joints']),flush=True)
