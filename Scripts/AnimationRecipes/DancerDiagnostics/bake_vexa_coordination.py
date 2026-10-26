import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
R=Path(os.environ.get('SS_ANIMATION_PROJECT',str(Path.home()/'SpaceSurvival'))).resolve()/'.agent/local/AnimationReview_20261025'
assert (R.parents[2]/'SpaceSurvival.uproject').is_file(), 'Set SS_ANIMATION_PROJECT to the canonical project'
R.mkdir(parents=True,exist_ok=True)

"""Save one compact private proof; no original or Unreal asset is overwritten."""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Matrix
P=R.parents[2];D=P/'SourceAssets/DanceRefinement_20261025';O=R/'VexaCoordinatedSymmetry';O.mkdir(exist_ok=True)
from coordinated_girdle import coordinate
from mirror_vexa_shoulder_weights import apply
source=P/'SourceAssets/CharacterWorkshop_20261021/Vexa_Character_Options.blend';proof=D/'Vexa_LegPlane_Proof.blend'
source_hashes={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (source,proof)}
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False);s=bpy.context.scene;old=next(o for o in s.objects if o.type=='ARMATURE');old.animation_data_clear()
for pb in old.pose.bones:pb.matrix_basis=Matrix.Identity(4)
replacement=('Vexa_Nude_Torso','Vexa_Nude_Legs','Vexa_Bottom')
for name in replacement:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
with bpy.data.libraries.load(str(proof),link=False) as (a,b):b.objects=[n for n in a.objects if n in replacement or n==old.name]
for ob in b.objects:s.collection.objects.link(ob)
bpy.context.view_layer.update();rig=next(o for o in b.objects if o.type=='ARMATURE')
for ob in list(s.objects):
 if ob.type!='MESH':continue
 if ob.parent==old:
  world=ob.matrix_world.copy();ob.parent=rig;ob.matrix_world=world
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
bpy.data.objects.remove(old,do_unlink=True);bpy.context.view_layer.update()
ordered=sorted(rig.pose.bones,key=lambda b:len(b.parent_recursive));rest={b.name:(rig.matrix_world@b.bone.matrix_local).copy() for b in ordered};parent={b.name:b.parent.name if b.parent else None for b in ordered};desc={b.name:[b.name]+[c.name for c in b.children_recursive] for b in ordered};inv=rig.matrix_world.inverted()
end=round(rig.animation_data.action.frame_range[1]);buffers={b.name:{'q':[[],[],[],[]],'p':[[],[],[]]} for b in ordered};previous={};step=0.;changes=[]
for f in range(1,end+1):
 s.frame_set(f);pose={b.name:(rig.matrix_world@b.matrix).copy() for b in ordered};changes.append(coordinate(pose,rest,parent,desc,True));local={n:inv@m for n,m in pose.items()}
 for pb in ordered:
  base=local[pb.parent.name]@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local if pb.parent else pb.bone.matrix_local
  basis=base.inverted()@local[pb.name];q=basis.to_quaternion().normalized()
  if pb.name in previous:
   if q.dot(previous[pb.name])<0:q.negate()
   if pb.name.startswith(('clavicle_','neck_','upperarm_')):step=max(step,math.degrees(q.rotation_difference(previous[pb.name]).angle))
  previous[pb.name]=q.copy()
  for k in range(4):buffers[pb.name]['q'][k].extend((f,q[k]))
  for k in range(3):buffers[pb.name]['p'][k].extend((f,basis.translation[k]))
assert step<5,step
act=bpy.data.actions.new('A_F3_Vexa_CoordinatedSymmetry_Spiral');rig.animation_data.action=act
for pb in ordered:
 pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=1,group=pb.name);pb.keyframe_insert('location',frame=1,group=pb.name)
for layer in act.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    n=fc.data_path.split('"')[1];kind='q' if fc.data_path.endswith('rotation_quaternion') else 'p';fc.keyframe_points.clear();fc.keyframe_points.add(end);fc.keyframe_points.foreach_set('co',buffers[n][kind][fc.array_index])
    for key in fc.keyframe_points:key.interpolation='LINEAR'
    fc.update()
weights=apply(bpy.data.objects['Vexa_Nude_Torso'])
# Keep a small geometry/motion review, with no second packed texture library.
keep={'Vexa_Nude_Torso','Vexa_Nude_Legs','Vexa_Top','Vexa_Bottom','Eden_Pink_CharacterMesh0.001','Eden_Pink_Hands.001','Eden_Pink_Feet.001','Eden_Pink_Hair.001'}
clay=bpy.data.materials.new('PRIVATE_ReviewClay');clay.diffuse_color=(.6,.6,.6,1)
for ob in list(s.objects):
 if ob!=rig and (ob.type!='MESH' or ob.name not in keep):bpy.data.objects.remove(ob,do_unlink=True);continue
 if ob.type=='MESH':
  ob.data.materials.clear();ob.data.materials.append(clay)
  for p in ob.data.polygons:p.material_index=0
  if 'Hair' in ob.name:ob.hide_render=True
used={act}|{o.data.shape_keys.animation_data.action for o in s.objects if o.type=='MESH' and o.data.shape_keys and o.data.shape_keys.animation_data}
for a in list(bpy.data.actions):
 if a not in used:bpy.data.actions.remove(a)
for m in list(bpy.data.materials):
 if m!=clay:bpy.data.materials.remove(m)
for im in list(bpy.data.images):bpy.data.images.remove(im)
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=False,do_recursive=True)
s.render.fps=60;s.frame_start=1;s.frame_end=end;s.frame_set(543);bpy.context.preferences.filepaths.save_version=0
rig['Proof_Status']='PRIVATE: coordinated clavicle/neck and left shoulder weight trial. Not adopted; neck/shoulder/motion remain open.'
path=D/'Vexa_CoordinatedSymmetry_Proof.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in source_hashes.items())
report={'status':rig['Proof_Status'],'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_hashes':source_hashes,'frames':end,'max_clavicle_neck_upperarm_step_deg':step,'max_arm_root_shift_m':max(r[side]['arm_root_shift_m'] for r in changes for side in ('l','r')),'max_head_translation_m':max(r['neck']['head_translation_m'] for r in changes),'weights':weights,'bones':len(rig.data.bones),'source_unchanged':True}
(O/'BakeReport.json').write_text(json.dumps(report,indent=2));print('COORDINATED_PROOF_SAVED',json.dumps({k:v for k,v in report.items() if k not in ('weights','source_hashes')}),flush=True)
