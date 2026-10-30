import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""CPU Cycles comparison, bounded nape weighting trial; no source modification."""
import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaNape';O.mkdir(exist_ok=True)
import nape_weights
path=D/'Vexa_CoordinatedSymmetry_Proof.blend';before=hashlib.sha256(path.read_bytes()).hexdigest()
pairs=json.loads((R/'VexaShoulderFoundation/Report.json').read_text())['neck_pairs'];report=[]
for mode in ('baseline','weights'):
 bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False);s=bpy.context.scene;rig=next(o for o in s.objects if o.type=='ARMATURE');torso=bpy.data.objects['Vexa_Nude_Torso'];head=bpy.data.objects['Eden_Pink_CharacterMesh0.001'];row={'mode':mode,'frames':[]}
 if mode=='weights':row['repair']=nape_weights.apply(torso,head,pairs)
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=False;s.render.threads_mode='FIXED';s.render.threads=4
 s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 s.world=bpy.data.worlds.new('NapeCPU');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.16,.2,.25,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
 mat=bpy.data.materials.new('NapeCPUClay');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.45,.47,.50,1);bs.inputs['Roughness'].default_value=.8
 for ob in s.objects:
  if ob.type=='MESH':ob.data.materials.clear();ob.data.materials.append(mat)
 bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.64
 lights=[]
 for energy,size in ((90,1.3),(40,1.8)):
  bpy.ops.object.light_add(type='AREA');li=bpy.context.object;li.data.energy=energy;li.data.shape='DISK';li.data.size=size;lights.append(li)
 for frame in (241,543,733):
  s.frame_set(frame);bpy.context.view_layer.update();center=(rig.matrix_world@rig.pose.bones['neck_01'].matrix).translation-Vector((0,0,.08));chest=(rig.matrix_world@rig.pose.bones['spine_05'].matrix).to_quaternion()@(rig.matrix_world@rig.data.bones['spine_05'].matrix_local).to_quaternion().inverted()
  dg=bpy.context.evaluated_depsgraph_get();a=torso.evaluated_get(dg);b=head.evaluated_get(dg);gaps=[((a.matrix_world@a.data.vertices[i].co)-(b.matrix_world@b.data.vertices[j].co)).length for i,j,*_ in pairs]
  row['frames'].append({'frame':frame,'max_neck_seam_gap_m':max(gaps)});assert max(gaps)<1e-5,max(gaps)
  for view,offset in [('back',Vector((0,3,.12))),('front',Vector((0,-3,.12)))]:
   if frame!=543 and view=='front':continue
   cam.location=center+chest@offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
   for li,off in zip(lights,(Vector((-1,1.5,1.7)),Vector((1,-1,1)))):
    li.location=center+chest@off;li.rotation_euler=(center-li.location).to_track_quat('-Z','Y').to_euler()
   s.render.filepath=str(O/f'{mode}_{frame}_{view}.png');bpy.ops.render.render(write_still=True)
 if mode=='weights':
  for ob in list(s.objects):
   if ob.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(ob,do_unlink=True)
  bpy.context.preferences.filepaths.save_version=0;candidate=D/'Vexa_NapeWeights_Trial.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate),compress=True);row['candidate']=str(candidate);row['sha256']=hashlib.sha256(candidate.read_bytes()).hexdigest()
 report.append(row)
assert hashlib.sha256(path.read_bytes()).hexdigest()==before
(O/'Review.json').write_text(json.dumps({'source_sha256':before,'source_unchanged':True,'rows':report},indent=2));print('NAPE_CPU_REVIEW_DONE',flush=True)
