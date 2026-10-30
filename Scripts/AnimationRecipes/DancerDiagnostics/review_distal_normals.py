import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file()
R.mkdir(parents=True,exist_ok=True)

"""Isolate shading continuity at coincident modular wrist/ankle vertices.

In-memory control only. Never saves the character or changes geometry/weights.
"""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
P=R.parents[2]
proof=P/'SourceAssets/DanceRefinement_20261025/Vexa_AxillaLocal_Proof.blend'
before=hashlib.sha256(proof.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(proof),load_ui=False)
s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE')
seams=json.loads((R/'VexaEndJoints/Seams.json').read_text())
out=R/'VexaEndJoints/NormalControl';out.mkdir(exist_ok=True)
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO'
s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.55,.55,.55)
s.display.shading.show_cavity=True;s.display.shading.background_type='WORLD'
s.world=bpy.data.worlds.new('DistalControl');s.world.color=(.035,.045,.055)
s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO'
report={'proof_sha256':before,'source_unchanged':False,'normal_mismatch_degrees':{},'views':[]}
def capture(label):
 for joint,sec in [('foot_r',11.966667),('hand_r',4)]:
  f=1+sec*60;s.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
  bone=rig.pose.bones[joint];center=rig.matrix_world@bone.head
  orientation=(rig.matrix_world@bone.parent.matrix).to_quaternion()
  cam.data.ortho_scale=.50 if joint.startswith('foot') else .40
  for view,direction in [('front',Vector((0,-2,.8))),('side',Vector((2,0,.8)))]:
   cam.location=center+orientation@direction;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
   file=out/f'{joint}_{label}_{view}.png';s.render.filepath=str(file);bpy.ops.render.render(write_still=True)
   report['views'].append(str(file))
capture('before')
for kind,entry in seams['pairs'].items():
 a=bpy.data.objects[entry['distal']];b=bpy.data.objects[entry['proximal']]
 arrays={o.name:[tuple(n.vector) for n in o.data.corner_normals] for o in (a,b)}
 maps={o.name:{} for o in (a,b)}
 for o in (a,b):
  for loop in o.data.loops:maps[o.name].setdefault(loop.vertex_index,[]).append(loop.index)
 mismatch=[]
 for i,j,_ in entry['pairs']:
  av=sum((Vector(arrays[a.name][li]) for li in maps[a.name][i]),Vector()).normalized()
  bv=sum((Vector(arrays[b.name][li]) for li in maps[b.name][j]),Vector()).normalized()
  aw=(a.matrix_world.to_3x3().inverted().transposed()@av).normalized()
  bw=(b.matrix_world.to_3x3().inverted().transposed()@bv).normalized()
  mismatch.append(math.degrees(aw.angle(bw)))
  mean=(aw+bw).normalized()
  for o,vi in ((a,i),(b,j)):
   local=(o.matrix_world.to_3x3().transposed()@mean).normalized()
   for li in maps[o.name][vi]:arrays[o.name][li]=tuple(local)
 for o in (a,b):o.data.normals_split_custom_set(arrays[o.name]);o.data.update()
 report['normal_mismatch_degrees'][kind]={'pairs':len(mismatch),'max':max(mismatch),'mean':sum(mismatch)/len(mismatch)}
capture('averaged')
report['source_unchanged']=hashlib.sha256(proof.read_bytes()).hexdigest()==before
assert report['source_unchanged']
(out/'Report.json').write_text(json.dumps(report,indent=2));print('DISTAL_NORMAL_CONTROL',json.dumps(report['normal_mismatch_degrees']),flush=True)
